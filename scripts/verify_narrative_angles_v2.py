#!/usr/bin/env python3
"""Verify Narrative Angles v2 detectors (Phases 1, 6-11) fire in production.

Walks every week of one or more seasons, invokes the unified angle pipeline
exactly the way the recap lifecycle does, and reports per-detector firing
rates for the five non-player angle modules:

    - narrative_angles_v1            (foundation — franchise-level baseline)
    - auction_draft_angles_v1        (Dimension 6)
    - franchise_deep_angles_v1       (Dimensions 7, 8, 9)
    - bye_week_context_v1            (Dimension 10)
    - league_rules_context_v1        (Dimension 11)

Player narrative angles (Dimensions 1-5) are deliberately EXCLUDED — those
are covered by ``scripts/verify_player_trend_detectors.py``. Run both
scripts to get the complete narrative-angle landscape.

This script is read-only. It does not modify the database, generate any
LLM output, or touch any external API.

Usage::

    ./scripts/py -u scripts/verify_narrative_angles_v2.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025

    # With sample headlines:
    ./scripts/py -u scripts/verify_narrative_angles_v2.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2025 --samples 2
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict

from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
)
from squadvault.core.resolvers import build_player_name_map
from squadvault.core.storage.session import DatabaseSession
from squadvault.recaps._preview_angles import detect_all_angles

# ─────────────────────────────────────────────────────────────────────
# Detector category catalog — every category string emitted by the five
# non-player angle modules, grouped by the dimension it lives in.
#
# Sourced by: grep 'category="' on each module's source file at b55cc17.
# franchise_deep_angles_v1 dimension assignments derived from the file's
# explicit ``# ── Dimension N`` section markers.
# ─────────────────────────────────────────────────────────────────────

# (category, expected_state) — expected_state is one of:
#   "normal"          — should fire at meaningful rates; zero is suspicious
#   "rare"            — fires sparingly by design; low rate is fine
#   "expected_zero"   — disabled detector; zero is the correct state
EXPECTED_NORMAL = "normal"
EXPECTED_RARE = "rare"
EXPECTED_ZERO = "expected_zero"


FOUNDATION_FRANCHISE = [
    # narrative_angles_v1 — the original franchise-level baseline (pre-v2).
    ("BLOWOUT", EXPECTED_NORMAL),
    ("NAIL_BITER", EXPECTED_NORMAL),
    ("RIVALRY", EXPECTED_NORMAL),
    ("SCORING_ANOMALY", EXPECTED_NORMAL),
    ("SCORING_RECORD", EXPECTED_RARE),
    ("STREAK", EXPECTED_NORMAL),
    ("UPSET", EXPECTED_NORMAL),
]

DIMENSION_6_AUCTION = [
    # auction_draft_angles_v1
    # AUCTION_BUDGET_ALLOCATION: gate requires the most-concentrated
    # franchise's bid std-dev to be > 1.5x the most-balanced franchise's.
    # In any season where all 10 franchises draft with similar spread,
    # the detector legitimately stays silent. Re-tagged rare based on
    # 2026-04-09 verification + source inspection.
    ("AUCTION_BUDGET_ALLOCATION", EXPECTED_RARE),
    ("AUCTION_BUST", EXPECTED_NORMAL),
    ("AUCTION_DOLLAR_PER_POINT", EXPECTED_NORMAL),
    ("AUCTION_DRAFT_TO_FAAB_PIPELINE", EXPECTED_NORMAL),
    ("AUCTION_LEAGUE_INFLATION", EXPECTED_RARE),
    ("AUCTION_MOST_EXPENSIVE_HISTORY", EXPECTED_RARE),
    ("AUCTION_POSITIONAL_SPENDING", EXPECTED_NORMAL),
    # AUCTION_PRICE_VS_PRODUCTION: gate requires the all-time best
    # points-per-dollar pick in league history to (a) still be on their
    # original drafting franchise and (b) score this week. The all-time
    # leader is locked in across seasons, so when they're traded or
    # dropped the detector goes silent for the rest of league history.
    # Re-tagged rare based on 2026-04-09 verification + source inspection.
    ("AUCTION_PRICE_VS_PRODUCTION", EXPECTED_RARE),
    ("AUCTION_STRATEGY_CONSISTENCY", EXPECTED_NORMAL),
]

DIMENSION_7_FRANCHISE_SCORING = [
    # franchise_deep_angles_v1 — Dimension 7 section
    ("POSITIONAL_STRENGTH", EXPECTED_NORMAL),
    # SCORING_CONCENTRATION: gate requires a single starter to account
    # for ≥35% of franchise total starter scoring through this week. A
    # high bar — requires a genuinely dominant individual or a weak
    # surrounding cast. Re-tagged rare based on 2026-04-09 verification
    # + source inspection.
    ("SCORING_CONCENTRATION", EXPECTED_RARE),
    ("SCORING_VOLATILITY", EXPECTED_NORMAL),
    # STAR_EXPLOSION_COUNT: gate requires one franchise to have 3+
    # individual 40+ point performances AND at least 2x the next-highest
    # franchise's count. The 2x dominance threshold is steep; in any
    # season where multiple franchises have stars, no one team will
    # double the others. Re-tagged rare based on 2026-04-09 verification
    # + source inspection.
    ("STAR_EXPLOSION_COUNT", EXPECTED_RARE),
]

DIMENSION_8_BENCH_LINEUP = [
    # franchise_deep_angles_v1 — Dimension 8 section
    ("BENCH_COST_GAME", EXPECTED_NORMAL),
    ("CHRONIC_BENCH_MISMANAGEMENT", EXPECTED_RARE),
    ("PERFECT_LINEUP_WEEK", EXPECTED_RARE),
]

DIMENSION_9_FRANCHISE_HISTORY = [
    # franchise_deep_angles_v1 — Dimension 9 section
    ("CHAMPIONSHIP_HISTORY", EXPECTED_RARE),
    # CLOSE_GAME_RECORD: per documented learning, was fixed to only fire when
    # the record-holding franchise is actually involved in the week's close
    # game. Expected to fire occasionally, not every week.
    ("CLOSE_GAME_RECORD", EXPECTED_RARE),
    ("FRANCHISE_ALLTIME_SCORING", EXPECTED_RARE),
    ("LUCKY_RECORD", EXPECTED_NORMAL),
    ("POINTS_AGAINST_LUCK", EXPECTED_NORMAL),
    ("REGULAR_SEASON_VS_PLAYOFF", EXPECTED_RARE),
    ("REPEAT_MATCHUP_PATTERN", EXPECTED_RARE),
    ("SCHEDULE_STRENGTH", EXPECTED_NORMAL),
    ("SCORING_MOMENTUM_IN_STREAK", EXPECTED_NORMAL),
    ("SEASON_TRAJECTORY_MATCH", EXPECTED_NORMAL),
    ("SECOND_HALF_SURGE_COLLAPSE", EXPECTED_NORMAL),
    ("THE_ALMOST", EXPECTED_RARE),
    ("THE_BRIDESMAID", EXPECTED_RARE),
    # TRANSACTION_VOLUME_IDENTITY: per documented learning, transaction
    # counts proved unverifiable and consistently fabricated; the detector
    # is disabled. Zero is the correct firing rate.
    ("TRANSACTION_VOLUME_IDENTITY", EXPECTED_ZERO),
    ("WEEKLY_SCORING_RANK_DOMINANCE", EXPECTED_NORMAL),
]

DIMENSION_10_BYE = [
    # bye_week_context_v1
    ("BYE_WEEK_CONFLICT", EXPECTED_NORMAL),
    ("BYE_WEEK_IMPACT", EXPECTED_NORMAL),
    ("FRANCHISE_BYE_WEEK_RECORD", EXPECTED_RARE),
]

DIMENSION_11_RULES = [
    # league_rules_context_v1
    ("SCORING_STRUCTURE_CONTEXT", EXPECTED_RARE),
]

ALL_DIMENSIONS = [
    ("Foundation — Franchise-level (narrative_angles_v1)", FOUNDATION_FRANCHISE),
    ("Dimension 6 — Auction draft strategy & outcomes", DIMENSION_6_AUCTION),
    ("Dimension 7 — Franchise scoring patterns", DIMENSION_7_FRANCHISE_SCORING),
    ("Dimension 8 — Bench & lineup decisions", DIMENSION_8_BENCH_LINEUP),
    ("Dimension 9 — Franchise history & identity", DIMENSION_9_FRANCHISE_HISTORY),
    ("Dimension 10 — Bye week impact", DIMENSION_10_BYE),
    ("Dimension 11 — Scoring rules context", DIMENSION_11_RULES),
]

ALL_KNOWN_CATEGORIES: set[str] = {
    cat for _, dim in ALL_DIMENSIONS for cat, _ in dim
}

# Categories owned by player_narrative_angles_v1, deliberately filtered out
# of this scan (covered by verify_player_trend_detectors.py instead).
PLAYER_CATEGORIES: set[str] = {
    "PLAYER_HOT_STREAK", "PLAYER_COLD_STREAK", "PLAYER_SEASON_HIGH",
    "PLAYER_BOOM_BUST", "PLAYER_BREAKOUT", "ZERO_POINT_STARTER",
    "PLAYER_ALLTIME_HIGH", "PLAYER_FRANCHISE_RECORD", "CAREER_MILESTONE",
    "PLAYER_FRANCHISE_TENURE", "PLAYER_JOURNEY",
    "PLAYER_VS_OPPONENT", "REVENGE_GAME", "PLAYER_DUEL",
    "TRADE_OUTCOME", "THE_ONE_THAT_GOT_AWAY",
    "FAAB_ROI_NOTABLE", "FAAB_FRANCHISE_EFFICIENCY", "WAIVER_DEPENDENCY",
}


def _discover_max_week(db_path: str, league_id: str, season: int) -> int:
    """Return the highest week index with WEEKLY_MATCHUP_RESULT data."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """
            SELECT MAX(CAST(json_extract(payload_json, '$.week') AS INTEGER))
              FROM v_canonical_best_events
             WHERE league_id = ? AND season = ?
               AND event_type = 'WEEKLY_MATCHUP_RESULT'
            """,
            (league_id, season),
        ).fetchone()
    return int(row[0]) if row and row[0] else 0


def _scan_season(
    db_path: str,
    league_id: str,
    season: int,
    name_map: dict[str, str],
    player_name_map: dict[str, str],
) -> tuple[Counter[str], dict[str, set[int]], dict[str, list[str]], int]:
    """Scan one season, return (totals, weeks_active, samples, weeks_scanned).

    Player narrative categories are filtered out before aggregation.
    """
    max_week = _discover_max_week(db_path, league_id, season)
    if max_week == 0:
        return Counter(), defaultdict(set), defaultdict(list), 0

    totals: Counter[str] = Counter()
    weeks_active: dict[str, set[int]] = defaultdict(set)
    samples: dict[str, list[str]] = defaultdict(list)

    pname = lambda pid: player_name_map.get(pid, pid)  # noqa: E731
    fname = lambda fid: name_map.get(fid, fid)  # noqa: E731

    for week in range(1, max_week + 1):
        angles, _module_counts = detect_all_angles(
            db_path=db_path,
            league_id=league_id,
            season=season,
            week=week,
            pname=pname,
            fname=fname,
        )
        for a in angles:
            if a.category in PLAYER_CATEGORIES:
                continue
            totals[a.category] += 1
            weeks_active[a.category].add(week)
            samples[a.category].append(a.headline)

    return totals, weeks_active, samples, max_week


def _print_dimension_table(
    *,
    dim_label: str,
    detectors: list[tuple[str, str]],
    totals: Counter[str],
    weeks_active: dict[str, set[int]],
    weeks_scanned: int,
    samples: dict[str, list[str]],
    sample_count: int,
) -> int:
    """Print one dimension's table. Returns count of unexpected zero-firing
    detectors (i.e., zero fires for a category whose expected state is
    NORMAL — RARE-zero and EXPECTED_ZERO are not counted)."""
    print(f"\n  {dim_label}")
    print(f"  {'─' * len(dim_label)}")
    print(
        f"    {'Detector':<32s} {'Expected':<10s} {'Fires':>7s} "
        f"{'Weeks':>7s} {'Rate':>7s}"
    )
    print(
        f"    {'─' * 32} {'─' * 10} {'─' * 7} {'─' * 7} {'─' * 7}"
    )

    unexpected_zero = 0
    for category, expected in detectors:
        fires = totals.get(category, 0)
        weeks_count = len(weeks_active.get(category, set()))
        rate = (weeks_count / weeks_scanned * 100.0) if weeks_scanned else 0.0

        if fires == 0:
            if expected == EXPECTED_NORMAL:
                marker = "  ⚠ "
                unexpected_zero += 1
            elif expected == EXPECTED_ZERO:
                marker = "  · "  # disabled — zero is correct
            else:  # rare
                marker = "    "
        else:
            marker = "    "

        expected_label = {
            EXPECTED_NORMAL: "normal",
            EXPECTED_RARE: "rare",
            EXPECTED_ZERO: "disabled",
        }[expected]

        print(
            f"  {marker}{category:<32s} {expected_label:<10s} "
            f"{fires:>7d} {weeks_count:>7d} {rate:>6.1f}%"
        )
        if sample_count > 0 and samples.get(category):
            for headline in samples[category][:sample_count]:
                shown = headline if len(headline) <= 80 else headline[:77] + "..."
                print(f"        · {shown}")
    return unexpected_zero


def report_season(
    *,
    db_path: str,
    league_id: str,
    season: int,
    sample_count: int,
) -> tuple[int, bool]:
    """Run the verification scan for one season and print the report.

    Returns ``(unexpected_zero_count, had_data)``:

    - ``unexpected_zero_count``: how many categories whose expected state is
      NORMAL fired zero times. RARE categories with zero fires and disabled
      categories (expected_zero) are NOT counted toward this total.
    - ``had_data``: True iff at least one week of WEEKLY_MATCHUP_RESULT data
      was found for this season.
    """
    print(f"\n{'=' * 78}")
    print(f"  NARRATIVE ANGLES v2 VERIFICATION — Season {season}")
    print(f"{'=' * 78}")

    name_map = build_cross_season_name_resolver(db_path, league_id)
    player_name_map = build_player_name_map(db_path, league_id)

    totals, weeks_active, samples, weeks_scanned = _scan_season(
        db_path=db_path,
        league_id=league_id,
        season=season,
        name_map=name_map,
        player_name_map=player_name_map,
    )

    if weeks_scanned == 0:
        print(f"  No WEEKLY_MATCHUP_RESULT data found for season {season}.")
        return 0, False

    total_angles = sum(totals.values())
    print(f"\n  Weeks scanned:       {weeks_scanned}")
    print(f"  Total non-player angles fired:  {total_angles}")
    print(f"  Distinct non-player categories: {len(totals)}")

    total_unexpected_zero = 0
    for dim_label, detectors in ALL_DIMENSIONS:
        unexpected = _print_dimension_table(
            dim_label=dim_label,
            detectors=detectors,
            totals=totals,
            weeks_active=weeks_active,
            weeks_scanned=weeks_scanned,
            samples=samples,
            sample_count=sample_count,
        )
        total_unexpected_zero += unexpected

    # Surface any categories that fired but aren't in our catalog (would
    # indicate a new detector landed without updating this script).
    unknown = sorted(
        set(totals.keys()) - ALL_KNOWN_CATEGORIES - PLAYER_CATEGORIES
    )
    if unknown:
        print("\n  ⚠ Unknown categories (not in script catalog):")
        for cat in unknown:
            print(f"      {cat}: {totals[cat]} fires")

    # Headline verdict
    print()
    if total_unexpected_zero == 0:
        print(
            f"  ✓ All NORMAL-tier detectors fired at least once in season {season}."
        )
    else:
        print(
            f"  ⚠ {total_unexpected_zero} NORMAL-tier detector(s) did NOT fire "
            f"in season {season} — investigate."
        )
    return total_unexpected_zero, True


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Verify Narrative Angles v2 non-player detectors fire on "
            "production data."
        ),
    )
    ap.add_argument("--db", default=".local_squadvault.sqlite")
    ap.add_argument("--league-id", default="70985")
    ap.add_argument(
        "--season",
        type=int,
        action="append",
        required=True,
        help="Season to scan; pass multiple times to sweep several seasons.",
    )
    ap.add_argument(
        "--samples",
        type=int,
        default=0,
        help="Show N sample headlines per detector (default: 0, summary only).",
    )
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        return 1

    total_warnings = 0
    seasons_with_data = 0
    for season in args.season:
        warnings, had_data = report_season(
            db_path=args.db,
            league_id=args.league_id,
            season=season,
            sample_count=args.samples,
        )
        total_warnings += warnings
        if had_data:
            seasons_with_data += 1

    print()
    if seasons_with_data == 0:
        print("OVERALL: No matchup data found in any scanned season.")
        return 1
    if total_warnings > 0:
        print(
            f"OVERALL: {total_warnings} unexpected zero-firing NORMAL "
            f"detector(s) across {seasons_with_data} season(s) with data."
        )
        return 2
    print(
        f"OVERALL: All NORMAL-tier detectors firing across "
        f"{seasons_with_data} season(s) with data."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
