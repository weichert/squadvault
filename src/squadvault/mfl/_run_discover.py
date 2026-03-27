#!/usr/bin/env python3
"""
SquadVault: MFL League Discovery

Probes an MFL league across multiple seasons to determine:
- Which seasons the league was active
- What MFL server hosts each season
- How many franchises per season

This is a read-only operation — no database writes.

Usage:
  ./scripts/py -u src/squadvault/mfl/_run_discover.py \
    --league-id 70985 \
    --start-year 2009 \
    --end-year 2025 \
    --known-server www44.myfantasyleague.com
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from squadvault.mfl.discovery import discover_mfl_league


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for MFL league discovery."""
    ap = argparse.ArgumentParser(
        description="Discover available seasons for an MFL league."
    )
    ap.add_argument(
        "--league-id",
        required=True,
        help="MFL league identifier (e.g. 70985)",
    )
    ap.add_argument(
        "--start-year",
        type=int,
        default=2009,
        help="First year to probe (default: 2009)",
    )
    ap.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="Last year to probe (default: 2025)",
    )
    ap.add_argument(
        "--known-server",
        default="www44.myfantasyleague.com",
        help="Starting MFL server (default: www44.myfantasyleague.com)",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between API calls (default: 1.0)",
    )
    ap.add_argument(
        "--expected-franchises",
        type=int,
        default=None,
        help="Expected franchise count (flag mismatches as suspect)",
    )
    ap.add_argument(
        "--expected-name",
        default=None,
        help="Expected league name substring (flag mismatches as suspect)",
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry attempts per season probe (default: 3)",
    )
    ap.add_argument(
        "--output",
        help="Save discovery report as JSON to this path",
    )
    args = ap.parse_args(argv)

    print("=== SquadVault MFL Discovery ===")
    print(f"League  : {args.league_id}")
    print(f"Range   : {args.start_year}–{args.end_year}")
    print(f"Server  : {args.known_server}")
    if args.expected_franchises:
        print(f"Expected franchises: {args.expected_franchises}")
    if args.expected_name:
        print(f"Expected name: {args.expected_name}")
    print()

    report = discover_mfl_league(
        league_id=args.league_id,
        start_year=args.start_year,
        end_year=args.end_year,
        known_server=args.known_server,
        request_delay_s=args.delay,
        expected_franchise_count=args.expected_franchises,
        expected_league_name=args.expected_name,
        max_retries=args.retries,
    )

    report.print_summary()

    if args.output:
        out_path = Path(args.output)
        report_dict = {
            "league_id": report.league_id,
            "platform": report.platform,
            "probed_range": list(report.probed_range),
            "seasons": [
                {
                    "season": s.season,
                    "server": s.server,
                    "franchise_count": s.franchise_count,
                    "categories": s.categories,
                }
                for s in report.seasons
            ],
            "errors": report.errors,
        }
        out_path.write_text(
            json.dumps(report_dict, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Report saved to: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
