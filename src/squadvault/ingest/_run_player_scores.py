"""CLI runner for player scores ingestion from MFL weeklyResults API.

Uses the same weeklyResults endpoint as matchup results but extracts
per-player scoring and lineup status.

Usage:
  PYTHONPATH=src python src/squadvault/ingest/_run_player_scores.py

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

from pathlib import Path
import os

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.mfl.client import MflClient
from squadvault.ingest.player_scores import derive_player_score_envelopes

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
    """Ingest player scores for all weeks."""
    print("\n=== SquadVault Player Scores Ingest ===")
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

    total_inserted = 0
    total_skipped = 0
    total_events = 0

    for week in range(1, MAX_WEEKS + 1):
        try:
            raw_json, source_url = client.get_weekly_results(year=YEAR, week=week)
        except Exception as e:
            print(f"  Week {week:2d}: FETCH ERROR — {e}")
            continue

        events = derive_player_score_envelopes(
            year=YEAR,
            week=week,
            league_id=LEAGUE_ID,
            weekly_results_json=raw_json,
            source_url=source_url,
        )

        if not events:
            print(f"  Week {week:2d}: no player scores found")
            continue

        inserted, skipped = store.append_events(events)
        total_inserted += inserted
        total_skipped += skipped
        total_events += len(events)

        print(f"  Week {week:2d}: {len(events)} player scores → {inserted} inserted, {skipped} skipped")

    print("\n=== Summary ===")
    print(f"events_prepared = {total_events}")
    print(f"inserted = {total_inserted}")
    print(f"skipped = {total_skipped}")

    # Show current player score event counts
    from squadvault.core.storage.session import DatabaseSession
    with DatabaseSession(str(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE event_type = 'WEEKLY_PLAYER_SCORE' AND league_id = ? AND season = ?",
            (LEAGUE_ID, YEAR),
        ).fetchone()
        print(f"total WEEKLY_PLAYER_SCORE in memory_events = {row[0]}")


if __name__ == "__main__":
    main()
