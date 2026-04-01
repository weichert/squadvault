"""CLI runner for raw event ingestion to SQLite store."""

from __future__ import annotations

import logging
import os
from collections import Counter
from pathlib import Path

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.auction_draft import derive_auction_event_envelopes_from_transactions
from squadvault.ingest.transactions import derive_transaction_event_envelopes
from squadvault.ingest.waiver_bids import derive_waiver_bid_event_envelopes_from_transactions
from squadvault.mfl.client import MflClient

logger = logging.getLogger(__name__)


def _sqlite_list_tables(db_path: Path) -> list[str]:
    """List all user tables in a SQLite database."""
    if not db_path.exists():
        return []
    with DatabaseSession(str(db_path)) as conn:

        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]


def _sqlite_table_counts(db_path: Path, tables: list[str]) -> dict[str, int]:
    """Return row counts for all tables."""
    if not db_path.exists():
        return {}
    with DatabaseSession(str(db_path)) as conn:

        out: dict[str, int] = {}
        for t in tables:
            # defensive: skip SQLite internal tables if any
            if t.startswith("sqlite_"):
                continue
            try:
                out[t] = int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            except Exception as exc:
                logger.debug("%s", exc)
                # some tables/views might not be countable in the same way
                out[t] = -1
        return out


def main() -> None:
    """CLI entrypoint: ingest events to SQLite store."""
    from dotenv import load_dotenv

    load_dotenv(".env")

    schema = Path("src/squadvault/core/storage/schema.sql").read_text()
    db_path = Path(os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"))
    year = int(os.environ.get("SQUADVAULT_YEAR", "2024"))
    league_id = os.environ["MFL_LEAGUE_ID"]  # required
    mfl_server = os.environ["MFL_SERVER"]  # required
    mfl_username = os.environ.get("MFL_USERNAME")
    mfl_password = os.environ.get("MFL_PASSWORD")
    raw_json_truncate_chars = int(os.environ.get("RAW_JSON_TRUNCATE_CHARS", "2000"))

    print("\n=== SquadVault Ingest Runner ===")
    print("DB_PATH (relative) =", db_path)
    print("DB_PATH (absolute) =", db_path.resolve())
    print("YEAR =", year)
    print("LEAGUE_ID =", league_id)
    print("MFL_SERVER =", mfl_server)

    store = SQLiteStore(db_path)
    store.init_db(schema)

    # Show what tables exist after init_db() so you can see the ledger table name.
    tables = _sqlite_list_tables(db_path)
    print("\n=== SQLite tables ===")
    if not tables:
        print("(no tables found — DB file may not exist yet)")
    else:
        for t in tables:
            print("-", t)

        counts = _sqlite_table_counts(db_path, tables)
        print("\n=== Table row counts (pre-ingest) ===")
        for t in sorted(counts.keys()):
            print(f"{t}: {counts[t]}")

    client = MflClient(
        server=mfl_server,
        league_id=league_id,
        username=mfl_username,
        password=mfl_password,
    )

    raw_json, source_url = client.get_transactions(year=year)

    transactions = raw_json.get("transactions", {}).get("transaction", [])
    if isinstance(transactions, dict):
        transactions = [transactions]

    events = []
    events += derive_auction_event_envelopes_from_transactions(
        year=year,
        league_id=league_id,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )
    events += derive_transaction_event_envelopes(
        year=year,
        league_id=league_id,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )
    events += derive_waiver_bid_event_envelopes_from_transactions(
        year=year,
        league_id=league_id,
        transactions=transactions,
        source_url=source_url,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )

    inserted, skipped = store.append_events(events)
    by_type = Counter([e["event_type"] for e in events])

    print("\n=== Ingest results ===")
    print("events_prepared =", len(events))
    print("inserted =", inserted, "skipped =", skipped)
    print("by_event_type =", dict(by_type))

    # Post-ingest: show which table(s) grew. One of these is your "ledger".
    tables_after = _sqlite_list_tables(db_path)
    counts_after = _sqlite_table_counts(db_path, tables_after)

    print("\n=== Table row counts (post-ingest) ===")
    for t in sorted(counts_after.keys()):
        print(f"{t}: {counts_after[t]}")

    # Your existing "ledger_total" check remains (whatever store.fetch_events reads from).
    fetched = store.fetch_events(league_id=league_id, season=year, limit=1000, use_canonical=False)
    print("\nledger_total (via store.fetch_events, limit=1000) =", len(fetched))

    # Helpful hint: likely ledger candidates (based on table names)
    if tables_after:
        candidates = [t for t in tables_after if "ledger" in t.lower() or "event" in t.lower()]
        if candidates:
            print("\nLikely ledger table candidates:", candidates)
        else:
            print("\nNo obvious ledger table name detected; check the tables list above.")


if __name__ == "__main__":
    main()
