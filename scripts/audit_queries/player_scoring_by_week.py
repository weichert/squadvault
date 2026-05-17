#!/usr/bin/env python3
"""Player scoring by week for a season.

Reads WEEKLY_PLAYER_SCORE canonical events. Useful for fact-checking
individual performance claims and streak/average assertions in recap drafts.

Usage:
  ./scripts/py scripts/audit_queries/player_scoring_by_week.py \\
      --season 2025 --player "Justin Jefferson" --league-id 70985

  --player accepts a partial name match (case-insensitive).

Optional:
  --franchise NAME   Filter to a specific franchise (partial match)
  --week N           Show only a specific week
  --db PATH          Database path (default: .local_squadvault.sqlite)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = "70985"


def _player_name_map(con: sqlite3.Connection, league_id: str, season: int) -> dict[str, str]:
    rows = con.execute(
        "SELECT player_id, name FROM player_directory WHERE league_id=? AND season=?",
        (league_id, season),
    ).fetchall()
    result: dict[str, str] = {}
    for r in rows:
        pid, raw = str(r[0]), str(r[1] or "")
        if ", " in raw:
            parts = raw.split(", ", 1)
            result[pid] = f"{parts[1]} {parts[0]}"
        else:
            result[pid] = raw
    return result


def _franchise_name_map(con: sqlite3.Connection, league_id: str, season: int) -> dict[str, str]:
    rows = con.execute(
        "SELECT franchise_id, name FROM franchises WHERE league_id=? AND season=?",
        (league_id, season),
    ).fetchall()
    return {str(r[0]): str(r[1]) for r in rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    ap.add_argument("--player", default=None, help="Player name (partial match).")
    ap.add_argument("--player-id", default=None, dest="player_id", help="Exact player ID.")
    ap.add_argument("--franchise", default=None, help="Franchise name (partial match).")
    ap.add_argument("--week", type=int, default=None, help="Filter to one week.")
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args(argv)

    if not args.player and not args.player_id:
        print("ERROR: provide --player NAME or --player-id ID", file=sys.stderr)
        return 2

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    pname_map = _player_name_map(con, str(args.league_id), args.season)
    fname_map = _franchise_name_map(con, str(args.league_id), args.season)

    # Resolve target player IDs
    if args.player_id:
        target_pids: set[str] = {args.player_id}
    else:
        query = args.player.lower()
        target_pids = {
            pid for pid, name in pname_map.items()
            if query in name.lower()
        }
        if not target_pids:
            print(f"No players found matching '{args.player}' in season {args.season}.")
            con.close()
            return 0

    # Load WEEKLY_PLAYER_SCORE events
    sql = """SELECT payload_json FROM v_canonical_best_events
             WHERE league_id=? AND season=? AND event_type='WEEKLY_PLAYER_SCORE'"""
    params: list = [str(args.league_id), args.season]
    rows = con.execute(sql, params).fetchall()
    con.close()

    hits: list[dict] = []
    for row in rows:
        try:
            p = json.loads(row["payload_json"])
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        pid = str(p.get("player_id") or "").strip()
        if pid not in target_pids:
            continue

        week = int(p.get("week", 0))
        if args.week and week != args.week:
            continue

        fid = str(p.get("franchise_id") or p.get("team_id") or "").strip()
        fname = fname_map.get(fid, fid)
        if args.franchise and args.franchise.lower() not in fname.lower():
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0

        slot = str(p.get("slot") or p.get("starting_status") or "")

        hits.append({
            "player_id": pid,
            "player_name": pname_map.get(pid, pid),
            "week": week,
            "score": score,
            "franchise_id": fid,
            "franchise_name": fname,
            "slot": slot,
        })

    hits.sort(key=lambda h: (h["player_id"], h["week"]))

    print(f"\nPlayer scoring -- League {args.league_id} -- Season {args.season}")
    print("=" * 60)

    if not hits:
        print("  No matching player score records found.")
        print()
        return 0

    current_player = None
    for h in hits:
        pid = h["player_id"]
        if pid != current_player:
            current_player = pid
            scores = [x["score"] for x in hits if x["player_id"] == pid]
            avg = sum(scores) / len(scores)
            print(f"\n  {h['player_name']} (id={pid})")
            print(f"  {len(scores)} week(s)  avg {avg:.2f}  "
                  f"min {min(scores):.2f}  max {max(scores):.2f}")
            print(f"  {'Wk':>3}  {'Score':>8}  {'Slot':>6}  Franchise")
            print(f"  {'--':>3}  {'-----':>8}  {'----':>6}  {'---'}")
        slot_str = h["slot"][:6] if h["slot"] else ""
        print(
            f"  {h['week']:>3}  {h['score']:>8.2f}  "
            f"{slot_str:>6}  {h['franchise_name']}"
        )

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
