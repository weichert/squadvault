import argparse

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_store import (
    get_latest_recap_row,
    mark_latest_stale_if_needed,
    insert_regenerated_recap,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--regenerate", action="store_true")
    args = ap.parse_args()

    sel = select_weekly_recap_events_v1(args.db, args.league_id, args.season, args.week_index)
    if sel.window.mode != "LOCK_TO_LOCK":
        print("status: UNAVAILABLE (no safe window)")
        return

    latest = get_latest_recap_row(args.db, args.league_id, args.season, args.week_index)
    if latest is None:
        print("status: NO_RECAP")
        print("current_fingerprint:", sel.fingerprint)
        return

    latest_version, latest_fp, latest_status = int(latest[0]), str(latest[1]), str(latest[2])

    print("latest_version:", latest_version)
    print("latest_status:", latest_status)
    print("latest_fingerprint:", latest_fp)
    print("current_fingerprint:", sel.fingerprint)

    if latest_fp == sel.fingerprint:
        print("status: FRESH")
        return

    # Mark stale
    marked = mark_latest_stale_if_needed(args.db, args.league_id, args.season, args.week_index, sel.fingerprint)
    print("status: STALE" if marked else "status: STALE_ALREADY")

    if args.regenerate:
        new_v = insert_regenerated_recap(
            args.db,
            args.league_id,
            args.season,
            args.week_index,
            sel.fingerprint,
            sel.window.window_start,
            sel.window.window_end,
        )
        print("regenerated_version:", new_v)


if __name__ == "__main__":
    main()
