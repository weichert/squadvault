import argparse

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_store import insert_recap_v1_if_missing


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    args = ap.parse_args()

    sel = select_weekly_recap_events_v1(args.db, args.league_id, args.season, args.week_index)

    if sel.window.mode != "LOCK_TO_LOCK":
        print("recap_init: UNAVAILABLE (no safe window)")
        return

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
