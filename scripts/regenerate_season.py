#!/usr/bin/env python3
"""Batch regenerate weekly recap drafts for a season range.

Usage:
    source .env.local  # sets ANTHROPIC_API_KEY
    ./scripts/py scripts/regenerate_season.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2025 \
        --start-week 1 --end-week 18 \
        --reason "competitive-rivalry-regen"

Generates a new DRAFT version for each week (force=True).
Reports verification results per week.
"""
from __future__ import annotations

import argparse
import time

from squadvault.recaps.weekly_recap_lifecycle import (
    GenerateDraftResult,
    RecapNotFoundError,
    generate_weekly_recap_draft,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch regenerate season recaps.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--created-by", default="system")
    ap.add_argument("--delay", type=float, default=2.0,
                    help="Seconds between API calls (rate-limit safety)")
    args = ap.parse_args()

    print("=== Batch regenerate ===")
    print(f"DB         : {args.db}")
    print(f"League     : {args.league_id}")
    print(f"Season     : {args.season}")
    print(f"Weeks      : {args.start_week}-{args.end_week}")
    print(f"Reason     : {args.reason}")
    print(f"Delay      : {args.delay}s between weeks")
    print()

    results: dict[str, list[int]] = {
        "generated": [],
        "skipped": [],
        "failed": [],
        "verification_warn": [],
    }

    for w in range(args.start_week, args.end_week + 1):
        try:
            res: GenerateDraftResult = generate_weekly_recap_draft(
                db_path=args.db,
                league_id=args.league_id,
                season=args.season,
                week_index=w,
                reason=args.reason,
                force=True,
                created_by=args.created_by,
            )

            v_status = "—"
            if res.verification_result is not None:
                hard = len(res.verification_result.hard_failures)
                soft = len(res.verification_result.soft_failures)
                v_status = f"hard={hard} soft={soft}"
                if hard > 0:
                    results["verification_warn"].append(w)

            attempts = res.verification_attempts
            print(
                f"  week {w:2d}: v{res.version} "
                f"(attempts={attempts}, verification: {v_status})"
            )
            results["generated"].append(w)

        except RecapNotFoundError:
            print(f"  week {w:2d}: SKIP — no recap_runs data")
            results["skipped"].append(w)

        except Exception as e:
            print(f"  week {w:2d}: FAIL — {type(e).__name__}: {e}")
            results["failed"].append(w)

        # Rate-limit delay between API calls
        if w < args.end_week:
            time.sleep(args.delay)

    print()
    print("=== Summary ===")
    print(f"  Generated : {len(results['generated'])} weeks")
    print(f"  Skipped   : {len(results['skipped'])} weeks {results['skipped']}")
    print(f"  Failed    : {len(results['failed'])} weeks {results['failed']}")
    if results["verification_warn"]:
        print(f"  V-warnings: {results['verification_warn']}")

    return 1 if results["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
