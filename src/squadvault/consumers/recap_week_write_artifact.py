#!/usr/bin/env python3

import argparse

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_store import (
    ensure_weekly_recap_artifact_row_if_missing,
    get_latest_recap_row,
    set_recap_artifact,
)
from squadvault.core.recaps.artifacts.write_recap_artifact_v1 import write_recap_artifact_v1
from squadvault.core.recaps.recap_runs import get_recap_run_state, update_recap_run_state

ARTIFACT_TYPE = "WEEKLY_RECAP"
SAFE_WINDOW_MODES = {"LOCK_TO_LOCK", "LOCK_TO_SEASON_END", "LOCK_PLUS_7D_CAP"}


def _is_safe_window(mode: str | None, start: str | None, end: str | None) -> bool:
    return (mode in SAFE_WINDOW_MODES) and bool(start) and bool(end)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--base-dir", default="artifacts")
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument(
        "--season-end",
        default=None,
        help="Optional ISO cap for final-week windowing, e.g. 2024-01-07T18:00:00Z",
    )
    args = ap.parse_args()

    # Gate: only write/attach artifacts right after init (DRAFTED)
    state = get_recap_run_state(args.db, args.league_id, args.season, args.week_index)
    if state != "DRAFTED":
        print(f"recap_write: SKIPPED (state={state})")
        return

    latest = get_latest_recap_row(args.db, args.league_id, args.season, args.week_index)
    if latest is None:
        raise RuntimeError("recap_write: missing recap row (did you run recap_week_init?)")

    recap_version, _selection_fp, _artifact_state = latest

    selection = select_weekly_recap_events_v1(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        season_end=args.season_end,
    )

    # Safety: if window isn't safe, don't write an artifact (should have been gated upstream)
    if not _is_safe_window(selection.window.mode, selection.window.window_start, selection.window.window_end):
        print(
            "recap_write: WITHHELD (unsafe_window_or_missing_bounds)",
            selection.window.mode,
            selection.window.window_start,
            selection.window.window_end,
        )
        return

    window_start = selection.window.window_start
    window_end = selection.window.window_end

    # Ensure artifact row exists (idempotent)
    ensure_weekly_recap_artifact_row_if_missing(
        args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        version=recap_version,
        state="DRAFTED",
        selection_fingerprint=selection.fingerprint,
        window_start=window_start,
        window_end=window_end,
    )

    # NOTE: Empty selection is valid; writer should produce a summary-only artifact.
    artifact_path, artifact_json = write_recap_artifact_v1(
        base_dir=args.base_dir,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        recap_version=recap_version,
        selection=selection,
    )

    set_recap_artifact(
        args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        recap_version=recap_version,
        artifact_path=artifact_path,
        artifact_json=artifact_json,
    )

    update_recap_run_state(args.db, args.league_id, args.season, args.week_index, "WRITTEN")
    print(f"recap_write: OK ({artifact_path})")


if __name__ == "__main__":
    main()
