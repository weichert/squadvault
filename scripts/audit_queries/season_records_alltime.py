#!/usr/bin/env python3
"""All-time best regular season win-loss records by franchise or season.

Reads WEEKLY_MATCHUP_RESULT, excludes championship weeks, ranks by
winning percentage then total wins.

Use this to fact-check N-M record or best record claims in recap drafts.

Usage:
  ./scripts/py scripts/audit_queries/season_records_alltime.py --league-id 70985

Optional:
  --franchise NAME    Show only the specified franchise (partial name match)
  --season N          Show only the specified season
  --top N             Show only the top N records (default: 10)
  --db PATH           Database path (default: .local_squadvault.sqlite)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = "70985"

_CHAMP_WEEK: list[tuple[range, int]] = [
    (range(2010, 2021), 16),
    (range(2021, 2050), 18),
]


def champ_week_for_season(season: int) -> int:
    for r, w in _CHAMP_WEEK:
        if season in r:
            return w
    return 18


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    ap.add_argument("--franchise", default=None, help="Franchise name (partial match).")
    ap.add_argument("--season", type=int, default=None, help="Filter to one season.")
    ap.add_argument("--top", type=int, default=10, help="Show top N records (default 10).")
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args(argv)

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    name_rows = con.execute(
        "SELECT franchise_id, name, season FROM franchises WHERE league_id=? ORDER BY season DESC",
        (str(args.league_id),),
    ).fetchall()
    name_map: dict[str, str] = {}
    for r in name_rows:
        fid = str(r["franchise_id"])
        if fid not in name_map:
            name_map[fid] = str(r["name"])

    sql = "SELECT season, payload_json FROM v_canonical_best_events WHERE league_id=? AND event_type='WEEKLY_MATCHUP_RESULT'"
    params: list = [str(args.league_id)]
    if args.season:
        sql += " AND season=?"
        params.append(args.season)
    rows = con.execute(sql + " ORDER BY season ASC", params).fetchall()
    con.close()

    records: dict[tuple[str, int], dict] = defaultdict(lambda: {"wins": 0, "losses": 0})

    for row in rows:
        season = int(row["season"])
        try:
            p = json.loads(row["payload_json"])
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue
        week = int(p.get("week", 0))
        if week == champ_week_for_season(season):
            continue
        winner = str(p.get("winner_franchise_id") or p.get("winner_team_id") or "").strip()
        loser = str(p.get("loser_franchise_id") or p.get("loser_team_id") or "").strip()
        if winner:
            records[(winner, season)]["wins"] += 1
        if loser:
            records[(loser, season)]["losses"] += 1

    if not records:
        print(f"No matchup records found for league {args.league_id}.")
        return 0

    entries: list[dict] = []
    for (fid, season), rec in records.items():
        w, l = rec["wins"], rec["losses"]
        total = w + l
        pct = w / total if total > 0 else 0.0
        fname = name_map.get(fid, fid)
        if args.franchise and args.franchise.lower() not in fname.lower():
            continue
        entries.append({"franchise_id": fid, "franchise_name": fname,
                         "season": season, "wins": w, "losses": l, "pct": pct})

    entries.sort(key=lambda e: (-e["pct"], -e["wins"], e["season"]))
    top = entries[:args.top]

    print(f"\nAll-time best regular season records -- League {args.league_id}")
    if args.season:
        print(f"Season filter: {args.season}")
    print("=" * 60)
    print(f"  {'#':>3}  {'W-L':>6}  {'Pct':>5}  {'Season':>6}  Franchise")
    print(f"  {'---':>3}  {'------':>6}  {'-----':>5}  {'------':>6}  {'---'}")
    for i, e in enumerate(top, 1):
        print(
            f"  {i:>3}  {e['wins']}-{e['losses']:<2}   "
            f"{e['pct']:.3f}  {e['season']:>6}  {e['franchise_name']}"
        )

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
