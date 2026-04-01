"""Generate a rivalry chronicle from canonical events."""

#!/usr/bin/env python3
# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT_CONTRACT_V1
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from squadvault.chronicle.generate_rivalry_chronicle_v1 import generate_rivalry_chronicle_v1
from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy
from squadvault.chronicle.persist_rivalry_chronicle_v1 import persist_rivalry_chronicle_v1


def _debug(msg: str) -> None:
    """Print debug message to stderr if SV_DEBUG=1."""
    if os.environ.get("SV_DEBUG") == "1":
        print(msg, file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: generate a rivalry chronicle."""
    ap = argparse.ArgumentParser(description="Generate + persist Rivalry Chronicle v1 (APPROVED recaps only).")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", type=int, required=True)
    ap.add_argument("--season", type=int, required=True)

    # Team pair (contract-compliant path)
    ap.add_argument("--team-a-id", type=str, default=None, help="Franchise ID for Team A")
    ap.add_argument("--team-b-id", type=str, default=None, help="Franchise ID for Team B")

    # Week selection: either --start-week/--end-week or --week-range or --weeks
    week_group = ap.add_mutually_exclusive_group(required=True)
    week_group.add_argument("--week-range", type=str, help="inclusive start:end (e.g., 1:14)")
    week_group.add_argument("--weeks", type=str, help="comma-separated week indices (e.g., 1,2,3)")
    week_group.add_argument("--start-week", type=int, help="Start week (requires --end-week)")

    ap.add_argument("--end-week", type=int, default=None, help="End week (requires --start-week)")

    ap.add_argument(
        "--missing-weeks-policy",
        choices=[p.value for p in MissingWeeksPolicy],
        default=MissingWeeksPolicy.ACKNOWLEDGE_MISSING.value,
        help="refuse OR acknowledge_missing (default)",
    )
    ap.add_argument("--created-at-utc", default=None)
    ap.add_argument("--requested-at-utc", default=None, help="Alias for --created-at-utc (metadata only)")
    ap.add_argument("--out", default=None, help="Optional: write draft payload JSON to this path")

    args = ap.parse_args(argv)

    # Resolve created_at_utc
    created_at_utc = args.created_at_utc or args.requested_at_utc
    if not created_at_utc:
        from datetime import datetime, timezone
        created_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Resolve week selection
    week_range: tuple[int, int] | None = None
    if args.start_week is not None:
        if args.end_week is None:
            raise SystemExit("ERROR: --start-week requires --end-week")
        week_range = (args.start_week, args.end_week)
        week_indices = tuple(range(args.start_week, args.end_week + 1))
    elif args.week_range:
        start_s, end_s = args.week_range.split(":")
        week_range = (int(start_s), int(end_s))
        week_indices = tuple(range(int(start_s), int(end_s) + 1))
    else:
        week_indices = tuple(int(x.strip()) for x in args.weeks.split(",") if x.strip() != "")
        week_range = (min(week_indices), max(week_indices)) if week_indices else None

    if not week_indices:
        raise SystemExit("ERROR: no weeks specified")

    # Validate team pair: both or neither
    team_a_id = getattr(args, "team_a_id", None)
    team_b_id = getattr(args, "team_b_id", None)
    if (team_a_id is None) != (team_b_id is None):
        raise SystemExit("ERROR: --team-a-id and --team-b-id must both be provided or both omitted")

    gen = generate_rivalry_chronicle_v1(
        db_path=args.db,
        league_id=int(args.league_id),
        season=int(args.season),
        week_indices=week_indices,
        week_range=week_range,
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=str(created_at_utc),
        team_a_id=str(team_a_id) if team_a_id is not None else None,
        team_b_id=str(team_b_id) if team_b_id is not None else None,
    )
    txt = str(getattr(gen, 'text', None) or '')
    if not txt.strip():
        raise SystemExit('ERROR: rivalry_chronicle_generate_v1 produced empty gen.text; refusing to persist')

    res = persist_rivalry_chronicle_v1(
        db_path=args.db,
        league_id=int(args.league_id),
        season=int(args.season),
        week_indices=week_indices,
        week_range=week_range,
        missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),
        created_at_utc=str(created_at_utc),
        team_a_id=str(team_a_id) if team_a_id is not None else None,
        team_b_id=str(team_b_id) if team_b_id is not None else None,
    )

    _debug(
        f"OK: {res.artifact_type} league={res.league_id} season={res.season} "
        f"anchor_week={res.anchor_week_index} v={res.version} created_new={res.created_new}"
    )

    if args.out:
        import json
        payload = {
            "artifact_type": res.artifact_type,
            "league_id": res.league_id,
            "season": res.season,
            "anchor_week_index": res.anchor_week_index,
            "version": res.version,
            "created_new": res.created_new,
            "rendered_text": txt,
            "fingerprint": gen.fingerprint,
        }
        from pathlib import Path
        Path(args.out).write_text(json.dumps(payload, indent=2))
        _debug(f"Wrote draft payload to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
