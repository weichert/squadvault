#!/usr/bin/env python3
"""Batch regenerate all weekly recap drafts for a season.

Usage:
    ANTHROPIC_API_KEY=sk-... ./scripts/py scripts/regenerate_full_season.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2024 \
        --start-week 1 --end-week 17 \
        --reason "v2-pipeline-backfill"

Dry-run by default. Add --execute to actually write changes.
Each week calls generate_weekly_recap_draft with force=True,
which creates a new DRAFT artifact version (superseding any prior).

The creative layer requires ANTHROPIC_API_KEY in the environment.
Without it, drafts will contain deterministic facts only (no prose).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from squadvault.recaps.weekly_recap_lifecycle import (
    GenerateDraftResult,
    generate_weekly_recap_draft,
)
from squadvault.core.recaps.recap_runs import get_recap_run_state
from squadvault.core.storage.session import DatabaseSession
from squadvault.errors import RecapDataError, RecapNotFoundError


def _latest_artifact_info(
    db_path: str, league_id: str, season: int, week_index: int,
) -> dict | None:
    """Get state and version of the latest WEEKLY_RECAP artifact."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """
            SELECT version, state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()
    if not row:
        return None
    return {"version": int(row[0]), "state": str(row[1])}


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch regenerate full season recaps.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--reason", required=True,
                    help="Audit reason for regeneration (e.g. 'v2-pipeline-backfill')")
    ap.add_argument("--created-by", default="system")
    ap.add_argument("--delay", type=float, default=2.0,
                    help="Seconds to wait between API calls (default: 2.0)")
    ap.add_argument("--execute", action="store_true",
                    help="Actually write changes (default is dry-run)")
    args = ap.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"

    # Pre-flight: check API key
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

    print(f"=== Batch regenerate: {mode} ===")
    print(f"DB         : {args.db}")
    print(f"League     : {args.league_id}")
    print(f"Season     : {args.season}")
    print(f"Weeks      : {args.start_week}-{args.end_week}")
    print(f"Reason     : {args.reason}")
    print(f"Created by : {args.created_by}")
    print(f"API key    : {'SET' if has_key else 'NOT SET (facts-only drafts)'}")
    print(f"Delay      : {args.delay}s between weeks")
    print()

    if not has_key:
        print("WARNING: ANTHROPIC_API_KEY not set — drafts will be facts-only (no prose).")
        print()

    summary: dict[str, list] = {"regenerated": [], "skipped": [], "errors": []}

    for w in range(args.start_week, args.end_week + 1):
        run_state = get_recap_run_state(args.db, args.league_id, args.season, w)
        info = _latest_artifact_info(args.db, args.league_id, args.season, w)

        if run_state is None:
            reason = "no recap_runs row"
            print(f"  week {w:2d}: SKIP -- {reason}")
            summary["skipped"].append((w, reason))
            continue

        current_desc = ""
        if info:
            current_desc = f" (current: v{info['version']} {info['state']})"

        if not args.execute:
            print(f"  week {w:2d}: WOULD REGENERATE{current_desc}")
            summary["regenerated"].append(w)
            continue

        try:
            t0 = time.monotonic()
            res: GenerateDraftResult = generate_weekly_recap_draft(
                db_path=args.db,
                league_id=args.league_id,
                season=args.season,
                week_index=w,
                reason=args.reason,
                force=True,
                created_by=args.created_by,
            )
            elapsed = time.monotonic() - t0

            status = "NEW" if res.created_new else "IDEMPOTENT"
            superseded_msg = ""
            if res.prev_approved_version is not None:
                superseded_msg = f" (prev approved: v{res.prev_approved_version})"

            print(
                f"  week {w:2d}: {status} v{res.version}{superseded_msg}"
                f" -> recap_run={res.synced_recap_run_state}"
                f" [{elapsed:.1f}s]"
            )
            summary["regenerated"].append(w)

            # Delay between API calls to respect rate limits
            if w < args.end_week and args.delay > 0:
                time.sleep(args.delay)

        except (RecapNotFoundError, RecapDataError) as e:
            print(f"  week {w:2d}: ERROR -- {e}")
            summary["errors"].append((w, str(e)))
        except Exception as e:
            print(f"  week {w:2d}: ERROR -- {type(e).__name__}: {e}")
            summary["errors"].append((w, str(e)))

    print()
    print(f"=== Summary ({mode}) ===")
    print(f"  Regenerated: {len(summary['regenerated'])} weeks {summary['regenerated']}")
    print(f"  Skipped    : {len(summary['skipped'])} weeks")
    for w, reason in summary["skipped"]:
        print(f"               week {w}: {reason}")
    if summary["errors"]:
        print(f"  Errors     : {len(summary['errors'])}")
        for w, e in summary["errors"]:
            print(f"               week {w}: {e}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
