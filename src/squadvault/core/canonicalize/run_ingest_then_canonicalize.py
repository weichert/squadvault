from __future__ import annotations

from collections import Counter
import argparse
from pathlib import Path
import os
import sqlite3

from dotenv import load_dotenv

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.mfl.client import MflClient

from squadvault.ingest.auction_draft import derive_auction_event_envelopes_from_transactions
from squadvault.ingest.transactions import derive_transaction_event_envelopes
from squadvault.ingest.waiver_bids import derive_waiver_bid_event_envelopes_from_transactions

from squadvault.core.canonicalize.run_canonicalize import canonicalize


# Load env early so argparse defaults can safely reference env vars.
load_dotenv(".env")

SCHEMA = Path("src/squadvault/core/storage/schema.sql").read_text()

RAW_JSON_TRUNCATE_CHARS = int(os.environ.get("RAW_JSON_TRUNCATE_CHARS", "2000"))


def run_sql_checks(conn: sqlite3.Connection, league_id: str, season: int) -> None:
    print("\n=== Sanity checks ===")

    stub_awards = conn.execute(
        """
        SELECT COUNT(*) AS stub_awards
        FROM memory_events
        WHERE league_id=? AND season=? AND event_type='WAIVER_BID_AWARDED'
          AND (json_extract(payload_json,'$.player_id') IS NULL OR json_extract(payload_json,'$.player_id')='')
          AND (json_extract(payload_json,'$.bid_amount') IS NULL OR json_extract(payload_json,'$.bid_amount')='')
          AND (json_extract(payload_json,'$.players_added_ids') IS NULL OR json_extract(payload_json,'$.players_added_ids')='');
        """,
        (league_id, season),
    ).fetchone()[0]

    best_with_blank_player = conn.execute(
        """
        SELECT COUNT(*) AS best_with_blank_player
        FROM canonical_events ce
        JOIN memory_events me ON me.id = ce.best_memory_event_id
        WHERE ce.league_id=? AND ce.season=? AND ce.event_type='WAIVER_BID_AWARDED'
          AND (json_extract(me.payload_json,'$.player_id') IS NULL OR json_extract(me.payload_json,'$.player_id')='');
        """,
        (league_id, season),
    ).fetchone()[0]

    ledger_free_agent = conn.execute(
        """
        SELECT COUNT(*)
        FROM memory_events
        WHERE league_id=? AND season=? AND event_type='TRANSACTION_FREE_AGENT'
        """,
        (league_id, season),
    ).fetchone()[0]

    canonical_free_agent = conn.execute(
        """
        SELECT COUNT(*)
        FROM canonical_events
        WHERE league_id=? AND season=? AND event_type='TRANSACTION_FREE_AGENT'
        """,
        (league_id, season),
    ).fetchone()[0]

    ratio = (float(canonical_free_agent) / float(ledger_free_agent)) if ledger_free_agent else 0.0

    print("stub_awards_in_ledger =", int(stub_awards), "(should not increase)")
    print("best_with_blank_player =", int(best_with_blank_player), "(must be 0)")
    print("free_agent_ledger =", int(ledger_free_agent))
    print("free_agent_canonical =", int(canonical_free_agent))
    print("free_agent_collapse_ratio =", f"{ratio:.3f}")

    totals = conn.execute(
        """
        SELECT event_type, COUNT(*) AS n
        FROM canonical_events
        WHERE league_id=? AND season=?
        GROUP BY event_type
        ORDER BY n DESC
        """,
        (league_id, season),
    ).fetchall()

    print("canonical_by_type =", {et: int(n) for (et, n) in totals})


def _env_required(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"Missing required environment variable: {name}")
    return v


def parse_args() -> argparse.Namespace:
    """
    Daily driver: ingest -> canonicalize -> checks

    Important: this script must NOT run at import-time, and -h must show help and exit.
    """
    p = argparse.ArgumentParser(description="SquadVault daily driver: ingest -> canonicalize -> checks")

    p.add_argument(
        "--db",
        default=os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"),
        help="Path to SQLite DB (default: env SQUADVAULT_DB or .local_squadvault.sqlite)",
    )
    p.add_argument(
        "--league-id",
        default=os.environ.get("MFL_LEAGUE_ID"),
        help="MFL league id (default: env MFL_LEAGUE_ID)",
    )
    p.add_argument(
        "--season",
        "--year",
        dest="season",
        type=int,
        default=int(os.environ.get("SQUADVAULT_YEAR", "2024")),
        help="Season/year (default: env SQUADVAULT_YEAR or 2024)",
    )
    p.add_argument(
        "--mfl-server",
        default=os.environ.get("MFL_SERVER"),
        help="MFL server hostname (default: env MFL_SERVER)",
    )
    p.add_argument(
        "--raw-json-truncate-chars",
        type=int,
        default=int(os.environ.get("RAW_JSON_TRUNCATE_CHARS", str(RAW_JSON_TRUNCATE_CHARS))),
        help="Max chars to store for raw_json (default: env RAW_JSON_TRUNCATE_CHARS or 2000)",
    )

    # Optional auth; required only if your client needs it.
    p.add_argument("--mfl-username", default=os.environ.get("MFL_USERNAME"), help="MFL username (optional)")
    p.add_argument("--mfl-password", default=os.environ.get("MFL_PASSWORD"), help="MFL password (optional)")

    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Resolve required values: either CLI arg or env var.
    league_id = args.league_id or _env_required("MFL_LEAGUE_ID")
    mfl_server = args.mfl_server or _env_required("MFL_SERVER")

    db_path = Path(args.db)
    season = int(args.season)
    raw_json_truncate_chars = int(args.raw_json_truncate_chars)

    print("\n=== SquadVault Daily Driver: ingest -> canonicalize -> checks ===")
    print("DB_PATH =", db_path.resolve())
    print("YEAR =", season)
    print("LEAGUE_ID =", league_id)
    print("MFL_SERVER =", mfl_server)

    store = SQLiteStore(db_path)

    # Only initialize schema for a brand-new DB file.
    if (not db_path.exists()) or db_path.stat().st_size == 0:
        store.init_db(SCHEMA)

    client = MflClient(
        server=mfl_server,
        league_id=league_id,
        username=args.mfl_username,
        password=args.mfl_password,
    )

    raw_json, source_url = client.get_transactions(year=season)

    transactions = raw_json.get("transactions", {}).get("transaction", [])
    if isinstance(transactions, dict):
        transactions = [transactions]

    events: list[dict] = []
    events += derive_auction_event_envelopes_from_transactions(
        year=season,
        league_id=league_id,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )
    events += derive_transaction_event_envelopes(
        year=season,
        league_id=league_id,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )
    events += derive_waiver_bid_event_envelopes_from_transactions(
        year=season,
        league_id=league_id,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )

    inserted, skipped = store.append_events(events)
    counts = Counter([e["event_type"] for e in events])

    print("\n=== Ingest results ===")
    print("events_prepared =", len(events))
    print("inserted =", inserted, "skipped =", skipped)
    print("by_event_type =", dict(counts))
    print("ingest_status =", "no_new_rows" if inserted == 0 else "appended_rows")

    print("\n=== Canonicalize ===")
    # NOTE: canonicalize() uses the default DB in its implementation. If it supports a db_path,
    # pass it through. If not, we rely on canonicalize reading the same DB from env/config.
    try:
        canonicalize(league_id=league_id, season=season, db_path=str(db_path))  # type: ignore[arg-type]
    except TypeError:
        # Backward compatible call signature
        canonicalize(league_id=league_id, season=season)

    print("\n=== Post-run checks (SQLite) ===")
    conn = sqlite3.connect(str(db_path))
    try:
        run_sql_checks(conn, league_id=league_id, season=season)
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
