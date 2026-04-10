#!/usr/bin/env python3
"""Diagnose SCORING_MOMENTUM_IN_STREAK gate tightness against production data.

The detector ``detect_scoring_momentum_in_streak`` fires when a franchise's
current active win streak (length ≥4) has strictly monotonic margins — every
margin strictly greater than, or strictly less than, the one before it. In
PFL Buddies' 2024 and 2025 production data the detector fires zero times
across 36 weeks despite the league having plenty of win streaks.

This diagnostic answers two questions:

1. How many 4+ game active win streaks exist in each season, per franchise
   and per week? (i.e., what streaks does the detector actually evaluate?)
2. What shape are those streaks? How many are strictly monotonic, how many
   are one blip away from strictly monotonic, how many are flat or mixed?

The second question is the key one: if many streaks are one blip away from
strictly monotonic, a "directional trend with at most one deviation" gate
would unlock real production firings. If streaks are mostly mixed, the
current strict gate is a reasonable match for reality and zero firings is
the right answer.

This script is read-only. It does not modify the database, generate any
LLM output, or touch any external API.

Usage::

    ./scripts/py -u scripts/diagnose_streak_momentum_gate.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025

    # Show the full margin sequence of every 4+ streak observation:
    ./scripts/py -u scripts/diagnose_streak_momentum_gate.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025 --verbose
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    build_cross_season_name_resolver,
    load_all_matchups,
)

# ─────────────────────────────────────────────────────────────────────
# Classification
# ─────────────────────────────────────────────────────────────────────

# Kept in display order.
CLS_STRICTLY_GROWING = "strictly_growing"
CLS_STRICTLY_SHRINKING = "strictly_shrinking"
CLS_FLAT = "flat"
CLS_NEAR_GROWING = "near_growing_1blip"
CLS_NEAR_SHRINKING = "near_shrinking_1blip"
CLS_MIXED = "mixed"

CLASSIFICATION_ORDER = [
    CLS_STRICTLY_GROWING,
    CLS_STRICTLY_SHRINKING,
    CLS_FLAT,
    CLS_NEAR_GROWING,
    CLS_NEAR_SHRINKING,
    CLS_MIXED,
]


def classify_sequence(seq: tuple[float, ...]) -> str:
    """Classify a margin sequence into one of six shape categories.

    Precedence: strict-monotonic classifications take priority over near-
    monotonic classifications. Flat sequences are their own category. Only
    sequences of length ≥2 are meaningfully classified.
    """
    if len(seq) < 2:
        return CLS_MIXED

    if all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)):
        return CLS_STRICTLY_GROWING
    if all(seq[i] > seq[i + 1] for i in range(len(seq) - 1)):
        return CLS_STRICTLY_SHRINKING
    if all(m == seq[0] for m in seq):
        return CLS_FLAT

    # Near-monotonic: removing any one element yields a strictly-monotonic
    # sequence of length ≥2.
    for j in range(len(seq)):
        reduced = seq[:j] + seq[j + 1 :]
        if len(reduced) < 2:
            continue
        if all(reduced[i] < reduced[i + 1] for i in range(len(reduced) - 1)):
            return CLS_NEAR_GROWING
    for j in range(len(seq)):
        reduced = seq[:j] + seq[j + 1 :]
        if len(reduced) < 2:
            continue
        if all(reduced[i] > reduced[i + 1] for i in range(len(reduced) - 1)):
            return CLS_NEAR_SHRINKING

    return CLS_MIXED


# ─────────────────────────────────────────────────────────────────────
# Simulation — mirror the detector's per-week active-streak loop exactly
# ─────────────────────────────────────────────────────────────────────


def simulate_detector_observations(
    matchups: list[HistoricalMatchup],
    season: int,
) -> tuple[list[tuple[str, int, tuple[float, ...], str]], int]:
    """Walk the season week-by-week and return every observation the
    detector would make where active streak length ≥4.

    Each observation is ``(franchise_id, target_week, streak_margins, cls)``.
    Mirrors the detector code in ``detect_scoring_momentum_in_streak``
    exactly: for each franchise, for each target_week, walks backwards
    while winning and collects margins in chronological order.

    Returns ``(observations, max_week)``. ``max_week`` is the highest week
    number found in the season's non-tie matchups; 0 if no data.
    """
    # Build per-franchise per-week (won, margin) map for this season.
    fid_weekly: dict[str, dict[int, tuple[bool, float]]] = {}
    max_week = 0
    for m in matchups:
        if m.season != season or m.is_tie:
            continue
        if m.week > max_week:
            max_week = m.week
        for fid, won, margin in [
            (m.winner_id, True, m.margin),
            (m.loser_id, False, m.margin),
        ]:
            if fid not in fid_weekly:
                fid_weekly[fid] = {}
            fid_weekly[fid][m.week] = (won, margin)

    if max_week == 0:
        return [], 0

    observations: list[tuple[str, int, tuple[float, ...], str]] = []
    for target_week in range(1, max_week + 1):
        for fid in sorted(fid_weekly.keys()):
            weekly = fid_weekly[fid]
            streak_margins: list[float] = []
            wk = target_week
            while wk >= 1 and wk in weekly:
                won, margin = weekly[wk]
                if won:
                    streak_margins.insert(0, margin)
                    wk -= 1
                else:
                    break
            if len(streak_margins) >= 4:
                seq = tuple(streak_margins)
                cls = classify_sequence(seq)
                observations.append((fid, target_week, seq, cls))
    return observations, max_week


# ─────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────


def _format_margins(seq: tuple[float, ...]) -> str:
    """Render margins as a compact comma-separated list."""
    return ", ".join(f"{m:.1f}" for m in seq)


_CLASSIFICATION_LABELS = {
    CLS_STRICTLY_GROWING: "STRICTLY GROWING (detector fires)",
    CLS_STRICTLY_SHRINKING: "STRICTLY SHRINKING (detector fires)",
    CLS_FLAT: "FLAT (equal margins)",
    CLS_NEAR_GROWING: "NEAR GROWING (1 blip from strictly growing)",
    CLS_NEAR_SHRINKING: "NEAR SHRINKING (1 blip from strictly shrinking)",
    CLS_MIXED: "MIXED (no clear direction)",
}


def report_season(
    *,
    matchups: list[HistoricalMatchup],
    season: int,
    name_map: dict[str, str],
    verbose: bool,
) -> bool:
    """Report win-streak diagnostics for one season.

    Returns True if the season had any matchup data, False otherwise.
    """
    print(f"\n{'=' * 78}")
    print(f"  SCORING_MOMENTUM_IN_STREAK GATE DIAGNOSTIC — Season {season}")
    print(f"{'=' * 78}")

    observations, max_week = simulate_detector_observations(matchups, season)

    if max_week == 0:
        print(f"\n  No matchup data found for season {season}.")
        return False

    print(f"\n  Weeks scanned:                        {max_week}")
    print(f"  Total ≥4-game active-streak observations: {len(observations)}")

    if not observations:
        print("\n  No franchise reached a 4+ game active win streak in this season.")
        print("  The detector's gate is unreachable — no streaks to classify.")
        return True

    # Classification distribution
    cls_counts: Counter[str] = Counter(o[3] for o in observations)
    fires = cls_counts[CLS_STRICTLY_GROWING] + cls_counts[CLS_STRICTLY_SHRINKING]

    print(f"\n  Detector would fire on {fires} of {len(observations)} observations "
          f"({(fires / len(observations) * 100):.1f}%)")
    print("\n  Classification breakdown:")
    print(f"    {'Shape':<50s} {'Count':>7s} {'Share':>7s}")
    print(f"    {'─' * 50} {'─' * 7} {'─' * 7}")
    for cls in CLASSIFICATION_ORDER:
        count = cls_counts[cls]
        share = (count / len(observations) * 100) if observations else 0.0
        label = _CLASSIFICATION_LABELS[cls]
        print(f"    {label:<50s} {count:>7d} {share:>6.1f}%")

    # Gate-relaxation what-if: how many would fire under "strictly monotonic
    # OR near-monotonic (1 blip allowed)"?
    near_count = cls_counts[CLS_NEAR_GROWING] + cls_counts[CLS_NEAR_SHRINKING]
    relaxed_fires = fires + near_count
    print()
    print("  Gate-relaxation what-if:")
    print(f"    Current gate (strict monotonic):       {fires} fires "
          f"({(fires / len(observations) * 100):.1f}%)")
    print(f"    Relaxed (strict OR near-monotonic):    {relaxed_fires} fires "
          f"({(relaxed_fires / len(observations) * 100):.1f}%)")

    # Max streak length reached by each franchise
    max_len_per_franchise: dict[str, int] = {}
    for fid, _tw, seq, _cls in observations:
        if len(seq) > max_len_per_franchise.get(fid, 0):
            max_len_per_franchise[fid] = len(seq)

    if max_len_per_franchise:
        print()
        print("  Longest active streak reached this season (≥4 only):")
        for fid in sorted(max_len_per_franchise.keys()):
            name = name_map.get(fid, fid)
            print(f"    {name:<40s} {max_len_per_franchise[fid]} games")

    # Verbose: dump every observation with franchise name and margins
    if verbose:
        print()
        print("  Every ≥4-game observation (chronological):")
        print(f"    {'Week':<6s} {'Franchise':<32s} {'Len':<5s} "
              f"{'Class':<20s} Margins")
        print(f"    {'─' * 6} {'─' * 32} {'─' * 5} {'─' * 20} "
              f"{'─' * 40}")
        for fid, tw, seq, cls in observations:
            name = name_map.get(fid, fid)
            short_cls = {
                CLS_STRICTLY_GROWING: "strict growing",
                CLS_STRICTLY_SHRINKING: "strict shrinking",
                CLS_FLAT: "flat",
                CLS_NEAR_GROWING: "near growing",
                CLS_NEAR_SHRINKING: "near shrinking",
                CLS_MIXED: "mixed",
            }[cls]
            print(
                f"    W{tw:<5d} {name:<32s} {len(seq):<5d} "
                f"{short_cls:<20s} {_format_margins(seq)}"
            )

    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Diagnose SCORING_MOMENTUM_IN_STREAK gate tightness against "
            "production win-streak data."
        ),
    )
    ap.add_argument("--db", default=".local_squadvault.sqlite")
    ap.add_argument("--league-id", default="70985")
    ap.add_argument(
        "--season",
        type=int,
        action="append",
        required=True,
        help="Season to scan; pass multiple times to scan several seasons.",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Dump every ≥4-game streak observation with full margins.",
    )
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        return 1

    matchups = load_all_matchups(args.db, args.league_id)
    name_map = build_cross_season_name_resolver(args.db, args.league_id)

    seasons_with_data = 0
    for season in args.season:
        if report_season(
            matchups=matchups,
            season=season,
            name_map=name_map,
            verbose=args.verbose,
        ):
            seasons_with_data += 1

    print()
    if seasons_with_data == 0:
        print("OVERALL: No matchup data found in any scanned season.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
