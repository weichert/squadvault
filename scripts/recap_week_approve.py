#!/usr/bin/env python3
# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md

from __future__ import annotations

import argparse
import json
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Approve latest weekly recap (WEEKLY_RECAP) artifact")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--approved-by", required=True)
    ap.add_argument(
        "--require-draft",
        action="store_true",
        help="Refuse to approve unless a DRAFT exists (approvable state).",
    )
    args = ap.parse_args()

    if args.require_draft and not _has_draft(args.db, args.league_id, args.season, args.week_index):
        raise SystemExit("Refusing to approve: no DRAFT WEEKLY_RECAP artifact exists for that week.")

    res = approve_latest_weekly_recap(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        approved_by=args.approved_by,
    )

    print(json.dumps(res.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
