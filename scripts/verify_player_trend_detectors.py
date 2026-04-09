#!/usr/bin/env python3
"""Verify Player Trend Detectors (T1-T11) are firing in production data.

Walks every week of one or more seasons, invokes
``detect_player_narrative_angles_v1`` exactly as the recap lifecycle does,
and reports per-detector firing rates.

Purpose: confirm the player narrative angle detectors are doing real work
on production data, not silently no-op-ing on a data shape mismatch.

This script is read-only. It does not modify the database, generate any
LLM output, or touch any external API. It is purely a diagnostic.

Usage::

    ./scripts/py -u scripts/verify_player_trend_detectors.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2025

    # Sweep both production seasons:
    ./scripts/py -u scripts/verify_player_trend_detectors.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025

    # Show a few sample angle headlines per category:
    ./scripts/py -u scripts/verify_player_trend_detectors.py \\
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
    compute_franchise_tenures,
)
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    detect_player_narrative_angles_v1,
)
from squadvault.core.resolvers import build_player_name_map
from squadvault.core.storage.session import DatabaseSession

# ─────────────────────────────────────────────────────────────────────
# Detector category catalog — every category string emitted by
# player_narrative_angles_v1, grouped by the dimension it lives in.
# Order here is the order rendered in the summary table.
# ─────────────────────────────────────────────────────────────────────

DIMENSION_1_SHORT_HORIZON = [
    ("PLAYER_HOT_STREAK", "T1"),
    ("PLAYER_COLD_STREAK", "T2"),
    ("PLAYER_SEASON_HIGH", "T3"),
    ("PLAYER_BOOM_BUST", "T4"),
    ("PLAYER_BREAKOUT", "T5"),
    ("ZERO_POINT_STARTER", "T6"),
]

DIMENSION_2_LONG_HORIZON = [
    ("PLAYER_ALLTIME_HIGH", "T7"),
    ("PLAYER_FRANCHISE_RECORD", "T8"),
    ("CAREER_MILESTONE", "T9"),
    ("PLAYER_FRANCHISE_TENURE", "T10"),
    ("PLAYER_JOURNEY", "T11"),
]

DIMENSION_3_VS_OPPONENT = [
    ("PLAYER_VS_OPPONENT", "D3"),
    ("REVENGE_GAME", "D3"),
    ("PLAYER_DUEL", "D3"),
]

DIMENSION_4_TRADES = [
    ("TRADE_OUTCOME", "D4"),
    ("THE_ONE_THAT_GOT_AWAY", "D4"),
]

DIMENSION_5_FAAB = [
    ("FAAB_ROI_NOTABLE", "D5"),
    ("FAAB_FRANCHISE_EFFICIENCY", "D5"),
    ("WAIVER_DEPENDENCY", "D5"),
]

ALL_DIMENSIONS = [
    ("Dimension 1 — Short horizon (current season)", DIMENSION_1_SHORT_HORIZON),
    ("Dimension 2 — Long horizon (cross-season)", DIMENSION_2_LONG_HORIZON),
    ("Dimension 3 — Player vs. opponent", DIMENSION_3_VS_OPPONENT),
    ("Dimension 4 — Trade & transaction outcomes", DIMENSION_4_TRADES),
    ("Dimension 5 — FAAB & waiver efficiency", DIMENSION_5_FAAB),
]

ALL_KNOWN_CATEGORIES = {
    cat for _, dim in ALL_DIMENSIONS for cat, _ in dim
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
    tenure_map: dict[str, int] | None,
) -> tuple[Counter[str], dict[str, set[int]], dict[str, list[str]], int]:
    """Scan one season, return (totals, weeks_active, samples, weeks_scanned).

    - totals[category] = total angle count across season
    - weeks_active[category] = set of week indices where category fired
    - samples[category] = list of headlines (capped per --samples flag)
    - weeks_scanned = number of weeks walked
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
        angles = detect_player_narrative_angles_v1(
            db_path=db_path,
            league_id=league_id,
            season=season,
            week=week,
            tenure_map=tenure_map,
            pname=pname,
            fname=fname,
        )
        for a in angles:
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
    """Print one dimension's table. Returns count of zero-firing detectors."""
    print(f"\n  {dim_label}")
    print(f"  {'─' * (len(dim_label))}")
    print(f"    {'Detector':<28s} {'Code':<5s} {'Fires':>7s} {'Weeks':>7s} {'Rate':>7s}")
    print(f"    {'─' * 28} {'─' * 5} {'─' * 7} {'─' * 7} {'─' * 7}")

    zero_firing = 0
    for category, code in detectors:
        fires = totals.get(category, 0)
        weeks_count = len(weeks_active.get(category, set()))
        rate = (weeks_count / weeks_scanned * 100.0) if weeks_scanned else 0.0
        marker = "  ⚠ " if fires == 0 else "    "
        if fires == 0:
            zero_firing += 1
        print(
            f"  {marker}{category:<28s} {code:<5s} {fires:>7d} {weeks_count:>7d} "
            f"{rate:>6.1f}%"
        )
        if sample_count > 0 and samples.get(category):
            for headline in samples[category][:sample_count]:
                # truncate long headlines for table sanity
                shown = headline if len(headline) <= 76 else headline[:73] + "..."
                print(f"        · {shown}")
    return zero_firing


def report_season(
    *,
    db_path: str,
    league_id: str,
    season: int,
    sample_count: int,
) -> tuple[int, bool]:
    """Run the verification scan for one season and print the report.

    Returns ``(zero_firing_count, had_data)``:

    - ``zero_firing_count``: how many of the 11 T1-T11 detectors (Dimensions
      1-2) did not fire at all in this season. This is the headline
      diagnostic. Dimensions 3-5 are reported for completeness but are not
      counted toward the warning total since their firing depends on trades,
      FAAB, and matchup overlap that may legitimately be absent.
    - ``had_data``: True iff at least one week of WEEKLY_MATCHUP_RESULT data
      was found for this season.
    """
    print(f"\n{'=' * 78}")
    print(f"  PLAYER TREND DETECTOR VERIFICATION — Season {season}")
    print(f"{'=' * 78}")

    name_map = build_cross_season_name_resolver(db_path, league_id)
    player_name_map = build_player_name_map(db_path, league_id)
    try:
        tenure_map = compute_franchise_tenures(db_path, league_id)
    except Exception as exc:  # noqa: BLE001
        print(f"  (tenure_map unavailable: {exc})")
        tenure_map = None

    totals, weeks_active, samples, weeks_scanned = _scan_season(
        db_path=db_path,
        league_id=league_id,
        season=season,
        name_map=name_map,
        player_name_map=player_name_map,
        tenure_map=tenure_map,
    )

    if weeks_scanned == 0:
        print(f"  No WEEKLY_MATCHUP_RESULT data found for season {season}.")
        return 0, False

    total_angles = sum(totals.values())
    print(f"\n  Weeks scanned:       {weeks_scanned}")
    print(f"  Total angles fired:  {total_angles}")
    print(f"  Distinct categories: {len(totals)}")

    t1_t11_zero = 0
    for dim_label, detectors in ALL_DIMENSIONS:
        zero_count = _print_dimension_table(
            dim_label=dim_label,
            detectors=detectors,
            totals=totals,
            weeks_active=weeks_active,
            weeks_scanned=weeks_scanned,
            samples=samples,
            sample_count=sample_count,
        )
        if dim_label.startswith("Dimension 1") or dim_label.startswith("Dimension 2"):
            t1_t11_zero += zero_count

    # Surface any unexpected categories not in our catalog (would indicate
    # a new detector landed without updating this script).
    unknown = sorted(set(totals.keys()) - ALL_KNOWN_CATEGORIES)
    if unknown:
        print("\n  ⚠ Unknown categories (not in script catalog):")
        for cat in unknown:
            print(f"      {cat}: {totals[cat]} fires")

    # Headline verdict
    print()
    if t1_t11_zero == 0:
        print(f"  ✓ All 11 T1-T11 detectors fired at least once in season {season}.")
    else:
        print(
            f"  ⚠ {t1_t11_zero} of 11 T1-T11 detectors did NOT fire in "
            f"season {season} — investigate."
        )
    return t1_t11_zero, True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify player trend detectors fire on production data.",
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
            f"OVERALL: {total_warnings} zero-firing T1-T11 detector(s) "
            f"across {seasons_with_data} season(s) with data."
        )
        return 2
    print(
        f"OVERALL: All T1-T11 detectors firing across {seasons_with_data} "
        f"season(s) with data."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
