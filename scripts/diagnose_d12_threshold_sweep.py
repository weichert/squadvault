#!/usr/bin/env python3
"""Sweep D12 PLAYER_VS_OPPONENT detector parameters to find a tuning sweet spot.

The current detector requires a player to have scored >= 30 points in ALL of
their >= 3 prior career meetings against the same opponent (while on the same
franchise). This is extremely strict — across both 2024 and 2025 production
seasons, the detector fires once total.

This script sweeps four threshold values, two min-meeting counts, and two
match modes ("all meetings" vs ">= 75% of meetings") and reports per-combination
firing counts. Read-only: no DB writes, no LLM calls, no external API contact.

Usage::

    ./scripts/py -u scripts/diagnose_d12_threshold_sweep.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025

    # Show sample headlines per combination:
    ./scripts/py -u scripts/diagnose_d12_threshold_sweep.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025 \\
        --samples 2

The output is a parameter grid suitable for picking a target tuning. The
governing question: at what point does PLAYER_VS_OPPONENT fire often enough
to add narrative value without becoming noise?

This is a diagnostic only. No changes to the detector are made.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from dataclasses import dataclass

from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
)
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    _CrossSeasonRecord,
    _load_all_matchup_opponents,
    _load_all_seasons_player_scores,
)
from squadvault.core.resolvers import build_player_name_map
from squadvault.core.storage.session import DatabaseSession

# Sweep grid
THRESHOLDS = [15.0, 20.0, 25.0, 30.0]
MIN_MEETINGS = [2, 3]
MATCH_MODES = ["all", "75pct"]


@dataclass(frozen=True)
class _SweepHit:
    """One PLAYER_VS_OPPONENT angle that would have fired under given params."""
    season: int
    week: int
    franchise_id: str
    player_id: str
    opponent_id: str
    this_week_score: float
    prior_scores: tuple[float, ...]


def _detect_pvo_parametric(
    all_records: list[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    opponent_index: dict[tuple[int, int, str], str],
    *,
    threshold: float,
    min_meetings: int,
    match_mode: str,
) -> list[_SweepHit]:
    """Parametric reimplementation of detect_player_vs_opponent.

    match_mode:
      - "all":   require ALL prior meetings to be >= threshold (current behavior)
      - "75pct": require >= 75% of prior meetings to be >= threshold
    """
    this_week = [
        r for r in all_records
        if r.season == current_season and r.week == target_week and r.is_starter
    ]
    if not this_week:
        return []

    hits: list[_SweepHit] = []

    for r in sorted(this_week, key=lambda x: (x.franchise_id, x.player_id)):
        opponent_id = opponent_index.get((current_season, target_week, r.franchise_id))
        if not opponent_id:
            continue

        prior_scores: list[float] = []
        for hr in all_records:
            if hr.player_id != r.player_id or hr.franchise_id != r.franchise_id:
                continue
            if hr.season == current_season and hr.week >= target_week:
                continue
            opp = opponent_index.get((hr.season, hr.week, hr.franchise_id))
            if opp == opponent_id and hr.is_starter:
                prior_scores.append(hr.score)

        if len(prior_scores) < min_meetings:
            continue

        above = sum(1 for s in prior_scores if s >= threshold)

        if match_mode == "all":
            qualifies = above == len(prior_scores)
        elif match_mode == "75pct":
            qualifies = above / len(prior_scores) >= 0.75 and above >= min_meetings
        else:
            raise ValueError(f"Unknown match_mode: {match_mode}")

        if qualifies:
            hits.append(_SweepHit(
                season=current_season,
                week=target_week,
                franchise_id=r.franchise_id,
                player_id=r.player_id,
                opponent_id=opponent_id,
                this_week_score=r.score,
                prior_scores=tuple(prior_scores),
            ))

    return hits


def _discover_max_week(db_path: str, league_id: str, season: int) -> int:
    """Highest week index with WEEKLY_MATCHUP_RESULT data."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT MAX(CAST(json_extract(payload_json, '$.week') AS INTEGER))
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'""",
            (league_id, season),
        ).fetchone()
    return int(row[0]) if row and row[0] else 0


def _format_hit(
    hit: _SweepHit,
    pname: dict[str, str] | None,
    fname: dict[str, str] | None,
) -> str:
    p = pname.get(hit.player_id, hit.player_id) if pname else hit.player_id
    f = fname.get(hit.franchise_id, hit.franchise_id) if fname else hit.franchise_id
    o = fname.get(hit.opponent_id, hit.opponent_id) if fname else hit.opponent_id
    n = len(hit.prior_scores)
    above_count = sum(1 for s in hit.prior_scores if s >= 15.0)
    avg = sum(hit.prior_scores) / n
    return (
        f"  S{hit.season} W{hit.week:>2}  {p:30s}  {f:25s} vs {o:25s}  "
        f"this: {hit.this_week_score:5.2f}  prior n={n} avg={avg:5.2f} "
        f"({above_count}/{n} above 15.0)"
    )


def _run_sweep(
    db_path: str,
    league_id: str,
    seasons: list[int],
    samples: int,
) -> None:
    print(f"Loading all-seasons player scores for league {league_id}...")
    all_records = _load_all_seasons_player_scores(db_path, league_id)
    print(f"  Loaded {len(all_records):,} WEEKLY_PLAYER_SCORE records")

    print(f"Loading matchup opponent index for league {league_id}...")
    opponent_index = _load_all_matchup_opponents(db_path, league_id)
    print(f"  Loaded {len(opponent_index):,} (season, week, franchise) -> opponent entries")

    # Resolvers — for sample output readability
    pname: dict[str, str] = {}
    fname: dict[str, str] = {}
    try:
        pname = build_player_name_map(db_path, league_id)
    except Exception as e:
        print(f"  (player name map unavailable: {e})")
    try:
        fname = build_cross_season_name_resolver(db_path, league_id)
    except Exception as e:
        print(f"  (franchise name resolver unavailable: {e})")

    # Sweep
    # results[(threshold, min_meetings, match_mode)] -> list of hits
    results: dict[tuple[float, int, str], list[_SweepHit]] = defaultdict(list)

    for season in seasons:
        max_week = _discover_max_week(db_path, league_id, season)
        if max_week == 0:
            print(f"\n[season {season}] no matchup data — skipping")
            continue
        print(f"\n[season {season}] scanning weeks 1..{max_week}")
        for week in range(1, max_week + 1):
            for threshold in THRESHOLDS:
                for min_n in MIN_MEETINGS:
                    for mode in MATCH_MODES:
                        hits = _detect_pvo_parametric(
                            all_records,
                            current_season=season,
                            target_week=week,
                            opponent_index=opponent_index,
                            threshold=threshold,
                            min_meetings=min_n,
                            match_mode=mode,
                        )
                        results[(threshold, min_n, mode)].extend(hits)

    # Report
    print("\n" + "=" * 78)
    print("D12 PLAYER_VS_OPPONENT — parameter sweep results")
    print("=" * 78)
    print(f"\nSeasons scanned: {seasons}")
    print(f"Total weeks:     {sum(_discover_max_week(db_path, league_id, s) for s in seasons)}")
    print()
    print(f"{'threshold':>10}  {'min_meet':>8}  {'mode':>6}  {'fires':>6}  {'unique_players':>15}")
    print("-" * 60)

    # Sort: threshold asc, min_meetings asc, mode (all before 75pct)
    sorted_keys = sorted(
        results.keys(),
        key=lambda k: (k[0], k[1], 0 if k[2] == "all" else 1),
    )
    for key in sorted_keys:
        threshold, min_n, mode = key
        hits = results[key]
        unique_players = len({(h.player_id, h.franchise_id) for h in hits})
        print(
            f"{threshold:>10.1f}  {min_n:>8d}  {mode:>6s}  "
            f"{len(hits):>6d}  {unique_players:>15d}"
        )

    # Sample output
    if samples > 0:
        print("\n" + "=" * 78)
        print(f"Sample hits (up to {samples} per combination, only combinations with hits)")
        print("=" * 78)
        for key in sorted_keys:
            hits = results[key]
            if not hits:
                continue
            threshold, min_n, mode = key
            print(f"\n--- threshold={threshold} min_meetings={min_n} mode={mode} ---")
            for hit in hits[:samples]:
                print(_format_hit(hit, pname, fname))


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Path to SQLite DB")
    parser.add_argument("--league-id", required=True, help="League ID (canonical)")
    parser.add_argument(
        "--season", type=int, action="append", required=True,
        help="Season to scan (repeatable)",
    )
    parser.add_argument(
        "--samples", type=int, default=0,
        help="Sample headlines to print per combination (default 0 = none)",
    )
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"ERROR: db not found: {args.db}", file=sys.stderr)
        return 2

    _run_sweep(
        db_path=args.db,
        league_id=args.league_id,
        seasons=sorted(set(args.season)),
        samples=args.samples,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
