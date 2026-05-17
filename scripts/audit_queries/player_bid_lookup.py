#!/usr/bin/env python3
"""Look up the canonical FAAB bid amount for a specific player.

Cross-references WAIVER_BID_AWARDED events against the player directory.
Use this to fact-check dollar amounts in recap drafts before approving.

Usage:
  ./scripts/py scripts/audit_queries/player_bid_lookup.py \\
      --season 2025 --player "Brian Thomas" --league-id 70985

  --player accepts a partial name match (case-insensitive).

  ./scripts/py scripts/audit_queries/player_bid_lookup.py \\
      --season 2025 --player-id 12345 --league-id 70985

Optional:
  --franchise NAME   Filter to a specific franchise name (partial match)
  --db PATH          Database path (default: .local_squadvault.sqlite)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = "70985"


def _resolve_player_ids(con: sqlite3.Connection, season: int, league_id: str,
                         name_query: str) -> dict[str, str]:
    """Return {player_id: display_name} for players matching name_query."""
    rows = con.execute(
        """SELECT player_id, name FROM player_directory
           WHERE league_id=? AND season=?""",
        (league_id, season),
    ).fetchall()
    query = name_query.lower()
    matches: dict[str, str] = {}
    for row in rows:
        pid, raw = str(row[0]), str(row[1] or "")
        # Convert "Last, First" to "First Last" for matching
        if ", " in raw:
            parts = raw.split(", ", 1)
            display = f"{parts[1]} {parts[0]}"
        else:
            display = raw
        if query in display.lower() or query in raw.lower():
            matches[pid] = display
    return matches


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    ap.add_argument("--player", default=None, help="Player name (partial match).")
    ap.add_argument("--player-id", default=None, dest="player_id", help="Exact player ID.")
    ap.add_argument("--franchise", default=None, help="Franchise name (partial match).")
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args(argv)

    if not args.player and not args.player_id:
        print("ERROR: provide --player NAME or --player-id ID", file=sys.stderr)
        return 2

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    # Resolve player IDs
    if args.player_id:
        target_pids = {args.player_id: args.player_id}
    else:
        target_pids = _resolve_player_ids(con, args.season, args.league_id, args.player)
        if not target_pids:
            print(f"No players found matching '{args.player}' in season {args.season}.")
            con.close()
            return 0

    # Load franchise names
    name_rows = con.execute(
        "SELECT franchise_id, name FROM franchises WHERE league_id=? AND season=?",
        (str(args.league_id), args.season),
    ).fetchall()
    fname_map: dict[str, str] = {r["franchise_id"]: r["name"] for r in name_rows}

    # Load all WAIVER_BID_AWARDED events for the season
    rows = con.execute(
        """SELECT payload_json, occurred_at
           FROM v_canonical_best_events
           WHERE league_id=? AND season=?
             AND event_type='WAIVER_BID_AWARDED'
           ORDER BY occurred_at ASC NULLS LAST""",
        (str(args.league_id), args.season),
    ).fetchall()
    con.close()

    results: list[dict] = []
    for row in rows:
        try:
            p = json.loads(row["payload_json"])
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        pid = str(p.get("player_id") or "").strip()
        if not pid:
            added = p.get("players_added_ids")
            if isinstance(added, str):
                pid = added.split(",")[0].strip()
            elif isinstance(added, list) and added:
                pid = str(added[0]).strip()

        if pid not in target_pids:
            continue

        fid = str(p.get("franchise_id") or p.get("team_id") or "").strip()
        bid = p.get("bid_amount") or p.get("bid") or p.get("amount")
        try:
            bid_val = float(bid) if bid is not None else 0.0
        except (ValueError, TypeError):
            bid_val = 0.0

        # Franchise filter
        if args.franchise:
            fname = fname_map.get(fid, fid)
            if args.franchise.lower() not in fname.lower():
                continue

        results.append({
            "player_id": pid,
            "player_display": target_pids.get(pid, pid),
            "franchise_id": fid,
            "franchise_name": fname_map.get(fid, fid),
            "bid_amount": bid_val,
            "occurred_at": str(row["occurred_at"] or ""),
        })

    print(f"\nFAAB bid lookup — League {args.league_id} — Season {args.season}")
    print("=" * 60)

    if not results:
        print(f"  No WAIVER_BID_AWARDED records found for the specified player(s).")
        print()
        return 0

    for r in results:
        date_str = r["occurred_at"][:10] if r["occurred_at"] else "?"
        print(
            f"  {r['player_display']} (id={r['player_id']})"
            f"  —  ${r['bid_amount']:.2f}"
            f"  —  {r['franchise_name']} ({r['franchise_id']})"
            f"  —  {date_str}"
        )

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
