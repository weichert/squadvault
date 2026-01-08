import argparse
import sqlite3

from squadvault.core.recaps.render.render_recap_text_v1 import render_recap_text_from_path_v1


def _get_active_artifact_path(db_path: str, league_id: str, season: int, week_index: int) -> str:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT artifact_path
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=? AND status='ACTIVE'
            ORDER BY recap_version DESC
            LIMIT 1;
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        raise SystemExit("No ACTIVE recap with artifact_path found for that week.")

    return str(row[0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    args = ap.parse_args()

    path = _get_active_artifact_path(args.db, args.league_id, args.season, args.week_index)
    print(render_recap_text_from_path_v1(path))


if __name__ == "__main__":
    main()
