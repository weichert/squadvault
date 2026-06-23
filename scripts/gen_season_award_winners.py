#!/usr/bin/env python3
"""gen_season_award_winners.py -- Engine-facts generator for the Trophy Room season awards.

W.5 Increment 3 Wave B1. Computes the three weekly-score-derived per-season awards off the
same completed-matchup stream the inc-2 Wave 2 generator used (HistoricalMatchup:
winner_score / loser_score / margin per matchup), and emits (a) a JSON fact set and (b) an
idempotent seed for the new season_award_winners table.

The three awards (spec engine OBSERVATIONS_2026_06_23_W5_INC3_SPECIFICATION.md section 4.2):
  - #4  The Cannon       - per season, the highest single-week franchise score. The frontend
                           reads the all-time max; per-season rows give a chronological drill-in.
  - #12 The Black Rose   - per season, the highest LOSING score (scored huge and still lost).
                           Tone-care (SHAME_RECORD): the fact is the fact, rendered plainly.
  - #33 One-Point Club   - the WINNER of any championship game decided by margin < 2. Founder
                           ruling (2026-06-23): membership is the winner only, not both finalists.
                           One row per qualifying season (none if the final was not close).

Co-holders on tie are emitted as multiple rows (C6); the natural key
(award_id, season, franchise_id) admits them. Franchise ids are the engine canonical codes
('0001'..'0010'); the seed resolves the league by canonical_id and stores the canonical code
as text (season_award_winners.franchise_id is text, not a UUID FK - no hardcoded UUIDs).

READ-ONLY on the engine DB. Born tracked under scripts/ (the inc-2 generators initially lived
untracked in ~/sv-apply/; that provenance gap is the lesson).

USAGE (engine repo, $DB set, ./scripts/py shim provides PYTHONPATH=src):
  cd ~/projects/squadvault-ingest-fresh
  ./scripts/py scripts/gen_season_award_winners.py --db "$DB" --league 70985 \
      --out scripts/season_award_winners_70985.json
  ./scripts/py scripts/gen_season_award_winners.py --db "$DB" --league 70985 \
      --seed ../squadvault/supabase/seed/004_season_award_winners.sql
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    compute_championship_roll,
)
from squadvault.core.recaps.context.league_history_v1 import load_all_matchups

AWARDS = ("4", "12", "33")


def _champ_week(season: int) -> int:
    """The single championship-game week; weeks before it are the regular season."""
    return 16 if season <= 2020 else 18


def build_awards(db_path: str, league_id: str) -> list[dict[str, Any]]:
    matchups = load_all_matchups(db_path, league_id)
    if not matchups:
        return []
    roll = compute_championship_roll(matchups)
    champ_by_season = {r.season: (r.champion_id, r.runner_up_id) for r in roll}
    seasons = sorted({m.season for m in matchups})
    out: list[dict[str, Any]] = []

    for s in seasons:
        sm = [m for m in matchups if m.season == s]

        # #4 The Cannon - highest single-week score by any franchise this season (co-holders on tie).
        sides = []  # (score, fid, week, opponent)
        for m in sm:
            sides.append((m.winner_score, m.winner_id, m.week, m.loser_id))
            sides.append((m.loser_score, m.loser_id, m.week, m.winner_id))
        top = max(x[0] for x in sides)
        for score, fid, week, opp in sides:
            if score == top:
                out.append({
                    "award_id": "4", "season": s, "franchise_id": fid,
                    "value": round(score, 2), "detail": {"week": week, "opponent": opp},
                })

        # #12 The Black Rose - highest LOSING score this season (non-tie; co-holders on tie).
        losers = [(m.loser_score, m.loser_id, m.week, m.winner_id) for m in sm if not m.is_tie]
        if losers:
            topl = max(x[0] for x in losers)
            for score, fid, week, opp in losers:
                if score == topl:
                    out.append({
                        "award_id": "12", "season": s, "franchise_id": fid,
                        "value": round(score, 2), "detail": {"week": week, "opponent": opp},
                    })

        # #33 One-Point Club - winner of a championship decided by margin < 2 (winner only).
        champ, runner = champ_by_season.get(s, (None, None))
        if champ:
            finals = [m for m in sm if m.week >= _champ_week(s) and {m.winner_id, m.loser_id} == {champ, runner}]
            if finals:
                f = finals[0]
                margin = f.winner_score - f.loser_score
                if margin < 2:
                    out.append({
                        "award_id": "33", "season": s, "franchise_id": f.winner_id,
                        "value": round(margin, 2), "detail": {"runner_up": runner, "week": f.week},
                    })

    out.sort(key=lambda d: (d["award_id"], d["season"], d["franchise_id"]))
    return out


def _sql_lit(s: str) -> str:
    """Single-quote a SQL string literal, doubling any embedded single quote."""
    return "'" + s.replace("'", "''") + "'"


def emit_seed(rows: list[dict[str, Any]], league: str) -> str:
    """Idempotent FK-safe seed for season_award_winners. Paste-safe: no semicolons in comments."""
    lines: list[str] = []
    lines.append("-- supabase/seed/004_season_award_winners.sql")
    lines.append("-- W.5 Inc 3 Wave B1 - the three weekly-score-derived season awards (#4 The Cannon,")
    lines.append("-- #12 The Black Rose, #33 One-Point Club). Generated by scripts/gen_season_award_winners.py")
    lines.append("-- in the engine repo - do not hand-edit. Idempotent: DELETE these awards then INSERT.")
    lines.append("-- Franchise resolves by (league canonical_id, canonical code) - no hardcoded UUIDs.")
    lines.append("-- Prerequisite: migration 028 (season_award_winners) applied. Paste-safe (no in-comment semicolons).")
    lines.append("BEGIN;")
    lines.append(
        "DELETE FROM season_award_winners WHERE league_id = "
        f"(SELECT id FROM leagues WHERE canonical_id = {_sql_lit(league)}) "
        "AND award_id IN ('4', '12', '33');"
    )
    lines.append("INSERT INTO season_award_winners (league_id, award_id, season, franchise_id, value, detail, provenance)")
    lines.append("SELECT l.id, v.award_id, v.season, v.franchise_id, v.value, v.detail::jsonb, 'engine:matchup-derived'")
    lines.append("FROM (VALUES")
    vals = []
    for r in rows:
        detail = json.dumps(r["detail"], ensure_ascii=False, sort_keys=True)
        vals.append(
            f"  ({_sql_lit(r['award_id'])}, {r['season']}, {_sql_lit(r['franchise_id'])}, "
            f"{r['value']}, {_sql_lit(detail)})"
        )
    lines.append(",\n".join(vals))
    lines.append(") AS v(award_id, season, franchise_id, value, detail)")
    lines.append(f"JOIN leagues l ON l.canonical_id = {_sql_lit(league)};")
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def print_table(rows: list[dict[str, Any]]) -> None:
    by_award: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in rows:
        by_award[d["award_id"]].append(d)
    print(f"\nrows={len(rows)}  awards={sorted(by_award)}\n")
    # All-time reads (what the frontend computes).
    cannon = max(by_award.get("4", []), key=lambda d: d["value"], default=None)
    rose = max(by_award.get("12", []), key=lambda d: d["value"], default=None)
    if cannon:
        top = [d for d in by_award["4"] if d["value"] == cannon["value"]]
        print(f"  #4  The Cannon (all-time): {cannon['value']} -> {[d['franchise_id'] + ' ' + str(d['season']) for d in top]}")
    if rose:
        top = [d for d in by_award["12"] if d["value"] == rose["value"]]
        print(f"  #12 The Black Rose (all-time): {rose['value']} -> {[d['franchise_id'] + ' ' + str(d['season']) for d in top]}")
    club = by_award.get("33", [])
    print(f"  #33 One-Point Club: {[(d['season'], d['franchise_id'], d['value']) for d in club]}")
    print("\n  award  season  franchise  value   detail")
    for d in rows:
        print(f"  {d['award_id']:>5}  {d['season']:>6}  {d['franchise_id']:>9}  {d['value']:>6}   {d['detail']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Season-award-winners generator (W.5 Inc 3 Wave B1).")
    ap.add_argument("--db", required=True, help="Path to engine SQLite ($DB)")
    ap.add_argument("--league", default="70985", help="Canonical league id (default 70985)")
    ap.add_argument("--out", default=None, help="Optional JSON output path")
    ap.add_argument("--seed", default=None, help="Optional seed SQL output path (004_season_award_winners.sql)")
    args = ap.parse_args(argv)

    rows = build_awards(args.db, args.league)
    if not rows:
        print(f"No matchups found for league {args.league} in {args.db}", file=sys.stderr)
        return 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(rows)} award rows to {args.out}")
    if args.seed:
        with open(args.seed, "w", encoding="utf-8") as f:
            f.write(emit_seed(rows, args.league))
        print(f"Wrote seed ({len(rows)} rows) to {args.seed}")
    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
