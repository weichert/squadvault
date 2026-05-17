#!/usr/bin/env python3
"""Cumulative FAAB spend by franchise for a season.

Reads WAIVER_BID_AWARDED canonical events and sums bid amounts per franchise.
Useful for verifying dollar figures in recaps before approval.

Usage:
  ./scripts/py scripts/audit_queries/faab_spend_by_franchise.py \\
      --season 2025 --league-id 70985

Optional:
  --week-through N   Include only bids through week N (default: all)
  --db PATH          Database path (default: .local_squadvault.sqlite)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID = "70985"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    ap.add_argument("--week-through", type=int, default=None, dest="week_through")
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args(argv)

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    # Load franchise display names
    name_rows = con.execute(
        "SELECT franchise_id, name FROM franchises WHERE league_id=? AND season=?",
        (str(args.league_id), args.season),
    ).fetchall()
    name_map: dict[str, str] = {r["franchise_id"]: r["name"] for r in name_rows}

    # Load WAIVER_BID_AWARDED events
    rows = con.execute(
        """SELECT payload_json, occurred_at
           FROM v_canonical_best_events
           WHERE league_id=? AND season=?
             AND event_type='WAIVER_BID_AWARDED'
           ORDER BY occurred_at ASC NULLS LAST""",
        (str(args.league_id), args.season),
    ).fetchall()
    con.close()

    # Aggregate
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    bids_by_franchise: dict[str, list[tuple[str, str, float]]] = {}

    for row in rows:
        try:
            p = json.loads(row["payload_json"])
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        fid = str(p.get("franchise_id") or p.get("team_id") or "").strip()
        if not fid:
            continue

        pid = str(p.get("player_id") or "").strip()
        bid = p.get("bid_amount") or p.get("bid") or p.get("amount")
        if bid is None:
            continue
        try:
            bid_val = float(bid)
        except (ValueError, TypeError):
            continue
        if bid_val <= 0:
            continue

        # Optional: filter by occurred_at week if --week-through given
        # (week filtering not available without matchup data; skip for now)

        totals[fid] = totals.get(fid, 0.0) + bid_val
        counts[fid] = counts.get(fid, 0) + 1
        bids_by_franchise.setdefault(fid, []).append((
            pid, str(row["occurred_at"] or ""), bid_val,
        ))

    if not totals:
        print(f"No WAIVER_BID_AWARDED records for league {args.league_id} season {args.season}.")
        return 0

    print(f"\nFAAB spend — League {args.league_id} — Season {args.season}")
    print("=" * 60)

    sorted_fids = sorted(totals.keys(), key=lambda f: -totals[f])
    for fid in sorted_fids:
        fname = name_map.get(fid, fid)
        total = totals[fid]
        n = counts[fid]
        print(f"\n  {fname} ({fid}): ${total:.2f} total — {n} acquisition(s)")
        for pid, occurred_at, bid_val in sorted(
            bids_by_franchise[fid], key=lambda t: -t[2]
        ):
            date_str = occurred_at[:10] if occurred_at else "?"
            print(f"    player {pid:>10}   ${bid_val:>7.2f}   {date_str}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
