    #!/usr/bin/env python3

    import argparse
    import sqlite3
    from typing import Optional

    from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
    from squadvault.core.recaps.recap_store import get_latest_recap_row, set_recap_artifact
    from squadvault.core.recaps.artifacts.write_recap_artifact_v1 import write_recap_artifact_v1
    from squadvault.core.recaps.recap_runs import get_recap_run_state, update_recap_run_state
    from squadvault.core.recaps.recap_store import ensure_weekly_recap_artifact_row_if_missing
    from squadvault.core.recaps.recap_store import (
        get_latest_recap_row,
        set_recap_artifact,
        ensure_weekly_recap_artifact_row_if_missing,
    )

    ARTIFACT_TYPE = "WEEKLY_RECAP"


    def _db_connect(db_path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def main() -> None:
        ap = argparse.ArgumentParser()
        ap.add_argument("--db", required=True)
        ap.add_argument("--base-dir", default="artifacts")
        ap.add_argument("--league-id", required=True)
        ap.add_argument("--season", type=int, required=True)
        ap.add_argument("--week-index", type=int, required=True)
        args = ap.parse_args()

        # Gate: only write/attach artifacts right after init (DRAFTED)
        state = get_recap_run_state(args.db, args.league_id, args.season, args.week_index)
        if state != "DRAFTED":
            print(f"recap_write: SKIPPED (state={state})")
            return

        latest = get_latest_recap_row(args.db, args.league_id, args.season, args.week_index)
        if latest is None:
            print("no recap exists for this week")
            return

        latest_version, _latest_fp, latest_status = int(latest[0]), str(latest[1]), str(latest[2])
        if latest_status != "ACTIVE":
            print(f"latest recap is not ACTIVE (status={latest_status}); refusing to attach artifact")
            return

        sel = select_weekly_recap_events_v1(args.db, args.league_id, args.season, args.week_index)
        if sel.window.mode != "LOCK_TO_LOCK":
            print("selection window unavailable")
            return

        ensure_weekly_recap_artifact_row_if_missing(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        version=latest_version,
        state="REVIEW_REQUIRED",
        selection_fingerprint=sel.fingerprint,
        window_start=sel.window.window_start,
        window_end=sel.window.window_end,
    )

        # ✅ Bridge: ensure recap_artifacts row exists so render can find it.
        # Insert-only, no lifecycle mutations.
        _ensure_recap_artifacts_row_exists(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            version=latest_version,
            state="REVIEW_REQUIRED",
            selection_fingerprint=sel.fingerprint,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
        )

        path, payload = write_recap_artifact_v1(
            base_dir=args.base_dir,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            recap_version=latest_version,
            selection=sel,
        )

        set_recap_artifact(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            recap_version=latest_version,
            artifact_path=path,
            artifact_json=payload,
        )

        # Success: artifact exists and is ready for human review
        update_recap_run_state(args.db, args.league_id, args.season, args.week_index, "REVIEW_REQUIRED")

        print("artifact_written:", path)
        print("attached_to_recap_version:", latest_version)
        print("recap_write: DONE -> REVIEW_REQUIRED")


    if __name__ == "__main__":
        main()
