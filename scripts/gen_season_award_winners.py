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
from squadvault.core.storage.session import DatabaseSession

# Wave B1: 4/12/33 (matchup-derived). Wave B2 sub-wave 1: 3 (margin) + 6/7/9 (optimal-lineup).
AWARDS = ("4", "12", "33", "3", "6", "7", "9")


def _champ_week(season: int) -> int:
    """This league's championship-game week (the final round of the playoff bracket).

    Bracket narrows 10 -> 8 (wk15) -> 4 (wk16) -> 2 (the final). For 16-week NFL seasons
    the final is week 16; for the 18-week seasons (2021+) it is week 17. MFL also reports
    the decided final again at week 18 (a trailing/padding week for leagues that run that
    long - ours does not); that week-18 copy is de-duplicated in build_awards. So the
    championship is 16 (<=2020) or 17 (2021+), NEVER 18 for this league.
    """
    return 16 if season <= 2020 else 17


def _load_season_lineups(
    db_path: str, league_id: str, season: int
) -> list[dict[str, Any]]:
    """Generator-local loader for the Group A/B (lineup) awards (engine-core untouched).

    Loads WEEKLY_PLAYER_SCORE for one season and returns a flat list of per-player-week
    records. Mirrors the canonical query in player_week_context_v1 (which exposes only
    is_starter, not should_start, so it cannot drive these awards directly).

    Each record: {week, franchise_id, player_id, score, is_starter, opt, raw_ok}.
    The A1 optimal-indicator gate (raw `shouldStart` parseable in {'0','1'}) is captured
    as `raw_ok`; the optimal-lineup indicator is `opt` (raw `shouldStart == '1'`). A row
    failing the gate (raw_ok False) participates in neither numerator nor denominator of
    the Group A computations. Coverage is 100% across all 16 seasons, so raw_ok excludes
    ~0 rows, but the gate is honored explicitly.
    """
    recs: list[dict[str, Any]] = []
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
               ORDER BY payload_json ASC""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue
        franchise_id = str(p.get("franchise_id", "")).strip()
        player_id = str(p.get("player_id", "")).strip()
        if not franchise_id or not player_id:
            continue
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week < 0:
            continue
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0
        is_starter = bool(p.get("is_starter", False))
        # A1 gate: parse the raw MFL shouldStart (the real indicator; the should_start
        # boolean is False both for MFL-no and MFL-omitted, so we read the raw).
        raw_ss: str | None = None
        rmj = p.get("raw_mfl_json")
        if isinstance(rmj, str):
            try:
                raw_ss_val = json.loads(rmj).get("shouldStart")
                raw_ss = str(raw_ss_val) if raw_ss_val is not None else None
            except (ValueError, TypeError, AttributeError):
                raw_ss = None
        raw_ok = raw_ss in ("0", "1")
        recs.append({
            "week": week, "franchise_id": franchise_id, "player_id": player_id,
            "score": score, "is_starter": is_starter,
            "opt": raw_ss == "1", "raw_ok": raw_ok,
        })
    return recs


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
                # Canonical serves a single final per season (the wk18 phantom is collapsed by R1).
                f = finals[0]
                margin = f.winner_score - f.loser_score
                if margin < 2:
                    out.append({
                        "award_id": "33", "season": s, "franchise_id": f.winner_id,
                        "value": round(margin, 2), "detail": {"runner_up": runner, "week": f.week},
                    })

        # ---- Wave B2 sub-wave 1: Group A (optimal-lineup) + Group B (margin) ----
        # Full-season scope (ratified): every WEEKLY_PLAYER_SCORE / matchup, playoffs included.
        # The 2021+ week-18 championship phantom is collapsed at the CANONICAL layer
        # (run_canonicalize R1, ratified 2026-06-23), so `sm` and `recs` read here are already
        # phantom-free. The former per-generator dedup is retired - the canonical truth is the
        # single source. The title shows its true week (17) because that is what canonical serves.
        recs = _load_season_lineups(db_path, league_id, s)

        franchises = sorted({r["franchise_id"] for r in recs})
        weeks_played = {
            fr: len({r["week"] for r in recs if r["franchise_id"] == fr}) for fr in franchises
        }

        # #6 The Benchwarmer - season gross points of benched optimal-starts (A1-gated).
        # Retrospective FACT only; no forward-looking lineup tooling (no-optimization, load-bearing).
        bench_pts: dict[str, float] = defaultdict(float)
        bench_rows: dict[str, list[tuple[float, int, str]]] = defaultdict(list)
        for r in recs:
            if r["raw_ok"] and r["opt"] and not r["is_starter"]:
                bench_pts[r["franchise_id"]] += r["score"]
                bench_rows[r["franchise_id"]].append((r["score"], r["week"], r["player_id"]))
        bench_val = {fr: round(v, 2) for fr, v in bench_pts.items()}
        if bench_val:
            top_bench = max(bench_val.values())
            if top_bench > 0:  # no degenerate zero-point Benchwarmer
                for fr in franchises:
                    if bench_val.get(fr) == top_bench:
                        left = sorted(bench_rows[fr], key=lambda t: (-t[0], t[1], t[2]))[:3]
                        out.append({
                            "award_id": "6", "season": s, "franchise_id": fr,
                            "value": top_bench,
                            "detail": {
                                "bench_points": top_bench,
                                "weeks": weeks_played[fr],
                                "top_left_on_bench": [
                                    {"week": w, "player_id": pid, "score": round(sc, 2)}
                                    for sc, w, pid in left
                                ],
                            },
                        })

        # #7 The Clairvoyant - season rate of optimal starts among actual starts (A1-gated).
        # C2: a retrospective rate over completed facts only - never a forecast.
        opt_starts: dict[str, int] = defaultdict(int)
        tot_starts: dict[str, int] = defaultdict(int)
        for r in recs:
            if r["is_starter"] and r["raw_ok"]:
                tot_starts[r["franchise_id"]] += 1
                if r["opt"]:
                    opt_starts[r["franchise_id"]] += 1
        rate_val = {
            fr: round(opt_starts[fr] / tot_starts[fr], 4) for fr in tot_starts if tot_starts[fr] > 0
        }
        if rate_val:
            top_rate = max(rate_val.values())
            for fr in franchises:
                if rate_val.get(fr) == top_rate:
                    out.append({
                        "award_id": "7", "season": s, "franchise_id": fr,
                        "value": top_rate,
                        "detail": {
                            "optimal_starts": opt_starts[fr],
                            "total_starts": tot_starts[fr],
                            "weeks": weeks_played[fr],
                        },
                    })

        # #9 The Oracle - weeks the franchise LOST but its optimal lineup would have WON.
        # C2: a retrospective counterfactual over completed games - never a forecast.
        opt_score: dict[tuple[str, int], float] = defaultdict(float)
        for r in recs:
            if r["raw_ok"] and r["opt"]:
                opt_score[(r["franchise_id"], r["week"])] += r["score"]
        oracle: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for m in sm:
            if m.is_tie:
                continue
            fr = m.loser_id  # strict loss (loser_score < winner_score) by construction
            opt_sc = opt_score.get((fr, m.week), 0.0)
            if opt_sc > m.winner_score:  # optimal beats opponent's ACTUAL score (strict; a tie is not a win)
                oracle[fr].append({
                    "week": m.week,
                    "actual_score": round(m.loser_score, 2),
                    "optimal_score": round(opt_sc, 2),
                    "opponent_score": round(m.winner_score, 2),
                    "opponent_franchise_id": m.winner_id,
                })
        oracle_cnt = {fr: len(v) for fr, v in oracle.items()}
        if oracle_cnt:
            top_or = max(oracle_cnt.values())
            if top_or > 0:
                for fr in sorted(oracle_cnt):
                    if oracle_cnt[fr] == top_or:
                        out.append({
                            "award_id": "9", "season": s, "franchise_id": fr,
                            "value": top_or,
                            "detail": {
                                "oracle_weeks": sorted(oracle[fr], key=lambda d: d["week"]),
                                "count": top_or,
                            },
                        })

        # #3 The Hammer - the started player most often decisive (score > the winning margin).
        # Started players only; wins only (a loss/tie has no winning margin).
        by_fw: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for r in recs:
            by_fw[(r["franchise_id"], r["week"])].append(r)
        ham_cnt: dict[tuple[str, str], int] = defaultdict(int)
        ham_weeks: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for m in sm:
            if m.is_tie:
                continue
            fr = m.winner_id
            margin = m.winner_score - m.loser_score
            for r in by_fw.get((fr, m.week), []):
                if r["is_starter"] and r["score"] > margin:
                    ham_key = (fr, r["player_id"])
                    ham_cnt[ham_key] += 1
                    ham_weeks[ham_key].append({
                        "week": m.week,
                        "player_score": round(r["score"], 2),
                        "margin": round(margin, 2),
                        "opponent_franchise_id": m.loser_id,
                    })
        if ham_cnt:
            top_h = max(ham_cnt.values())
            if top_h > 0:
                holders = sorted(k for k, c in ham_cnt.items() if c == top_h)  # (fid, pid)
                by_fr: dict[str, list[str]] = defaultdict(list)
                for fid, pid in holders:
                    by_fr[fid].append(pid)
                # The unique key is (award, season, franchise): emit one row per franchise.
                # Cross-franchise co-holders -> distinct rows; a (rare) same-franchise tie folds
                # the extra players into detail.co_player_ids so the unique constraint always holds.
                for fid in sorted(by_fr):
                    pids = sorted(by_fr[fid])
                    primary = pids[0]
                    detail: dict[str, Any] = {
                        "player_id": primary,
                        "decisive_weeks": top_h,
                        "weeks": sorted(ham_weeks[(fid, primary)], key=lambda d: d["week"]),
                    }
                    if len(pids) > 1:
                        detail["co_player_ids"] = pids[1:]
                    out.append({
                        "award_id": "3", "season": s, "franchise_id": fid,
                        "value": top_h, "detail": detail,
                    })

    out.sort(key=lambda d: (d["award_id"], d["season"], d["franchise_id"]))
    return out


def _sql_lit(s: str) -> str:
    """Single-quote a SQL string literal, doubling any embedded single quote."""
    return "'" + s.replace("'", "''") + "'"


def emit_seed(rows: list[dict[str, Any]], league: str) -> str:
    """Idempotent FK-safe seed for season_award_winners. Paste-safe: no semicolons in comments."""
    award_in = ", ".join(_sql_lit(a) for a in AWARDS)
    lines: list[str] = []
    lines.append("-- supabase/seed/004_season_award_winners.sql")
    lines.append("-- W.5 Inc 3 season awards. Wave B1: #4 The Cannon, #12 The Black Rose, #33 One-Point")
    lines.append("-- Club (matchup-derived). Wave B2 sub-wave 1: #3 The Hammer (margin), #6 The Benchwarmer,")
    lines.append("-- #7 The Clairvoyant, #9 The Oracle (optimal-lineup). Generated by")
    lines.append("-- scripts/gen_season_award_winners.py in the engine repo - do not hand-edit.")
    lines.append("-- Idempotent: DELETE these awards then INSERT. Provenance is per-award (CASE below).")
    lines.append("-- Franchise resolves by (league canonical_id, canonical code) - no hardcoded UUIDs.")
    lines.append("-- Prerequisite: migration 028 (season_award_winners) applied. Paste-safe (no in-comment semicolons).")
    lines.append("BEGIN;")
    lines.append(
        "DELETE FROM season_award_winners WHERE league_id = "
        f"(SELECT id FROM leagues WHERE canonical_id = {_sql_lit(league)}) "
        f"AND award_id IN ({award_in});"
    )
    lines.append("INSERT INTO season_award_winners (league_id, award_id, season, franchise_id, value, detail, provenance)")
    lines.append("SELECT l.id, v.award_id, v.season, v.franchise_id, v.value, v.detail::jsonb,")
    lines.append("  CASE")
    lines.append("    WHEN v.award_id IN ('4', '12', '33') THEN 'engine:matchup-derived'")
    lines.append("    WHEN v.award_id = '3' THEN 'engine:matchup-lineup-derived'")
    lines.append("    ELSE 'engine:lineup-derived'")
    lines.append("  END")
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
