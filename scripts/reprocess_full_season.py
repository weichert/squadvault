#!/usr/bin/env python3
"""Batch reprocess all weeks for a season: re-select + regenerate drafts.

Usage:
    ./scripts/py scripts/reprocess_full_season.py \
        --db path/to/squadvault.sqlite \
        --league-id 70985 \
        --season 2024 \
        --start-week 1 \
        --end-week 18

This script:
1. For each week, runs select_weekly_recap_events_v1 (includes all allowlisted
   event types, including WEEKLY_MATCHUP_RESULT)
2. Upserts recap_runs with the new selection data
3. Regenerates draft artifacts via generate_weekly_recap_draft
4. Weeks with zero eligible events are marked WITHHELD

Dry-run by default. Add --execute to actually write changes.
"""
from __future__ import annotations

import argparse
import json
import sys

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run, get_recap_run_state
from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft


_SAFE_MODES = {"LOCK_TO_LOCK", "LOCK_TO_SEASON_END", "LOCK_PLUS_7D_CAP"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch reprocess full season recaps.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--season-end", default=None,
                    help="Optional ISO cap for final-week windowing")
    ap.add_argument("--execute", action="store_true",
                    help="Actually write changes (default is dry-run)")
    ap.add_argument("--skip-regen", action="store_true",
                    help="Only update selections, skip draft regeneration")
    args = ap.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"=== Batch reprocess: {mode} ===")
    print(f"DB       : {args.db}")
    print(f"League   : {args.league_id}")
    print(f"Season   : {args.season}")
    print(f"Weeks    : {args.start_week}-{args.end_week}")
    if args.season_end:
        print(f"Season end: {args.season_end}")
    print()

    summary = {"drafted": [], "withheld": [], "errors": []}

    for w in range(args.start_week, args.end_week + 1):
        # 1. Re-select with full allowlist (includes WEEKLY_MATCHUP_RESULT)
        sel = select_weekly_recap_events_v1(
            args.db, args.league_id, args.season, w,
            season_end=args.season_end,
        )

        window_ok = (
            sel.window.mode in _SAFE_MODES
            and sel.window.window_start
            and sel.window.window_end
            and sel.window.window_start != sel.window.window_end
        )

        has_events = len(sel.canonical_ids) > 0

        if not window_ok or not has_events:
            reason = "no_safe_window" if not window_ok else "zero_eligible_events"
            print(f"  week {w:2d}: WITHHELD ({reason}) "
                  f"window={sel.window.mode} events={len(sel.canonical_ids)}")
            if args.execute:
                upsert_recap_run(
                    args.db,
                    RecapRunRecord(
                        league_id=args.league_id,
                        season=args.season,
                        week_index=w,
                        state="WITHHELD",
                        window_mode=sel.window.mode,
                        window_start=sel.window.window_start,
                        window_end=sel.window.window_end,
                        selection_fingerprint=sel.fingerprint,
                        canonical_ids=sel.canonical_ids,
                        counts_by_type=sel.counts_by_type,
                        reason=reason,
                    ),
                )
            summary["withheld"].append(w)
            continue

        # 2. Upsert recap_run with updated selection
        print(f"  week {w:2d}: DRAFT    events={len(sel.canonical_ids):3d} "
              f"types={sel.counts_by_type} fp={sel.fingerprint[:12]}...")
        if args.execute:
            upsert_recap_run(
                args.db,
                RecapRunRecord(
                    league_id=args.league_id,
                    season=args.season,
                    week_index=w,
                    state="DRAFTED",
                    window_mode=sel.window.mode,
                    window_start=sel.window.window_start,
                    window_end=sel.window.window_end,
                    selection_fingerprint=sel.fingerprint,
                    canonical_ids=sel.canonical_ids,
                    counts_by_type=sel.counts_by_type,
                    reason=None,
                ),
            )

        # 3. Regenerate draft
        if args.execute and not args.skip_regen:
            try:
                res = generate_weekly_recap_draft(
                    db_path=args.db,
                    league_id=args.league_id,
                    season=args.season,
                    week_index=w,
                    reason="batch_reprocess_with_matchup_results",
                    force=True,
                    created_by="batch_reprocess",
                )
                print(f"           regen OK: artifact_id={getattr(res, 'artifact_id', '?')}")
            except Exception as e:
                print(f"           regen ERROR: {e}")
                summary["errors"].append((w, str(e)))

        summary["drafted"].append(w)

    print()
    print(f"=== Summary ({mode}) ===")
    print(f"  Drafted : {len(summary['drafted'])} weeks {summary['drafted']}")
    print(f"  Withheld: {len(summary['withheld'])} weeks {summary['withheld']}")
    if summary["errors"]:
        print(f"  Errors  : {len(summary['errors'])}")
        for w, e in summary["errors"]:
            print(f"    week {w}: {e}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
