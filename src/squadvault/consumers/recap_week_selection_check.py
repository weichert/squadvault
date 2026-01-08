import argparse

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.selection.recap_selection_store import (
    get_stored_selection,
    is_stale,
)
from squadvault.core.recaps.recap_store import upsert_selection_if_stale

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--persist", action="store_true")
    args = ap.parse_args()

    sel = select_weekly_recap_events_v1(args.db, args.league_id, args.season, args.week_index)
    stored = get_stored_selection(args.db, args.league_id, args.season, args.week_index)

    print("mode:", sel.window.mode)
    print("window:", sel.window.window_start, "->", sel.window.window_end)
    print("event_count:", len(sel.canonical_ids))
    print("counts_by_type:", sel.counts_by_type)
    print("fingerprint:", sel.fingerprint)

    if stored is None:
        print("stored: NONE")
        print("status: NEW")
    else:
        print("stored_fingerprint:", stored.fingerprint)
        print("stored_computed_at:", stored.computed_at)
        print("status:", "STALE" if is_stale(stored, sel) else "FRESH")

    if args.persist:
        result = upsert_selection_if_stale(args.db, args.league_id, args.season, sel)
        print("persisted:", result)

if __name__ == "__main__":
    main()
