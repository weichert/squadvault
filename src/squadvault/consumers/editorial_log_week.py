from __future__ import annotations

import argparse
import sqlite3
import sys

from squadvault.consumers.editorial_actions import fetch_editorial_log


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Show editorial action log for a week")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args(argv)

    conn = sqlite3.connect(args.db)
    rows = fetch_editorial_log(
        conn,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        limit=args.limit,
    )

    if not rows:
        print("(no editorial actions logged)")
        return 0

    print("")
    print(f"Editorial Log — League {args.league_id} — Season {args.season} — Week {args.week_index}")
    print("-------------------------------------------------------------------")
    for created_at, actor, action, version, fp, notes in rows:
        suffix = f" | notes: {notes}" if notes else ""
        print(f"{created_at} | {actor} | {action} | v{int(version):02d} | {fp or '-'}{suffix}")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
