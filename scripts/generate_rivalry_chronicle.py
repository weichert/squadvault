#!/usr/bin/env python3
"""Convenience shim for generating Rivalry Chronicle artifacts.

Delegates to src/squadvault/consumers/rivalry_chronicle_generate_v1.py with
PFL Buddies defaults pre-filled. Standard invocation:

  ./scripts/py scripts/generate_rivalry_chronicle.py \\
      --team-a-id 0001 --team-b-id 0002 --season 2025 --start-week 1 --end-week 18

This generates a RIVALRY_CHRONICLE_V1 DRAFT artifact in the database for the
specified team pair and season. Approve with:

  ./scripts/py src/squadvault/consumers/rivalry_chronicle_approve_v1.py \\
      --db .local_squadvault.sqlite --league-id 70985 --season 2025 \\
      --week-index 18 --approved-by steve

Then verify the approved artifact with:

  ./scripts/py -c "
from squadvault.core.recaps.verification.chronicle_verifier_v1 import verify_chronicle_v1
import sqlite3
conn = sqlite3.connect('.local_squadvault.sqlite')
text = conn.execute(
    \"SELECT rendered_text FROM recap_artifacts WHERE artifact_type='RIVALRY_CHRONICLE_V1'
     AND state='APPROVED' ORDER BY version DESC LIMIT 1\"
).fetchone()[0]
r = verify_chronicle_v1(text)
print('passed:', r.passed, 'hard:', r.hard_failure_count, 'soft:', r.soft_failure_count)
"

This script imports from squadvault.core and must be run through the
./scripts/py shim, which sets PYTHONPATH=src.
"""

from __future__ import annotations

import argparse
import sys

from squadvault.consumers.rivalry_chronicle_generate_v1 import main as _generate_main

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = 70985


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Generate Rivalry Chronicle artifact (PFL Buddies shortcut).",
    )
    ap.add_argument("--team-a-id", required=True, help="Franchise ID for Team A (e.g. 0001).")
    ap.add_argument("--team-b-id", required=True, help="Franchise ID for Team B (e.g. 0002).")
    ap.add_argument("--season", type=int, default=None, help="NFL season year (omit when using --all-time or --start-season).")

    week_group = ap.add_mutually_exclusive_group(required=False)
    week_group.add_argument("--start-week", type=int, help="Start week (requires --end-week).")
    week_group.add_argument("--weeks", type=str, help="Comma-separated weeks (e.g. 1,2,3).")
    week_group.add_argument("--week-range", type=str, help="Inclusive range start:end (e.g. 1:18).")

    ap.add_argument("--end-week", type=int, default=None, help="End week (with --start-week).")
    ap.add_argument("--db", default=DEFAULT_DB, help=f"Database path (default: {DEFAULT_DB}).")
    ap.add_argument(
        "--missing-weeks-policy",
        default="acknowledge_missing",
        choices=["refuse", "acknowledge_missing"],
        help="Policy for weeks without approved recaps (default: acknowledge_missing).",
    )
    ap.add_argument("--out", default=None, help="Optional: write draft payload JSON to this path.")
    ap.add_argument("--all-time", action="store_true",
        help="Generate chronicle across all digital-era seasons (2010-2025).")
    ap.add_argument("--start-season", type=int, default=None,
        help="Multi-season start year.")
    ap.add_argument("--end-season", type=int, default=None,
        help="Multi-season end year (with --start-season).")
    args = ap.parse_args(argv)

    # Build args for the underlying consumer.
    # Multi-season path
    if args.all_time or args.start_season is not None:
        start = 2010 if args.all_time else args.start_season
        end = 2025 if args.all_time else args.end_season
        if end is None:
            print("ERROR: --start-season requires --end-season", file=sys.stderr)
            return 2
        consumer_argv = [
            "--db", args.db,
            "--league-id", str(DEFAULT_LEAGUE_ID),
            "--start-season", str(start),
            "--end-season", str(end),
            "--team-a-id", args.team_a_id,
            "--team-b-id", args.team_b_id,
            "--missing-weeks-policy", args.missing_weeks_policy,
        ]
        if args.out:
            consumer_argv += ["--out", args.out]
        return _generate_main(consumer_argv)

    # Single-season path
    consumer_argv = [
        "--db", args.db,
        "--league-id", str(DEFAULT_LEAGUE_ID),
        "--season", str(args.season),
        "--team-a-id", args.team_a_id,
        "--team-b-id", args.team_b_id,
        "--missing-weeks-policy", args.missing_weeks_policy,
    ]

    if args.start_week is not None:
        if args.end_week is None:
            print("ERROR: --start-week requires --end-week", file=sys.stderr)
            return 2
        consumer_argv += ["--start-week", str(args.start_week), "--end-week", str(args.end_week)]
    elif args.weeks:
        consumer_argv += ["--weeks", args.weeks]
    elif args.week_range:
        consumer_argv += ["--week-range", args.week_range]

    if args.out:
        consumer_argv += ["--out", args.out]

    return _generate_main(consumer_argv)


if __name__ == "__main__":
    sys.exit(main())
