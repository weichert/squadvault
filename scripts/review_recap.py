#!/usr/bin/env python3
"""Convenience shim for the commissioner review-and-approve workflow.

Delegates to src/squadvault/consumers/editorial_review_week.py with PFL Buddies
defaults pre-filled. The underlying consumer handles the full interactive loop:
display recap, choose Approve / Regenerate / Withhold / Notes / Quit.

Default invocation (review Week 14 of 2025):
  ./scripts/py scripts/review_recap.py --season 2025 --week-index 14

Override actor (default: value of SQUADVAULT_ACTOR env var, else 'commissioner'):
  ./scripts/py scripts/review_recap.py --season 2025 --week-index 14 --actor steve

Override database:
  ./scripts/py scripts/review_recap.py --season 2025 --week-index 14 --db other.sqlite

This script imports from squadvault.core and must be run through the ./scripts/py
shim, which sets PYTHONPATH=src.
"""

from __future__ import annotations

import argparse
import os
import sys

from squadvault.consumers.editorial_review_week import main as _review_main

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = "70985"
DEFAULT_ACTOR = os.environ.get("SQUADVAULT_ACTOR", "commissioner")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Commissioner recap review-and-approve (PFL Buddies shortcut).",
    )
    ap.add_argument("--season", type=int, required=True, help="NFL season year.")
    ap.add_argument("--week-index", type=int, required=True, help="Week index (1-based).")
    ap.add_argument("--actor", default=DEFAULT_ACTOR, help=f"Approver name (default: {DEFAULT_ACTOR}).")
    ap.add_argument("--db", default=DEFAULT_DB, help=f"Database path (default: {DEFAULT_DB}).")
    ap.add_argument("--base-dir", default="artifacts", help="Artifact base dir (default: artifacts).")
    ap.add_argument(
        "--voice",
        action="append",
        default=[],
        help="Render non-canonical voice variant (repeatable).",
    )
    args = ap.parse_args(argv)

    # Build the argument list for the underlying consumer.
    consumer_argv = [
        "--db", args.db,
        "--league-id", DEFAULT_LEAGUE_ID,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--actor", args.actor,
        "--base-dir", args.base_dir,
    ]
    for v in args.voice:
        consumer_argv += ["--voice", v]

    return _review_main(consumer_argv)


if __name__ == "__main__":
    sys.exit(main())
