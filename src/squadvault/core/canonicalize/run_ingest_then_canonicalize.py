from __future__ import annotations

from dotenv import load_dotenv

load_dotenv(".env")

from collections import Counter
from pathlib import Path
import os
import sqlite3

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.mfl.client import MflClient

from squadvault.ingest.auction_draft import derive_auction_event_envelopes_from_transactions
from squadvault.ingest.transactions import derive_transaction_event_envelopes
from squadvault.ingest.waiver_bids import derive_waiver_bid_event_envelopes_from_transactions

from squadvault.core.canonicalize.run_canonicalize import canonicalize


SCHEMA = Path("src/squadvault/core/storage/schema.sql").read_text()
DB_PATH = Path(".local_squadvault.sqlite")

YEAR = int(os.environ.get("SQUADVAULT_YEAR", "2024"))

LEAGUE_ID = os.environ["MFL_LEAGUE_ID"]  # required
MFL_SERVER = os.environ["MFL_SERVER"]  # required

MFL_USERNAME = os.environ.get("MFL_USERNAME")
MFL_PASSWORD = os.environ.get("MFL_PASSWORD")

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

def main() -> None:
    print("\n=== SquadVault Daily Driver: ingest -> canonicalize -> checks ===")
    print("DB_PATH =", DB_PATH.resolve())
    print("YEAR =", YEAR)
    print("LEAGUE_ID =", LEAGUE_ID)
    print("MFL_SERVER =", MFL_SERVER)

    store = SQLiteStore(DB_PATH)

    # Only initialize schema for a brand-new DB file.
    if (not DB_PATH.exists()) or DB_PATH.stat().st_size == 0:
        store.init_db(SCHEMA)

    client = MflClient(
        server=MFL_SERVER,
        league_id=LEAGUE_ID,
        username=MFL_USERNAME,
        password=MFL_PASSWORD,
    )

    raw_json, source_url = client.get_transactions(year=YEAR)

    transactions = raw_json.get("transactions", {}).get("transaction", [])
    if isinstance(transactions, dict):
        transactions = [transactions]

    events = []
    events += derive_auction_event_envelopes_from_transactions(
        year=YEAR,
        league_id=LEAGUE_ID,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=RAW_JSON_TRUNCATE_CHARS,
    )
    events += derive_transaction_event_envelopes(
        year=YEAR,
        league_id=LEAGUE_ID,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=RAW_JSON_TRUNCATE_CHARS,
    )
    events += derive_waiver_bid_event_envelopes_from_transactions(
        year=YEAR,
        league_id=LEAGUE_ID,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=RAW_JSON_TRUNCATE_CHARS,
    )

    inserted, skipped = store.append_events(events)
    counts = Counter([e["event_type"] for e in events])

    print("\n=== Ingest results ===")
    print("events_prepared =", len(events))
    print("inserted =", inserted, "skipped =", skipped)
    print("by_event_type =", dict(counts))
    print("ingest_status =", "no_new_rows" if inserted == 0 else "appended_rows")

    print("\n=== Canonicalize ===")
    canonicalize(league_id=LEAGUE_ID, season=YEAR)

    print("\n=== Post-run checks (SQLite) ===")
    conn = sqlite3.connect(str(DB_PATH))
    try:
        run_sql_checks(conn, league_id=LEAGUE_ID, season=YEAR)
    finally:
        conn.close()

if __name__ == "__main__":
    main()