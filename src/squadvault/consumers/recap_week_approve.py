from __future__ import annotations

import argparse
import sqlite3

from squadvault.recaps.weekly_recap_lifecycle import approve_latest_weekly_recap


def _has_draft(db_path: str, league_id: str, season: int, week_index: int) -> bool:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT 1
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND state='DRAFT'
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()
        return row is not None
    finally:
        con.close()


def approve_week(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    approved_by: str,
    require_draft: bool = False,
) -> None:
    """
    Thin wrapper: canonical approval lives in squadvault.recaps.weekly_recap_lifecycle.
    """
    if require_draft and not _has_draft(db_path, league_id, season, week_index):
        raise SystemExit("Refusing to approve: no DRAFT WEEKLY_RECAP artifact exists for that week.")

    # Canonical: approves latest DRAFT and supersedes prior APPROVED (if any), then syncs recap_runs.
    res = approve_latest_weekly_recap(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        approved_by=approved_by,
    )
    print(res)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--approved-by", required=True)
    ap.add_argument(
        "--require-draft",
        action="store_true",
        help="Refuse to approve unless a DRAFT WEEKLY_RECAP artifact exists.",
    )

    args = ap.parse_args()
    approve_week(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        approved_by=args.approved_by,
        require_draft=args.require_draft,
    )


if __name__ == "__main__":
    main()
