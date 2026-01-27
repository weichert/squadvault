#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy
from squadvault.chronicle.generate_rivalry_chronicle_v1 import generate_rivalry_chronicle_v1
from squadvault.chronicle.persist_rivalry_chronicle_v1 import persist_rivalry_chronicle_v1


def _debug(msg: str) -> None:
    if os.environ.get("SV_DEBUG") == "1":
        print(msg, file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate + persist Rivalry Chronicle v1 (APPROVED recaps only).")
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
        help="refuse (default) OR acknowledge_missing",
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

    # SV_PATCH_V4: chronicle consumer generates gen.text before persist
    # SV_PATCH_V4_1: pass exactly one of week_indices/week_range to generator
    # SV_PATCH_RIVALRY_CHRONICLE_GENERATE_V1: generate text, validate non-empty, pass persist kwargs
    gen_kwargs = dict(
        db_path=args.db,
        league_id=int(args.league_id),
        season=int(args.season),
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=str(args.created_at_utc),
    )
    if week_indices is not None:
        gen_kwargs['week_indices'] = week_indices
    else:
        gen_kwargs['week_range'] = week_range
    gen = generate_rivalry_chronicle_v1(**gen_kwargs)
    txt = str(getattr(gen, 'text', None) or '')
    if not txt.strip():
        raise SystemExit('ERROR: rivalry_chronicle_generate_v1 produced empty gen.text; refusing to persist.')
    # SV_PATCH_V4_2: pass exactly one of week_indices/week_range to persist
    persist_kwargs = dict(
        rendered_text=txt,
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=args.created_at_utc,
    )
    if week_indices is not None:
        persist_kwargs['week_indices'] = week_indices
    else:
        persist_kwargs['week_range'] = week_range
    res = persist_rivalry_chronicle_v1(**persist_kwargs)

    # Quiet-by-default: no stdout on success.
    _debug(
        f"OK: {res.artifact_type} league={res.league_id} season={res.season} "
        f"anchor_week={res.anchor_week_index} v={res.version} created_new={res.created_new}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
