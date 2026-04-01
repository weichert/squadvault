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

from __future__ import annotations

import os
from pathlib import Path

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.matchup_results import derive_matchup_result_envelopes
from squadvault.mfl.client import MflClient


def main() -> None:
    """Ingest matchup results for all weeks."""
    from dotenv import load_dotenv

    load_dotenv(".env")

    schema = Path("src/squadvault/core/storage/schema.sql").read_text()
    db_path = Path(os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"))
    year = int(os.environ.get("SQUADVAULT_YEAR", "2024"))
    league_id = os.environ["MFL_LEAGUE_ID"]
    mfl_server = os.environ["MFL_SERVER"]
    mfl_username = os.environ.get("MFL_USERNAME")
    mfl_password = os.environ.get("MFL_PASSWORD")
    max_weeks = int(os.environ.get("MFL_MAX_WEEKS", "18"))

    print("\n=== SquadVault Matchup Results Ingest ===")
    print(f"DB_PATH = {db_path.resolve()}")
    print(f"YEAR = {year}")
    print(f"LEAGUE_ID = {league_id}")
    print(f"MFL_SERVER = {mfl_server}")
    print(f"MAX_WEEKS = {max_weeks}")

    store = SQLiteStore(db_path)
    store.init_db(schema)

    client = MflClient(
        server=mfl_server,
        league_id=league_id,
        username=mfl_username,
        password=mfl_password,
    )

    # Look up lock timestamps to derive occurred_at for matchup events.
    # Matchup results get occurred_at = window_start (the lock that opens each week).
    week_occurred_at: dict[int, str | None] = {}
    try:
        from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index
        for w in range(1, max_weeks + 1):
            win = window_for_week_index(str(db_path), league_id, year, w)
            if win.mode != "UNSAFE" and win.window_start:
                week_occurred_at[w] = win.window_start
    except Exception as e:
        print(f"  WARNING: Could not load lock timestamps — occurred_at will be None: {e}")

    if week_occurred_at:
        print(f"  Lock timestamps resolved for {len(week_occurred_at)}/{max_weeks} weeks")
    else:
        print("  WARNING: No lock timestamps found — all matchup events will have NULL occurred_at.")
        print("  Ensure transaction ingestion + canonicalization runs BEFORE matchup results.")

    total_inserted = 0
    total_skipped = 0
    total_events = 0

    for week in range(1, max_weeks + 1):
        try:
            raw_json, source_url = client.get_weekly_results(year=year, week=week)
        except Exception as e:
            print(f"  Week {week:2d}: FETCH ERROR — {e}")
            continue

        events = derive_matchup_result_envelopes(
            year=year,
            week=week,
            league_id=league_id,
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

    print("\n=== Summary ===")
    print(f"events_prepared = {total_events}")
    print(f"inserted = {total_inserted}")
    print(f"skipped = {total_skipped}")

    # Show current matchup event counts
    from squadvault.core.storage.session import DatabaseSession
    with DatabaseSession(str(db_path)) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE event_type = 'WEEKLY_MATCHUP_RESULT' AND league_id = ? AND season = ?",
            (league_id, year),
        ).fetchone()
        print(f"total WEEKLY_MATCHUP_RESULT in memory_events = {row[0]}")


if __name__ == "__main__":
    main()
