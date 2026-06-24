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
  - W-L-T, points-for   (compute_all_season_records over the REGULAR-SEASON matchup set:
                         weeks before the championship final, _champ_week - excludes the title
                         game for both finalists, consistent with points_against and the verifier)
  - champion, runner-up (compute_championship_roll over the FULL matchup set)
  - points_against (REGULAR SEASON ONLY) + blowout_wins_60 (ALL DECIDED GAMES)
    (compute_extras; W.5 Inc 2 Wave 2 - Iron Curtain + Executioner)
No final rank / granular playoff finish: never ingested, not exactly derivable,
omitted per silence-over-speculation (this session's D4-1 decision).

W.5 Inc 2 Wave 2 (2026-06-22): two per-(franchise, season) facts off the same
HistoricalMatchup stream. points_against is REGULAR-SEASON-ONLY (weeks before the
championship week - W16 for 2010-2020, W18 for 2021+) for The Iron Curtain (best
all-time points-allowed average). blowout_wins_60 counts wins by 60+ over ALL decided
games (consistent with the probe that calibrated the 60 threshold) for The Executioner.
The regular-season GAME COUNT for the average is derived frontend-side from existing
columns (wins+losses+ties minus a championship appearance, result in CHAMPION/RUNNER_UP),
since exactly the two finalists play at week >= the championship week.

READ-ONLY on the engine DB. Tracked under scripts/ (was ~/sv-apply/, untracked).

USAGE (engine repo, $DB set, ./scripts/py shim provides PYTHONPATH=src):
  cd ~/projects/squadvault-ingest-fresh
  ./scripts/py scripts/gen_franchise_records.py --db "$DB" --league 70985 \
      --out scripts/franchise_records_70985.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    compute_all_season_records,
    compute_championship_roll,
)
from squadvault.core.recaps.context.league_history_v1 import load_all_matchups


def _champ_week(season: int) -> int:
    """The single championship-game week; weeks before it are the regular season.

    16 for 2010-2020; 17 for 2021+ (the bracket ends 10->8->4->2 at wk17; wk18 is MFL's
    trailing copy, collapsed at the canonical layer - see run_canonicalize R1). Gating
    regular-season points_against on `< _champ_week` therefore excludes the wk17 title.
    """
    return 16 if season <= 2020 else 17


def compute_extras(
    matchups: list[Any],
) -> tuple[dict[tuple[str, int], float], dict[tuple[str, int], int]]:
    """Per-(franchise, season): regular-season points-against + all-games blowout-60 wins.

    points_against is REGULAR SEASON ONLY (week < the championship week): for each such
    matchup, each participant is charged its opponent's score (ties included - both still
    allowed points). blowout_wins_60 is over ALL DECIDED games: a win by margin >= 60.
    """
    pa: dict[tuple[str, int], float] = defaultdict(float)
    bw: dict[tuple[str, int], int] = defaultdict(int)
    for m in matchups:
        if m.week < _champ_week(m.season):
            pa[(m.winner_id, m.season)] += m.loser_score
            pa[(m.loser_id, m.season)] += m.winner_score
        if not m.is_tie and m.margin >= 60:
            bw[(m.winner_id, m.season)] += 1
    return pa, bw


def build_records(db_path: str, league_id: str) -> list[dict[str, Any]]:
    matchups = load_all_matchups(db_path, league_id)
    if not matchups:
        return []
    # W-L / ties / points_for are REGULAR-SEASON (exclude the championship final), consistent
    # with points_against (compute_extras) and the recap verifier. Without this the final leaked
    # into the two finalists' W-L/PF each season (champion +1 win, runner-up +1 loss, both PF
    # inflated) - the defect this fix closes. compute_all_season_records is SHARED with the
    # hall-of-fame archive and is NOT modified; we filter its INPUT. The championship week is
    # _champ_week (16 for <=2020, 17 for 2021+; the wk18 phantom is already collapsed at the
    # canonical layer). compute_championship_roll stays on the FULL matchups - the title is
    # decided by the playoff games we filter out of the record.
    reg_matchups = [m for m in matchups if m.week < _champ_week(m.season)]
    records = compute_all_season_records(reg_matchups)
    roll = compute_championship_roll(matchups)
    champ_by_season = {r.season: r.champion_id for r in roll}
    runner_by_season = {r.season: r.runner_up_id for r in roll}
    pa, bw = compute_extras(matchups)

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
                "points_against": round(pa.get((r.franchise_id, r.season), 0.0), 2),
                "blowout_wins_60": bw.get((r.franchise_id, r.season), 0),
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
