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


SCHEMA = Path("src/squadvault/core/storage/schema.sql").read_text()
DB_PATH = Path(".local_squadvault.sqlite")

YEAR = int(os.environ.get("SQUADVAULT_YEAR", "2024"))

LEAGUE_ID = os.environ["MFL_LEAGUE_ID"]  # required
MFL_SERVER = os.environ["MFL_SERVER"]  # required

MFL_USERNAME = os.environ.get("MFL_USERNAME")
MFL_PASSWORD = os.environ.get("MFL_PASSWORD")

RAW_JSON_TRUNCATE_CHARS = int(os.environ.get("RAW_JSON_TRUNCATE_CHARS", "2000"))


def _sqlite_list_tables(db_path: Path) -> list[str]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def _sqlite_table_counts(db_path: Path, tables: list[str]) -> dict[str, int]:
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(str(db_path))
    try:
        out: dict[str, int] = {}
        for t in tables:
            # defensive: skip SQLite internal tables if any
            if t.startswith("sqlite_"):
                continue
            try:
                out[t] = int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            except Exception:
                # some tables/views might not be countable in the same way
                out[t] = -1
        return out
    finally:
        conn.close()


def main() -> None:
    print("\n=== SquadVault Ingest Runner ===")
    print("DB_PATH (relative) =", DB_PATH)
    print("DB_PATH (absolute) =", DB_PATH.resolve())
    print("YEAR =", YEAR)
    print("LEAGUE_ID =", LEAGUE_ID)
    print("MFL_SERVER =", MFL_SERVER)

    store = SQLiteStore(DB_PATH)
    store.init_db(SCHEMA)

    # Show what tables exist after init_db() so you can see the ledger table name.
    tables = _sqlite_list_tables(DB_PATH)
    print("\n=== SQLite tables ===")
    if not tables:
        print("(no tables found — DB file may not exist yet)")
    else:
        for t in tables:
            print("-", t)

        counts = _sqlite_table_counts(DB_PATH, tables)
        print("\n=== Table row counts (pre-ingest) ===")
        for t in sorted(counts.keys()):
            print(f"{t}: {counts[t]}")

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
    by_type = Counter([e["event_type"] for e in events])

    print("\n=== Ingest results ===")
    print("events_prepared =", len(events))
    print("inserted =", inserted, "skipped =", skipped)
    print("by_event_type =", dict(by_type))

    # Post-ingest: show which table(s) grew. One of these is your "ledger".
    tables_after = _sqlite_list_tables(DB_PATH)
    counts_after = _sqlite_table_counts(DB_PATH, tables_after)

    print("\n=== Table row counts (post-ingest) ===")
    for t in sorted(counts_after.keys()):
        print(f"{t}: {counts_after[t]}")

    # Your existing “ledger_total” check remains (whatever store.fetch_events reads from).
    fetched = store.fetch_events(league_id=LEAGUE_ID, season=YEAR, limit=1000)
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
