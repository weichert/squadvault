#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy
from squadvault.chronicle.persist_rivalry_chronicle_v1 import persist_rivalry_chronicle_v1


def _debug(msg: str) -> None:
    if os.environ.get("SV_DEBUG") == "1":
        print(msg, file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", type=int, required=True)
    ap.add_argument("--season", type=int, required=True)

    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--week-range", type=str, help="inclusive start:end (e.g., 1:14)")
    g.add_argument("--weeks", type=str, help="comma-separated week indices (e.g., 1,2,3)")

    ap.add_argument(
        "--missing-weeks-policy",
        choices=[p.value for p in MissingWeeksPolicy],
        default=MissingWeeksPolicy.REFUSE.value,
    )

    ap.add_argument("--created-at-utc", required=True)

    args = ap.parse_args()

    if args.week_range:
        start_s, end_s = args.week_range.split(":")
        week_range = (int(start_s), int(end_s))
        week_indices = None
    else:
        week_indices = tuple(int(x.strip()) for x in args.weeks.split(",") if x.strip() != "")
        week_range = None

    res = persist_rivalry_chronicle_v1(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_indices=week_indices,
        week_range=week_range,
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=args.created_at_utc,
    )

    _debug(
        f"Persisted {res.artifact_type} league={res.league_id} season={res.season} "
        f"anchor_week={res.anchor_week_index} v={res.version} created_new={res.created_new}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
