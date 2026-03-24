#!/usr/bin/env python3
"""Verify post-approval integrity for a full season.

Usage:
    ./scripts/py scripts/verify_season_approval.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2024 \
        --start-week 1 --end-week 18 -v
"""
from __future__ import annotations

import argparse
import sys

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.recaps.recap_runs import get_recap_run_state


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify season approval integrity.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="Show content snippets from approved artifacts")
    args = ap.parse_args()

    print(f"=== Season Approval Verification ===")
    print(f"DB     : {args.db}")
    print(f"League : {args.league_id}")
    print(f"Season : {args.season}")
    print(f"Weeks  : {args.start_week}-{args.end_week}")
    print()

    failures = []
    ok_count = 0

    for w in range(args.start_week, args.end_week + 1):
        run_state = get_recap_run_state(args.db, args.league_id, args.season, w)

        with DatabaseSession(args.db) as con:
            approved_rows = con.execute(
                """
                SELECT version, state, approved_by, approved_at, rendered_text
                FROM recap_artifacts
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
                  AND state='APPROVED'
                ORDER BY version DESC
                """,
                (args.league_id, args.season, w),
            ).fetchall()

            all_count = con.execute(
                """
                SELECT COUNT(*)
                FROM recap_artifacts
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
                """,
                (args.league_id, args.season, w),
            ).fetchone()[0]

            withheld_count = con.execute(
                """
                SELECT COUNT(*)
                FROM recap_artifacts
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
                  AND state='WITHHELD'
                """,
                (args.league_id, args.season, w),
            ).fetchone()[0]

        is_withheld = (run_state == "WITHHELD") or (withheld_count > 0 and len(approved_rows) == 0)

        if is_withheld:
            if len(approved_rows) > 0:
                msg = f"WITHHELD week has {len(approved_rows)} APPROVED artifact(s)"
                failures.append((w, msg))
                print(f"  week {w:2d}: FAIL -- {msg}")
            else:
                print(f"  week {w:2d}: OK   -- WITHHELD (recap_run={run_state}, artifacts={all_count})")
                ok_count += 1
            continue

        if run_state is None and all_count == 0:
            print(f"  week {w:2d}: OK   -- no data (no recap_run, no artifacts)")
            ok_count += 1
            continue

        if len(approved_rows) == 0:
            msg = f"no APPROVED artifact (recap_run={run_state}, total_artifacts={all_count})"
            failures.append((w, msg))
            print(f"  week {w:2d}: FAIL -- {msg}")
            continue

        if len(approved_rows) > 1:
            versions = [r[0] for r in approved_rows]
            msg = f"multiple APPROVED artifacts: versions {versions}"
            failures.append((w, msg))
            print(f"  week {w:2d}: FAIL -- {msg}")
            continue

        version, state, approved_by, approved_at, rendered_text = approved_rows[0]

        checks_ok = True
        if not approved_by:
            failures.append((w, "approved_by is NULL"))
            checks_ok = False
        if not approved_at:
            failures.append((w, "approved_at is NULL"))
            checks_ok = False
        if run_state != "APPROVED":
            msg = f"recap_run state={run_state}, expected APPROVED"
            failures.append((w, msg))
            checks_ok = False

        if checks_ok:
            snippet = ""
            if args.verbose and rendered_text:
                clean = rendered_text.replace("\n", " ").strip()
                snippet = f' -- "{clean[:120]}..."'
            print(f"  week {w:2d}: OK   -- APPROVED v{version} by={approved_by} at={approved_at}{snippet}")
            ok_count += 1
        else:
            print(f"  week {w:2d}: FAIL -- see above")

    print()
    print(f"=== Results ===")
    print(f"  OK     : {ok_count}")
    print(f"  FAILED : {len(failures)}")
    if failures:
        for w, msg in failures:
            print(f"    week {w}: {msg}")
        return 1

    print()
    print("All weeks verified. Season approval is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
