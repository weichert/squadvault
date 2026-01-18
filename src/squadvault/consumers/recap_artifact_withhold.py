import argparse
import sqlite3

from squadvault.core.recaps.recap_runs import sync_recap_run_state_from_artifacts
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_WEEKLY_RECAP, withhold_recap_artifact


def _artifact_state(db_path: str, league_id: str, season: int, week_index: int, version: int) -> str | None:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
            """,
            (league_id, season, week_index, ARTIFACT_TYPE_WEEKLY_RECAP, version),
        ).fetchone()
        return str(row[0]) if row else None
    finally:
        con.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument(
        "--reason",
        required=True,
        help="Deterministic code preferred (e.g., WINDOW_* or DNG_*).",
    )

    args = ap.parse_args()

    state = _artifact_state(args.db, args.league_id, args.season, args.week_index, args.version)
    if state is None:
        raise RuntimeError("recap_withhold: artifact not found")

    if state == "WITHHELD":
        synced = sync_recap_run_state_from_artifacts(args.db, args.league_id, args.season, args.week_index)
        print(f"recap_withhold: NO-OP (already WITHHELD v{args.version}; ledger={synced})")
        return

    # Normal path: must be DRAFT -> WITHHELD
    withhold_recap_artifact(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        version=args.version,
        withheld_reason=args.reason,
    )

    synced = sync_recap_run_state_from_artifacts(args.db, args.league_id, args.season, args.week_index)
    print(f"recap_withhold: OK (withheld v{args.version}; reason={args.reason}; ledger={synced})")


if __name__ == "__main__":
    main()
