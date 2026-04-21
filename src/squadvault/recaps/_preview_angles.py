#!/usr/bin/env python3
"""Preview narrative angles for a given week against the live DB.

Runs all 6 angle detection modules, applies the tiered budget,
resolves player and franchise names, and prints the formatted
angle feed exactly as it would appear in the creative layer prompt.

No API key required — this is purely deterministic.

Usage:
  ./scripts/py -u src/squadvault/recaps/_preview_angles.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --season 2024 \
    --week 5

  # All weeks in a season:
  ./scripts/py -u src/squadvault/recaps/_preview_angles.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --season 2024 \
    --all-weeks
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import Counter

from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    detect_auction_draft_angles_v1,
)
from squadvault.core.recaps.context.bye_week_context_v1 import (
    detect_bye_week_angles_v1,
)
from squadvault.core.recaps.context.franchise_deep_angles_v1 import (
    detect_franchise_deep_angles_v1,
)
from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
    compute_franchise_tenures,
    derive_league_history_v1,
    load_all_matchups,
)
from squadvault.core.recaps.context.league_rules_context_v1 import (
    detect_scoring_rules_angles_v1,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    NarrativeAngle,
    detect_narrative_angles_v1,
)
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    detect_player_narrative_angles_v1,
)
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
)
from squadvault.core.resolvers import build_player_name_map
from squadvault.core.resolvers import identity as _identity
from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)


def detect_all_angles(
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    *,
    pname=None,
    fname=None,
) -> tuple[list[NarrativeAngle], dict[str, int | str]]:
    """Run all 6 angle modules and return combined angles + module counts."""
    if pname is None:
        pname = _identity
    if fname is None:
        fname = _identity

    module_counts: dict[str, int | str] = {}

    # Shared context
    try:
        tenure_map = compute_franchise_tenures(db_path, league_id)
    except Exception as exc:
        logger.debug("%s", exc)
        tenure_map = None

    try:
        season_ctx = derive_season_context_v1(
            db_path=db_path, league_id=league_id, season=season, week_index=week,
        )
    except Exception as exc:
        logger.debug("%s", exc)
        season_ctx = None

    try:
        # Scoped to (season, week) per the Weekly Recap Context Temporal
        # Scoping Addendum (v1.0). Mirrors the production recap pipeline
        # so preview output reflects what the real recap would consume.
        history_ctx = derive_league_history_v1(
            db_path=db_path,
            league_id=league_id,
            as_of_season=season,
            as_of_week=week,
        )
    except Exception as exc:
        logger.debug("%s", exc)
        history_ctx = None

    try:
        # Scoped to the same approved window as history_ctx above, so
        # the narrative angle detector receives the same inputs it would
        # receive inside the production recap pipeline.
        all_matchups = load_all_matchups(
            db_path,
            league_id,
            as_of_season=season,
            as_of_week=week,
        )
    except Exception as exc:
        logger.debug("%s", exc)
        all_matchups = None

    all_angles: list[NarrativeAngle] = []

    # Module 1: Franchise-level angles (existing)
    try:
        if season_ctx is not None:
            m1 = detect_narrative_angles_v1(
                season_ctx=season_ctx,
                history_ctx=history_ctx,
                all_matchups=all_matchups,
                tenure_map=tenure_map,
                fname=fname,
            )
            angles = list(m1.angles)
            module_counts["narrative_angles_v1"] = len(angles)
            all_angles.extend(angles)
    except Exception as e:
        module_counts["narrative_angles_v1"] = f"ERROR: {e}"

    # Module 2: Player narrative angles (Dimensions 1-5)
    try:
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            tenure_map=tenure_map,
            pname=pname, fname=fname,
        )
        module_counts["player_narrative"] = len(angles)
        all_angles.extend(angles)
    except Exception as e:
        module_counts["player_narrative"] = f"ERROR: {e}"

    # Module 3: Auction draft angles (Dimension 6)
    try:
        angles = detect_auction_draft_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            pname=pname, fname=fname,
        )
        module_counts["auction_draft"] = len(angles)
        all_angles.extend(angles)
    except Exception as e:
        module_counts["auction_draft"] = f"ERROR: {e}"

    # Module 4: Franchise deep angles (Dimensions 7-9)
    try:
        angles = detect_franchise_deep_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            tenure_map=tenure_map,
            pname=pname, fname=fname,
        )
        module_counts["franchise_deep"] = len(angles)
        all_angles.extend(angles)
    except Exception as e:
        module_counts["franchise_deep"] = f"ERROR: {e}"

    # Module 5: Bye week angles (Dimension 10)
    try:
        angles = detect_bye_week_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            all_matchups=all_matchups,
            fname=fname,
        )
        module_counts["bye_week"] = len(angles)
        all_angles.extend(angles)
    except Exception as e:
        module_counts["bye_week"] = f"ERROR: {e}"

    # Module 6: Scoring rules context (Dimension 11)
    try:
        angles = detect_scoring_rules_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
        )
        module_counts["scoring_rules"] = len(angles)
        all_angles.extend(angles)
    except Exception as e:
        module_counts["scoring_rules"] = f"ERROR: {e}"

    # Sort
    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))
    return all_angles, module_counts


def apply_tiered_budget(angles: list[NarrativeAngle]) -> list[NarrativeAngle]:
    """Apply the tiered angle budget: 3H / 6N / 4m."""
    budgeted: list[NarrativeAngle] = []
    h, n, m = 0, 0, 0
    for a in angles:
        if a.strength >= 3 and h < 3:
            budgeted.append(a)
            h += 1
        elif a.strength == 2 and n < 6:
            budgeted.append(a)
            n += 1
        elif a.strength <= 1 and m < 4 and len(budgeted) < 12:
            budgeted.append(a)
            m += 1
    return budgeted


def render_angle(a: NarrativeAngle) -> str:
    """Render a single angle (names already resolved by detectors)."""
    label = {3: "HEADLINE", 2: "NOTABLE", 1: "MINOR"}.get(a.strength, "")
    line = f"  [{label}] {a.headline}"
    if a.detail:
        line += f" — {a.detail}"
    return line


def preview_week(db_path: str, league_id: str, season: int, week: int) -> None:
    """Print the full angle preview for a single week."""
    name_map = build_cross_season_name_resolver(db_path, league_id)
    player_name_map = build_player_name_map(db_path, league_id)

    all_angles, module_counts = detect_all_angles(
        db_path, league_id, season, week,
        pname=lambda pid: player_name_map.get(pid, pid),
        fname=lambda fid: name_map.get(fid, fid),
    )
    budgeted = apply_tiered_budget(all_angles)

    print(f"\n{'=' * 72}")
    print(f"  NARRATIVE ANGLES PREVIEW — Season {season}, Week {week}")
    print(f"{'=' * 72}")

    # Module summary
    print("\n  Module detection counts:")
    for mod, count in module_counts.items():
        print(f"    {mod:<25s} {count}")
    total_raw = sum(c for c in module_counts.values() if isinstance(c, int))
    print(f"    {'TOTAL RAW':<25s} {total_raw}")
    print(f"    {'AFTER BUDGET':<25s} {len(budgeted)}")

    # Category distribution
    cat_counts = Counter(a.category for a in all_angles)
    if cat_counts:
        print("\n  Category distribution (raw):")
        for cat, cnt in sorted(cat_counts.items()):
            print(f"    {cat:<40s} {cnt}")

    # Budgeted angles (what the creative layer would see)
    if budgeted:
        print("\n  === ANGLE FEED (as sent to creative layer) ===")
        print(f"  Narrative angles for Week {week} (what's interesting):")
        for a in budgeted:
            print(render_angle(a))
        remaining = total_raw - len(budgeted)
        if remaining > 0:
            print(f"  (+ {remaining} minor angles omitted)")
    else:
        print("\n  No angles detected for this week.")

    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Preview narrative angles for recap weeks.")
    ap.add_argument("--db", default=".local_squadvault.sqlite")
    ap.add_argument("--league-id", default="70985")
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--all-weeks", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        return 1

    if args.all_weeks:
        # Discover max week from matchup data
        with DatabaseSession(args.db) as con:
            row = con.execute(
                """SELECT MAX(CAST(json_extract(payload_json, '$.week') AS INTEGER))
                   FROM v_canonical_best_events
                   WHERE league_id = ? AND season = ?
                     AND event_type = 'WEEKLY_MATCHUP_RESULT'""",
                (args.league_id, args.season),
            ).fetchone()
        max_week = row[0] if row and row[0] else 0
        if max_week == 0:
            print(f"No matchup data found for season {args.season}", file=sys.stderr)
            return 1
        print(f"Scanning weeks 1-{max_week} for season {args.season}...")
        for w in range(1, max_week + 1):
            preview_week(args.db, args.league_id, args.season, w)
    elif args.week:
        preview_week(args.db, args.league_id, args.season, args.week)
    else:
        print("ERROR: specify --week N or --all-weeks", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
