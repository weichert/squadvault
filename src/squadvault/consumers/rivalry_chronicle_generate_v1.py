#!/usr/bin/env python3
# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT_CONTRACT_V1
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_output_contract_v1.md

from __future__ import annotations
# SV_PATCH_RC_GENERATE_PASS_BOTH_WEEK_SELECTORS_V4: restore-from-HEAD then pass both week_indices+week_range safely

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
    # Generator/persist may require week_indices and/or week_range (kw-only).
    # Compute BOTH and pass supported kwargs (signature-filtered).
    import inspect

    def _filter_kwargs(fn, kwargs):
        params = set(inspect.signature(fn).parameters.keys())
        return {k: v for k, v in kwargs.items() if k in params}

    # CLI guarantees exactly one of (week_indices, week_range) is set.
    if week_range is None:
        if not week_indices:
            raise SystemExit('ERROR: --weeks provided but empty')
        week_indices_eff = tuple(int(x) for x in week_indices)
        week_range_eff = (min(week_indices_eff), max(week_indices_eff))
    else:
        w0, w1 = int(week_range[0]), int(week_range[1])
        if w1 < w0:
            raise SystemExit('ERROR: --week-range end < start')
        week_range_eff = (w0, w1)
        week_indices_eff = tuple(range(w0, w1 + 1))

    gen_kwargs = dict(
        db_path=args.db,
        league_id=int(args.league_id),
        season=int(args.season),
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=str(args.created_at_utc),
        week_indices=week_indices_eff,
        week_range=week_range_eff,
    )
    gen = generate_rivalry_chronicle_v1(**_filter_kwargs(generate_rivalry_chronicle_v1, gen_kwargs))
    txt = str(getattr(gen, 'text', None) or '')
    if not txt.strip():
        raise SystemExit('ERROR: rivalry_chronicle_generate_v1 produced empty gen.text; refusing to persist')

    persist_kwargs = dict(
        rendered_text=txt,
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=args.created_at_utc,
        week_indices=week_indices_eff,
        week_range=week_range_eff,
    )
    res = persist_rivalry_chronicle_v1(**_filter_kwargs(persist_rivalry_chronicle_v1, persist_kwargs))

    _debug(
        f"OK: {res.artifact_type} league={res.league_id} season={res.season} "
        f"anchor_week={res.anchor_week_index} v={res.version} created_new={res.created_new}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
