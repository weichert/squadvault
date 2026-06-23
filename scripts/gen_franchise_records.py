#!/usr/bin/env python3
"""gen_franchise_records.py -- Engine-facts generator for the Member Office record board.

REVIEW MODE: reads the engine SQLite, computes per-(franchise, season) W-L-T +
points-for and the per-season champion/runner-up, joins them into a record-board
fact set, and emits (a) a JSON file and (b) a human-readable verification table.

It does NOT write Supabase or emit seed SQL yet. The engine->Supabase franchise-id
mapping must be confirmed first: the engine uses canonical franchise ids of the
form '0001'..'0010'; the only committed Supabase seed (demo) uses 'F01'..'F10'.
The production scheme must be verified before a seed can join correctly.

Facts are exact and derived only from ingested matchup results:
  - W-L-T, points-for   (compute_all_season_records)
  - champion, runner-up (compute_championship_roll)
No final rank / granular playoff finish: never ingested, not exactly derivable,
omitted per silence-over-speculation (this session's D4-1 decision).

READ-ONLY on the engine DB. Keep in ~/sv-apply/; run from outside the repo.

USAGE (engine repo, $DB set, ./scripts/py shim provides PYTHONPATH=src):
  cd ~/projects/squadvault-ingest-fresh
  ./scripts/py ~/sv-apply/gen_franchise_records.py --db "$DB" --league 70985 \
      --out ~/sv-apply/franchise_records_70985.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

from squadvault.core.recaps.context.league_history_v1 import load_all_matchups
from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    compute_all_season_records,
    compute_championship_roll,
)


def build_records(db_path: str, league_id: str) -> list[dict[str, Any]]:
    matchups = load_all_matchups(db_path, league_id)
    if not matchups:
        return []
    records = compute_all_season_records(matchups)
    roll = compute_championship_roll(matchups)
    champ_by_season = {r.season: r.champion_id for r in roll}
    runner_by_season = {r.season: r.runner_up_id for r in roll}

    out: list[dict[str, Any]] = []
    for r in records:
        if r.franchise_id == champ_by_season.get(r.season):
            result = "CHAMPION"
        elif r.franchise_id == runner_by_season.get(r.season):
            result = "RUNNER_UP"
        else:
            result = ""
        out.append(
            {
                "franchise_id": r.franchise_id,
                "season": r.season,
                "wins": r.wins,
                "losses": r.losses,
                "ties": r.ties,
                "points_for": r.points_for,
                "result": result,
            }
        )
    out.sort(key=lambda d: (d["franchise_id"], d["season"]))
    return out


def print_table(rows: list[dict[str, Any]]) -> None:
    by_f: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in rows:
        by_f[d["franchise_id"]].append(d)
    seasons = sorted({d["season"] for d in rows})
    print(
        f"\nfranchises={len(by_f)}  seasons={seasons[0]}-{seasons[-1]}  rows={len(rows)}\n"
    )
    print("  fid     seasons  all-time W-L-T   CH  RU")
    for fid in sorted(by_f):
        recs = by_f[fid]
        champs = sum(1 for d in recs if d["result"] == "CHAMPION")
        rus = sum(1 for d in recs if d["result"] == "RUNNER_UP")
        tw = sum(d["wins"] for d in recs)
        tl = sum(d["losses"] for d in recs)
        tt = sum(d["ties"] for d in recs)
        wlt = f"{tw}-{tl}-{tt}"
        print(f"  {fid:>6}  {len(recs):>7}  {wlt:>13}   {champs:>2}  {rus:>2}")

    rollmap: dict[int, dict[str, str]] = {}
    for d in rows:
        if d["result"] == "CHAMPION":
            rollmap.setdefault(d["season"], {})["c"] = d["franchise_id"]
        elif d["result"] == "RUNNER_UP":
            rollmap.setdefault(d["season"], {})["r"] = d["franchise_id"]
    print("\n  season  champion  runner_up")
    for s in sorted(rollmap):
        c = rollmap[s].get("c", "?")
        ru = rollmap[s].get("r", "?")
        print(f"  {s:>6}  {c:>8}  {ru:>9}")
    print(
        "\nEYEBALL CHECKS: confirm known facts (e.g. the 0-14 2025 team; the "
        "4-championship franchise) land on the right fid before any seed."
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Engine-facts generator for Member Office record board (review mode)."
    )
    ap.add_argument("--db", required=True, help="Path to engine SQLite ($DB)")
    ap.add_argument("--league", default="70985", help="Canonical league id (default 70985)")
    ap.add_argument("--out", default=None, help="Optional JSON output path")
    args = ap.parse_args(argv)

    rows = build_records(args.db, args.league)
    if not rows:
        print(
            f"No matchups found for league {args.league} in {args.db}",
            file=sys.stderr,
        )
        return 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(rows)} records to {args.out}")
    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
