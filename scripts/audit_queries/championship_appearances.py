#!/usr/bin/env python3
"""Championship game appearances by franchise.

Reads WEEKLY_MATCHUP_RESULT at championship weeks:
  W16 for seasons 2010-2020
  W18 for seasons 2021+

Use this to fact-check "X times" championship claims in recap drafts.

Usage:
  ./scripts/py scripts/audit_queries/championship_appearances.py \\
      --league-id 70985

Optional:
  --franchise NAME   Show only the specified franchise (partial name match)
  --through-season N Limit to seasons <= N (default: all available)
  --db PATH          Database path (default: .local_squadvault.sqlite)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = "70985"

# Championship week by era
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
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    ap.add_argument("--franchise", default=None, help="Franchise name (partial match).")
    ap.add_argument("--through-season", type=int, default=None, dest="through_season")
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args(argv)

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    # Load all seasons of franchise names (use most recent per franchise_id)
    name_rows = con.execute(
        """SELECT franchise_id, name, season FROM franchises
           WHERE league_id=? ORDER BY season DESC""",
        (str(args.league_id),),
    ).fetchall()
    name_map: dict[str, str] = {}
    for r in name_rows:
        fid = str(r["franchise_id"])
        if fid not in name_map:
            name_map[fid] = str(r["name"])

    # Load all WEEKLY_MATCHUP_RESULT events
    rows = con.execute(
        """SELECT season, payload_json
           FROM v_canonical_best_events
           WHERE league_id=?
             AND event_type='WEEKLY_MATCHUP_RESULT'
           ORDER BY season ASC""",
        (str(args.league_id),),
    ).fetchall()
    con.close()

    # Count championship appearances per franchise
    appearances: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        season = int(row["season"])
        if args.through_season and season > args.through_season:
            continue
        try:
            p = json.loads(row["payload_json"])
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        week = int(p.get("week", 0))
        if week != champ_week_for_season(season):
            continue

        winner = str(p.get("winner_franchise_id") or p.get("winner_team_id") or "").strip()
        loser = str(p.get("loser_franchise_id") or p.get("loser_team_id") or "").strip()

        try:
            ws = float(p.get("winner_score", 0))
            ls = float(p.get("loser_score", 0))
        except (ValueError, TypeError):
            ws = ls = 0.0

        if winner:
            appearances[winner].append({"season": season, "result": "W", "score": f"{ws:.2f}-{ls:.2f}"})
        if loser:
            appearances[loser].append({"season": season, "result": "L", "score": f"{ws:.2f}-{ls:.2f}"})

    if not appearances:
        print(f"No championship matchups found for league {args.league_id}.")
        return 0

    print(f"\nChampionship appearances — League {args.league_id}")
    if args.through_season:
        print(f"Through season {args.through_season}")
    print("=" * 60)

    sorted_fids = sorted(appearances.keys(), key=lambda f: -len(appearances[f]))
    for fid in sorted_fids:
        fname = name_map.get(fid, fid)
        if args.franchise and args.franchise.lower() not in fname.lower():
            continue
        apps = appearances[fid]
        n = len(apps)
        wins = sum(1 for a in apps if a["result"] == "W")
        losses = n - wins
        print(f"\n  {fname} ({fid}): {n} appearance(s) — {wins}W {losses}L")
        for a in sorted(apps, key=lambda x: x["season"]):
            print(f"    {a['season']}  {a['result']}  {a['score']}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
