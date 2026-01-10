#!/usr/bin/env python3

import argparse
import json

from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft


def main() -> int:
    p = argparse.ArgumentParser(description="Regenerate weekly recap artifact draft (canonical lifecycle).")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--created-by", default="system")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    res = generate_weekly_recap_draft(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        reason=args.reason,
        force=args.force,
        created_by=args.created_by,
    )

    print(json.dumps(res.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
