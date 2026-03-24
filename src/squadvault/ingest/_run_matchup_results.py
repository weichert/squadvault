"""CLI runner for matchup results ingestion from MFL weeklyResults API.

Usage:
  PYTHONPATH=src python src/squadvault/ingest/_run_matchup_results.py

Env vars:
  MFL_LEAGUE_ID  — required (e.g. 70985)
  MFL_SERVER     — required (e.g. 44)
  SQUADVAULT_YEAR — optional (default: 2024)
  MFL_USERNAME   — optional (for private leagues)
  MFL_PASSWORD   — optional (for private leagues)
  SQUADVAULT_DB  — optional (default: .local_squadvault.sqlite)
"""

from dotenv import load_dotenv
load_dotenv(".env")

from collections import Counter
from pathlib import Path
import os

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.mfl.client import MflClient
from squadvault.ingest.matchup_results import derive_matchup_result_envelopes

SCHEMA = Path("src/squadvault/core/storage/schema.sql").read_text()
DB_PATH = Path(os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"))

YEAR = int(os.environ.get("SQUADVAULT_YEAR", "2024"))
LEAGUE_ID = os.environ["MFL_LEAGUE_ID"]
MFL_SERVER = os.environ["MFL_SERVER"]
MFL_USERNAME = os.environ.get("MFL_USERNAME")
MFL_PASSWORD = os.environ.get("MFL_PASSWORD")

# Number of regular season + playoff weeks to ingest
MAX_WEEKS = int(os.environ.get("MFL_MAX_WEEKS", "18"))


def main() -> None:
    """Ingest matchup results for all weeks."""
    print("\n=== SquadVault Matchup Results Ingest ===")
    print(f"DB_PATH = {DB_PATH.resolve()}")
    print(f"YEAR = {YEAR}")
    print(f"LEAGUE_ID = {LEAGUE_ID}")
    print(f"MFL_SERVER = {MFL_SERVER}")
    print(f"MAX_WEEKS = {MAX_WEEKS}")

    store = SQLiteStore(DB_PATH)
    store.init_db(SCHEMA)

    client = MflClient(
        server=MFL_SERVER,
        league_id=LEAGUE_ID,
        username=MFL_USERNAME,
        password=MFL_PASSWORD,
    )

    # Look up lock timestamps to derive occurred_at for matchup events.
    # Matchup results get occurred_at = window_start (the lock that opens each week).
    week_occurred_at: dict[int, str | None] = {}
    try:
        from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index
        for w in range(1, MAX_WEEKS + 1):
            win = window_for_week_index(str(DB_PATH), LEAGUE_ID, YEAR, w)
            if win.mode == "LOCK_TO_LOCK" and win.window_start:
                week_occurred_at[w] = win.window_start
    except Exception as e:
        print(f"  WARNING: Could not load lock timestamps — occurred_at will be None: {e}")

    total_inserted = 0
    total_skipped = 0
    total_events = 0

    for week in range(1, MAX_WEEKS + 1):
        try:
            raw_json, source_url = client.get_weekly_results(year=YEAR, week=week)
        except Exception as e:
            print(f"  Week {week:2d}: FETCH ERROR — {e}")
            continue

        events = derive_matchup_result_envelopes(
            year=YEAR,
            week=week,
            league_id=LEAGUE_ID,
            weekly_results_json=raw_json,
            source_url=source_url,
            occurred_at=week_occurred_at.get(week),
        )

        if not events:
            print(f"  Week {week:2d}: no matchups found")
            continue

        inserted, skipped = store.append_events(events)
        total_inserted += inserted
        total_skipped += skipped
        total_events += len(events)

        print(f"  Week {week:2d}: {len(events)} matchups → {inserted} inserted, {skipped} skipped")

    print(f"\n=== Summary ===")
    print(f"events_prepared = {total_events}")
    print(f"inserted = {total_inserted}")
    print(f"skipped = {total_skipped}")

    # Show current matchup event counts
    from squadvault.core.storage.session import DatabaseSession
    with DatabaseSession(str(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE event_type = 'WEEKLY_MATCHUP_RESULT' AND league_id = ? AND season = ?",
            (LEAGUE_ID, YEAR),
        ).fetchone()
        print(f"total WEEKLY_MATCHUP_RESULT in memory_events = {row[0]}")


if __name__ == "__main__":
    main()
