import argparse

from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1

# NOTE: Adjust this import if your function lives elsewhere.
# If you already have this import working in your current file, keep it as-is.
from squadvault.core.recaps.recap_store import insert_recap_v1_if_missing

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Initialize weekly recap (v1) deterministically.")
    p.add_argument("--db", required=True, help="Path to SQLite DB")
    p.add_argument("--league-id", required=True, help="League ID")
    p.add_argument("--season", required=True, type=int, help="Season year")
    p.add_argument("--week-index", required=True, type=int, help="Week index (module-defined)")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()

    # 1) Deterministic selection
    sel = select_weekly_recap_events_v1(args.db, args.league_id, args.season, args.week_index)

    # 2) HARD GATE: if window is unsafe, WITHHOLD immediately
    if sel.window.mode != "LOCK_TO_LOCK" or not sel.window.window_start or not sel.window.window_end:
        upsert_recap_run(
            args.db,
            RecapRunRecord(
                league_id=args.league_id,
                season=args.season,
                week_index=args.week_index,
                state="WITHHELD",
                window_mode=getattr(sel.window, "mode", None),
                window_start=getattr(sel.window, "window_start", None),
                window_end=getattr(sel.window, "window_end", None),
                selection_fingerprint=sel.fingerprint,
                canonical_ids=sel.canonical_ids,
                counts_by_type=sel.counts_by_type,
                reason="unsafe_window_or_missing_lock",
            ),
        )
        print("recap_init: WITHHELD (unsafe_window_or_missing_lock)")
        return

    # 3) Otherwise: record deterministic inputs and allow drafting
    upsert_recap_run(
        args.db,
        RecapRunRecord(
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
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

    # 4) Initialize recap v1 record if missing (existing behavior)
    inserted = insert_recap_v1_if_missing(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        selection_fingerprint=sel.fingerprint,
        window_start=sel.window.window_start,
        window_end=sel.window.window_end,
    )

    if inserted:
        print("recap_init: INSERTED v1")
    else:
        print("recap_init: SKIPPED (already exists)")


if __name__ == "__main__":
    main()
