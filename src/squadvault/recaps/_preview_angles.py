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
import os
import re
import sys
from collections import Counter

from squadvault.core.recaps.context.narrative_angles_v1 import (
    NarrativeAngle,
    detect_narrative_angles_v1,
)
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    detect_player_narrative_angles_v1,
)
from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    detect_auction_draft_angles_v1,
)
from squadvault.core.recaps.context.franchise_deep_angles_v1 import (
    detect_franchise_deep_angles_v1,
)
from squadvault.core.recaps.context.bye_week_context_v1 import (
    detect_bye_week_angles_v1,
)
from squadvault.core.recaps.context.league_rules_context_v1 import (
    detect_scoring_rules_angles_v1,
)
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
)
from squadvault.core.recaps.context.league_history_v1 import (
    compute_franchise_tenures,
    derive_league_history_v1,
    load_all_matchups,
    build_cross_season_name_resolver,
)
from squadvault.core.storage.session import DatabaseSession


def _build_player_name_map(db_path: str, league_id: str) -> dict[str, str]:
    """Build player_id -> name map from player_directory."""
    name_map: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT player_id, name FROM player_directory
               WHERE league_id = ? ORDER BY season DESC""",
            (str(league_id),),
        ).fetchall()
    for row in rows:
        pid = str(row[0]).strip()
        name = str(row[1]).strip() if row[1] else ""
        if pid and name and pid not in name_map:
            name_map[pid] = name
    return name_map


def detect_all_angles(
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> tuple[list[NarrativeAngle], dict[str, int]]:
    """Run all 6 angle modules and return combined angles + module counts."""
    module_counts: dict[str, int] = {}

    # Shared context
    try:
        tenure_map = compute_franchise_tenures(db_path, league_id)
    except Exception:
        tenure_map = None

    try:
        season_ctx = derive_season_context_v1(
            db_path=db_path, league_id=league_id, season=season, week_index=week,
        )
    except Exception:
        season_ctx = None

    try:
        history_ctx = derive_league_history_v1(db_path=db_path, league_id=league_id)
    except Exception:
        history_ctx = None

    try:
        all_matchups = load_all_matchups(db_path, league_id)
    except Exception:
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
        )
        module_counts["player_narrative"] = len(angles)
        all_angles.extend(angles)
    except Exception as e:
        module_counts["player_narrative"] = f"ERROR: {e}"

    # Module 3: Auction draft angles (Dimension 6)
    try:
        angles = detect_auction_draft_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
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


def render_angle(
    a: NarrativeAngle,
    name_map: dict[str, str],
    player_name_map: dict[str, str],
) -> str:
    """Render a single angle with name resolution."""
    label = {3: "HEADLINE", 2: "NOTABLE", 1: "MINOR"}.get(a.strength, "")
    headline = a.headline
    detail = a.detail
    for fid, fname in name_map.items():
        headline = headline.replace(fid, fname)
        if detail:
            detail = detail.replace(fid, fname)
    for pid, pname in player_name_map.items():
        pat = r'(?<!\d)' + re.escape(pid) + r'(?!\d)'
        headline = re.sub(pat, pname, headline)
        if detail:
            detail = re.sub(pat, pname, detail)
    line = f"  [{label}] {headline}"
    if detail:
        line += f" — {detail}"
    return line


def preview_week(db_path: str, league_id: str, season: int, week: int) -> None:
    """Print the full angle preview for a single week."""
    name_map = build_cross_season_name_resolver(db_path, league_id)
    player_name_map = _build_player_name_map(db_path, league_id)

    all_angles, module_counts = detect_all_angles(db_path, league_id, season, week)
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
            print(render_angle(a, name_map, player_name_map))
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
