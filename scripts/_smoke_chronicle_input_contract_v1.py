#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Sequence

from squadvault.chronicle.approved_recap_refs_v1 import load_latest_approved_recap_refs_v1
from squadvault.chronicle.input_contract_v1 import (
    ChronicleInputResolverV1,
    MissingWeeksPolicy,
    RivalryChronicleInputV1,
)
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_WEEKLY_RECAP

WEEKLY_RECAP_ARTIFACT_TYPE = ARTIFACT_TYPE_WEEKLY_RECAP


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

    args = ap.parse_args()

    if args.week_range:
        start_s, end_s = args.week_range.split(":")
        week_range = (int(start_s), int(end_s))
        week_indices = None
    else:
        week_indices = tuple(int(x.strip()) for x in args.weeks.split(",") if x.strip() != "")
        week_range = None

    inp = RivalryChronicleInputV1(
        league_id=args.league_id,
        season=args.season,
        week_indices=week_indices,
        week_range=week_range,
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
    )

    def _loader(league_id: int, season: int, weeks: Sequence[int]):
        return load_latest_approved_recap_refs_v1(
            db_path=args.db,
            league_id=league_id,
            season=season,
            artifact_type=WEEKLY_RECAP_ARTIFACT_TYPE,
            week_indices=weeks,
        )

    resolver = ChronicleInputResolverV1(_loader)
    resolved = resolver.resolve(inp)

    payload = {
        "league_id": resolved.league_id,
        "season": resolved.season,
        "artifact_type": WEEKLY_RECAP_ARTIFACT_TYPE,
        "weeks_requested": list(resolved.week_indices),
        "weeks_missing": list(resolved.missing_weeks),
        "approved_recaps": [
            {
                "week_index": r.week_index,
                "artifact_type": r.artifact_type,
                "version": r.version,
                "selection_fingerprint": r.selection_fingerprint,
            }
            for r in resolved.approved_recaps
        ],
    }

    print(json.dumps(payload, indent=2, sort_keys=True))
    _debug("SV_DEBUG=1 enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
