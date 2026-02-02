#!/usr/bin/env python3
"""
Batch recap tooling: verdicts (Phase 2D) + safe workflow driver (Option A)

Modes:
- verdicts: Phase 2D gating report only (no generation).
- drive_workflow: safe init/write/enrich/view driver (DRY-RUN by default; requires --execute to run).

Key behavior:
- REVIEW_REQUIRED: run enrich -> render (because DB row may be missing / stale).
- WITHHELD: skip write/enrich/render (never crash because no week directory is expected).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import sqlite3
from typing import Optional, List

# Only these states are terminal for batch driving purposes.
TERMINAL_STATES = {"APPROVED", "WITHHELD"}


def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_run_state(conn: sqlite3.Connection, league_id: str, season: int, week_index: int) -> Optional[str]:
    row = conn.execute(
        """
        SELECT state
        FROM recap_runs
        WHERE league_id=? AND season=? AND week_index=?
        """,
        (league_id, season, week_index),
    ).fetchone()
    return None if row is None else str(row["state"])


def sh(cmd: List[str], execute: bool) -> None:
    prefix = "[RUN]" if execute else "[DRY-RUN]"
    print(f"{prefix} {' '.join(cmd)}")
    if execute:
        subprocess.run(cmd, check=True)


def run_drive_workflow(
    *,
    db_path: str,
    league_id: str,
    season: int,
    start_week: int,
    end_week: int,
    base_dir: str,
    execute: bool,
) -> int:
    print("=== Safe Workflow Driver (Option A) ===")
    print(f"DB       : {db_path}")
    print(f"League   : {league_id}")
    print(f"Season   : {season}")
    print(f"Weeks    : {start_week}..{end_week}")
    print(f"Mode     : {'EXECUTE' if execute else 'DRY-RUN'}")
    print("")

    conn = db_connect(db_path)
    try:
        for w in range(start_week, end_week + 1):
            state = get_run_state(conn, league_id, season, w)

            print(f"=== week {w:02d} state={state} ===")

            # Terminal: do nothing.
            if state in TERMINAL_STATES:
                print(f"week {w:02d}: SKIP (terminal state={state})")
                print("")
                continue

            # REVIEW_REQUIRED: re-run enrich/render only (idempotent + fixes missing/stale rendered_text).
            if state == "REVIEW_REQUIRED":
                sh(
                    [
                        sys.executable,
                        "-u",
                        "src/squadvault/consumers/recap_week_enrich_artifact.py",
                        "--db",
                        db_path,
                        "--league-id",
                        league_id,
                        "--season",
                        str(season),
                        "--week-index",
                        str(w),
                    ],
                    execute,
                )
                sh(
                    [
                        sys.executable,
                        "-u",
                        "src/squadvault/consumers/recap_week_render.py",
                        "--db",
                        db_path,
                        "--league-id",
                        league_id,
                        "--season",
                        str(season),
                        "--week-index",
                        str(w),
                        "--suppress-render-warning",
                    ],
                    execute,
                )
                print(f"week {w:02d}: {'DONE' if execute else 'DRY-RUN'} state=REVIEW_REQUIRED")
                print("")
                continue

            # For everything else (None / DRAFTED / WRITTEN / etc.), follow the safe workflow.
            sh(
                [
                    sys.executable,
                    "-u",
                    "src/squadvault/consumers/recap_week_gating_check.py",
                    "--db",
                    db_path,
                    "--league-id",
                    league_id,
                    "--season",
                    str(season),
                    "--week-index",
                    str(w),
                ],
                execute,
            )

            sh(
                [
                    sys.executable,
                    "-u",
                    "src/squadvault/consumers/recap_week_init.py",
                    "--db",
                    db_path,
                    "--league-id",
                    league_id,
                    "--season",
                    str(season),
                    "--week-index",
                    str(w),
                ],
                execute,
            )

            # Critical safety: init may WITHHOLD (unsafe window / missing lock). If so, skip remaining steps.
            state_after_init = get_run_state(conn, league_id, season, w)
            if state_after_init == "WITHHELD":
                print(f"week {w:02d}: WITHHELD (skipping write/enrich/render)")
                print("")
                continue

            # If init didn't land in DRAFTED, don't try to write/enrich/render.
            # This keeps the driver resilient to unexpected states.
            if state_after_init not in (None, "DRAFTED"):
                print(f"week {w:02d}: SKIP (post-init state={state_after_init})")
                print("")
                continue

            sh(
                [
                    sys.executable,
                    "-u",
                    "src/squadvault/consumers/recap_week_write_artifact.py",
                    "--db",
                    db_path,
                    "--base-dir",
                    base_dir,
                    "--league-id",
                    league_id,
                    "--season",
                    str(season),
                    "--week-index",
                    str(w),
                ],
                execute,
            )

            # Bridge: enrich -> DB rendered_text
            sh(
                [
                    sys.executable,
                    "-u",
                    "src/squadvault/consumers/recap_week_enrich_artifact.py",
                    "--db",
                    db_path,
                    "--league-id",
                    league_id,
                    "--season",
                    str(season),
                    "--week-index",
                    str(w),
                ],
                execute,
            )

            sh(
                [
                    sys.executable,
                    "-u",
                    "src/squadvault/consumers/recap_week_render.py",
                    "--db",
                    db_path,
                    "--league-id",
                    league_id,
                    "--season",
                    str(season),
                    "--week-index",
                    str(w),
                    "--suppress-render-warning",
                ],
                execute,
            )

            # At this point, the run should be REVIEW_REQUIRED (awaiting approval step).
            print(f"week {w:02d}: {'DONE' if execute else 'DRY-RUN'} state=REVIEW_REQUIRED")
            print("")
    finally:
        conn.close()

    return 0


def run_verdicts(
    *,
    db_path: str,
    league_id: str,
    season: int,
    season_start: str,
    season_end: str,
    persist_verdicts: bool,
    verdict_table: str,
) -> int:
    # NOTE: This mode is intentionally report-only in the MVP; wiring is handled elsewhere.
    print("=== Verdicts mode ===")
    print("NOTE: verdicts mode is report-only (no generation).")
    print(f"DB          : {db_path}")
    print(f"League      : {league_id}")
    print(f"Season      : {season}")
    print(f"Season start: {season_start}")
    print(f"Season end  : {season_end}")
    print(f"Persist     : {persist_verdicts}")
    print(f"Table       : {verdict_table}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Batch recap tooling: verdicts (Phase 2D) + safe workflow driver (Option A)"
    )
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)

    ap.add_argument(
        "--mode",
        choices=["verdicts", "drive_workflow"],
        default="verdicts",
        help="verdicts = Phase 2D gating report only (no generation). drive_workflow = safe init/write/enrich/render driver.",
    )

    ap.add_argument("--season-start", help="(verdicts) ISO start, e.g. 2024-08-01T00:00:00Z")
    ap.add_argument("--season-end", help="(verdicts) ISO end, e.g. 2024-12-31T23:59:59Z")
    ap.add_argument("--persist-verdicts", action="store_true")
    ap.add_argument("--verdict-table", default="recap_verdicts")

    ap.add_argument("--start-week-index", type=int, default=None, help="(drive_workflow) start week index (inclusive)")
    ap.add_argument("--end-week-index", type=int, default=None, help="(drive_workflow) end week index (inclusive)")
    ap.add_argument("--base-dir", default="artifacts", help="(drive_workflow) artifact base dir")
    ap.add_argument("--execute", action="store_true", help="(drive_workflow) actually run gating/init/write/enrich/render.")

    args = ap.parse_args()

    if args.mode == "verdicts":
        if not args.season_start or not args.season_end:
            raise SystemExit("--season-start and --season-end are required in --mode verdicts")
        return run_verdicts(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            season_start=args.season_start,
            season_end=args.season_end,
            persist_verdicts=args.persist_verdicts,
            verdict_table=args.verdict_table,
        )

    if args.start_week_index is None or args.end_week_index is None:
        raise SystemExit("--start-week-index and --end-week-index are required in --mode drive_workflow")

    return run_drive_workflow(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        start_week=args.start_week_index,
        end_week=args.end_week_index,
        base_dir=args.base_dir,
        execute=args.execute,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
