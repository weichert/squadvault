#!/usr/bin/env python3
"""Batch approve all DRAFT weekly recaps for a season.

Usage:
    ./scripts/py scripts/approve_full_season.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2024 \
        --start-week 1 --end-week 18 --approved-by steve

Dry-run by default. Add --execute to actually write changes.
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    RecapNotFoundError,
    RecapStateError,
)
from squadvault.core.recaps.recap_runs import get_recap_run_state
from squadvault.core.storage.session import DatabaseSession


def _latest_artifact_info(
    db_path: str, league_id: str, season: int, week_index: int
) -> Optional[dict]:
    """Get state and version of the latest WEEKLY_RECAP artifact."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """
            SELECT version, state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()
    if not row:
        return None
    return {"version": int(row[0]), "state": str(row[1])}


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch approve full season recaps.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--execute", action="store_true",
                    help="Actually write changes (default is dry-run)")
    args = ap.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"=== Batch approve: {mode} ===")
    print(f"DB         : {args.db}")
    print(f"League     : {args.league_id}")
    print(f"Season     : {args.season}")
    print(f"Weeks      : {args.start_week}-{args.end_week}")
    print(f"Approved by: {args.approved_by}")
    print()

    summary = {"approved": [], "skipped": [], "errors": []}

    for w in range(args.start_week, args.end_week + 1):
        info = _latest_artifact_info(args.db, args.league_id, args.season, w)
        run_state = get_recap_run_state(args.db, args.league_id, args.season, w)

        if info is None:
            reason = f"no artifact (recap_run={run_state or 'NONE'})"
            print(f"  week {w:2d}: SKIP -- {reason}")
            summary["skipped"].append((w, reason))
            continue

        state = info["state"]
        version = info["version"]

        if state in ("DRAFT", "DRAFTED"):
            if not args.execute:
                print(f"  week {w:2d}: WOULD APPROVE v{version} (state={state})")
                summary["approved"].append(w)
                continue

            try:
                res = approve_latest_weekly_recap(
                    db_path=args.db,
                    league_id=args.league_id,
                    season=args.season,
                    week_index=w,
                    approved_by=args.approved_by,
                )
                superseded_msg = ""
                if res.superseded_version is not None:
                    superseded_msg = f" (superseded v{res.superseded_version})"
                print(f"  week {w:2d}: APPROVED v{res.approved_version}{superseded_msg}"
                      f" -> recap_run={res.synced_recap_run_state}")
                summary["approved"].append(w)
            except (RecapNotFoundError, RecapStateError) as e:
                print(f"  week {w:2d}: ERROR -- {e}")
                summary["errors"].append((w, str(e)))
            except Exception as e:
                print(f"  week {w:2d}: ERROR -- {type(e).__name__}: {e}")
                summary["errors"].append((w, str(e)))

        elif state == "APPROVED":
            reason = f"already APPROVED (v{version})"
            print(f"  week {w:2d}: SKIP -- {reason}")
            summary["skipped"].append((w, reason))

        elif state == "WITHHELD":
            reason = f"WITHHELD (v{version})"
            print(f"  week {w:2d}: SKIP -- {reason}")
            summary["skipped"].append((w, reason))

        else:
            reason = f"unexpected state={state} (v{version})"
            print(f"  week {w:2d}: SKIP -- {reason}")
            summary["skipped"].append((w, reason))

    print()
    print(f"=== Summary ({mode}) ===")
    print(f"  Approved : {len(summary['approved'])} weeks {summary['approved']}")
    print(f"  Skipped  : {len(summary['skipped'])} weeks")
    for w, reason in summary["skipped"]:
        print(f"             week {w}: {reason}")
    if summary["errors"]:
        print(f"  Errors   : {len(summary['errors'])}")
        for w, e in summary["errors"]:
            print(f"             week {w}: {e}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
