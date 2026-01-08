import argparse

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_store import get_latest_recap_row, set_recap_artifact
from squadvault.core.recaps.artifacts.write_recap_artifact_v1 import write_recap_artifact_v1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--base-dir", default="artifacts")
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    args = ap.parse_args()

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

    print("artifact_written:", path)
    print("attached_to_recap_version:", latest_version)


if __name__ == "__main__":
    main()
