#!/usr/bin/env python3
"""Diagnose a full season: EAL directives, angle detection, and recap readiness.

Run against the production DB to answer three open questions:
1. Are playoff weeks getting appropriate EAL directives?
2. Are detector thresholds well-calibrated across weeks?
3. Which weeks are ready for recap regeneration?

Usage:
  ./scripts/py -u scripts/diagnose_season_readiness.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --season 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from squadvault.core.eal.editorial_attunement_v1 import EALMeta, evaluate_editorial_attunement_v1
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
from squadvault.core.resolvers import build_player_name_map, identity as _identity
from squadvault.core.storage.session import DatabaseSession


def _eal_for_week(db_path: str, league_id: str, season: int, week: int) -> tuple[str, int | None]:
    """Return (eal_directive, included_count) for a week."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week),
        ).fetchone()
        if not row or not row[0]:
            return ("NO_RECAP_RUN", None)
        try:
            ids = json.loads(row[0])
            included = len(ids) if isinstance(ids, list) else None
        except (ValueError, TypeError):
            included = None

        # Playoff detection: find the last week with full matchup count (= last regular
        # season week). Any week after that is a playoff, even if it has no matchup results.
        is_playoff = False
        try:
            _last_regular_row = con.execute(
                "SELECT MAX(week) FROM ("
                "  SELECT CAST(json_extract(payload_json, '$.week') AS INTEGER) as week,"
                "         COUNT(*) as cnt"
                "  FROM v_canonical_best_events"
                "  WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
                "  GROUP BY json_extract(payload_json, '$.week')"
                "  HAVING cnt = ("
                "    SELECT MAX(cnt2) FROM ("
                "      SELECT COUNT(*) as cnt2 FROM v_canonical_best_events"
                "      WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
                "      GROUP BY json_extract(payload_json, '$.week')"
                "    )"
                "  )"
                ")",
                (league_id, season, league_id, season),
            ).fetchone()
            _last_regular_week = _last_regular_row[0] if _last_regular_row else None
            if _last_regular_week and week > _last_regular_week:
                is_playoff = True
        except Exception:
            pass

    meta = EALMeta(has_selection_set=True, has_window=True, included_count=included, is_playoff=is_playoff)
    return (evaluate_editorial_attunement_v1(meta), included)


def _detect_all_angles(
    db_path: str, league_id: str, season: int, week: int,
    name_map: dict, player_name_map: dict, tenure_map: dict | None,
    season_ctx: object | None, history_ctx: object | None, all_matchups: object | None,
) -> list[NarrativeAngle]:
    """Run all detector modules for a single week."""
    all_angles: list[NarrativeAngle] = []
    fname = lambda fid: name_map.get(fid, fid)
    pname = lambda pid: player_name_map.get(pid, pid)

    try:
        all_angles.extend(detect_player_narrative_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            tenure_map=tenure_map, pname=pname, fname=fname,
        ))
    except Exception:
        pass

    try:
        all_angles.extend(detect_auction_draft_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            pname=pname, fname=fname,
        ))
    except Exception:
        pass

    try:
        all_angles.extend(detect_franchise_deep_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            tenure_map=tenure_map, pname=pname, fname=fname,
        ))
    except Exception:
        pass

    if season_ctx is not None:
        try:
            result = detect_narrative_angles_v1(
                season_ctx=season_ctx, history_ctx=history_ctx,
                all_matchups=all_matchups, tenure_map=tenure_map, fname=fname,
            )
            all_angles.extend(result.angles)
        except Exception:
            pass

    try:
        all_angles.extend(detect_bye_week_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
            all_matchups=all_matchups, fname=fname,
        ))
    except Exception:
        pass

    try:
        all_angles.extend(detect_scoring_rules_angles_v1(
            db_path=db_path, league_id=league_id, season=season, week=week,
        ))
    except Exception:
        pass

    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))
    return all_angles


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Diagnose season readiness: EAL, angles, recap status.")
    ap.add_argument("--db", required=True, help="Path to SQLite DB")
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--max-weeks", type=int, default=18)
    ap.add_argument("--show-angles", action="store_true", help="Print angle headlines per week")
    args = ap.parse_args(argv)

    db_path = args.db
    league_id = args.league_id
    season = args.season

    if not Path(db_path).exists():
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        return 1

    # Load shared context once
    print(f"Loading context for league {league_id} season {season}...")
    name_map = {}
    player_name_map: dict[str, str] = {}
    tenure_map = None
    history_ctx = None
    all_matchups = None

    try:
        name_map = build_cross_season_name_resolver(db_path, league_id)
    except Exception:
        pass
    try:
        player_name_map = build_player_name_map(db_path, league_id)
    except Exception:
        pass
    try:
        history_ctx = derive_league_history_v1(db_path=db_path, league_id=league_id)
        tenure_map = compute_franchise_tenures(db_path, league_id)
    except Exception:
        pass
    try:
        all_matchups = load_all_matchups(db_path, league_id)
    except Exception:
        pass

    # Per-week diagnosis
    print(f"\n{'Week':>4}  {'Events':>6}  {'EAL Directive':<28}  {'Angles':>6}  {'H':>2}  {'N':>2}  {'M':>2}  Notes")
    print("-" * 90)

    total_angles_by_week: list[int] = []
    eal_issues: list[str] = []

    for week in range(1, args.max_weeks + 1):
        eal_dir, included = _eal_for_week(db_path, league_id, season, week)

        if eal_dir == "NO_RECAP_RUN":
            print(f"{week:4d}  {'—':>6}  {'(no recap_run)':28}  {'—':>6}  {'':>2}  {'':>2}  {'':>2}")
            continue

        # Derive season context for this specific week
        season_ctx = None
        try:
            season_ctx = derive_season_context_v1(
                db_path=db_path, league_id=league_id, season=season, week_index=week,
            )
        except Exception:
            pass

        is_playoff = (season_ctx and hasattr(season_ctx, 'playoff_info')
                      and season_ctx.playoff_info
                      and season_ctx.playoff_info.is_playoff)

        angles = _detect_all_angles(
            db_path, league_id, season, week,
            name_map, player_name_map, tenure_map,
            season_ctx, history_ctx, all_matchups,
        )

        h = sum(1 for a in angles if a.strength >= 3)
        n = sum(1 for a in angles if a.strength == 2)
        m = sum(1 for a in angles if a.strength <= 1)

        notes = []
        if is_playoff:
            notes.append("PLAYOFF")
        if eal_dir == "LOW_CONFIDENCE_RESTRAINT":
            notes.append("⚠ LOW_CONF")
        if eal_dir == "AMBIGUITY_PREFER_SILENCE":
            notes.append("🔇 SILENCE")
        if included is not None and included < 8:
            notes.append(f"low_events({included})")
        if len(angles) == 0:
            notes.append("no_angles")

        notes_str = "  ".join(notes)
        inc_str = str(included) if included is not None else "?"
        print(f"{week:4d}  {inc_str:>6}  {eal_dir:28}  {len(angles):6d}  {h:2d}  {n:2d}  {m:2d}  {notes_str}")

        total_angles_by_week.append(len(angles))

        if is_playoff and eal_dir in ("LOW_CONFIDENCE_RESTRAINT", "AMBIGUITY_PREFER_SILENCE"):
            eal_issues.append(f"Week {week} (playoff): {eal_dir} with {included} events")

        if args.show_angles and angles:
            for a in angles[:15]:
                slabel = {3: "H", 2: "N", 1: "M"}.get(a.strength, "?")
                print(f"        [{slabel}] {a.headline}")
            if len(angles) > 15:
                print(f"        (+ {len(angles) - 15} more)")

    # Summary
    print("\n" + "=" * 90)
    if total_angles_by_week:
        avg = sum(total_angles_by_week) / len(total_angles_by_week)
        print(f"Angle stats: avg={avg:.1f}, min={min(total_angles_by_week)}, max={max(total_angles_by_week)}")

    if eal_issues:
        print(f"\n⚠  PLAYOFF EAL ISSUES ({len(eal_issues)}):")
        for issue in eal_issues:
            print(f"  {issue}")
        print("  → If included_count is low due to few matchups, consider a playoff-aware threshold.")
    else:
        print("\n✓  No playoff EAL issues detected.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
