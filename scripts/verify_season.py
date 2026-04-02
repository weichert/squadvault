"""Scan all APPROVED recaps for a season through the V1 verifier.

Usage:
    ./scripts/py scripts/verify_season.py [--season 2025] [--league 70985]

Reports all hard and soft failures by week, then a season summary.
"""
from __future__ import annotations

import argparse
import sys

from squadvault.core.recaps.verification.recap_verifier_v1 import (
    _build_reverse_name_map,
    _extract_shareable_recap,
    _load_franchise_names,
    verify_cross_week_consistency,
    verify_recap_v1,
)
from squadvault.core.storage.session import DatabaseSession

DB_PATH = ".local_squadvault.sqlite"


def _load_approved_weeks(
    db_path: str, league_id: str, season: int,
) -> list[tuple[int, str]]:
    """Return (week_index, rendered_text) for all APPROVED recaps."""
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT week_index, rendered_text
               FROM recap_artifacts
               WHERE league_id = ? AND season = ?
                 AND artifact_type = 'WEEKLY_RECAP'
                 AND state = 'APPROVED'
               ORDER BY week_index ASC""",
            (str(league_id), int(season)),
        ).fetchall()
    return [(int(r[0]), str(r[1])) for r in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify all approved recaps for a season.")
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument("--league", type=str, default="70985")
    parser.add_argument("--db", type=str, default=DB_PATH)
    args = parser.parse_args()

    weeks = _load_approved_weeks(args.db, args.league, args.season)
    if not weeks:
        print(f"No APPROVED recaps found for league={args.league} season={args.season}")
        sys.exit(1)

    print(f"Verifying {len(weeks)} approved recaps: league={args.league} season={args.season}")
    print("=" * 72)

    total_hard = 0
    total_soft = 0
    total_checks = 0
    weeks_passed = 0
    weeks_failed = 0
    hard_by_category: dict[str, int] = {}
    soft_by_category: dict[str, int] = {}

    for week_index, rendered_text in weeks:
        result = verify_recap_v1(
            rendered_text,
            db_path=args.db,
            league_id=args.league,
            season=args.season,
            week=week_index,
        )
        total_checks += result.checks_run

        has_hard = result.hard_failure_count > 0
        has_soft = result.soft_failure_count > 0

        if has_hard:
            weeks_failed += 1
            total_hard += result.hard_failure_count
            print(f"  Week {week_index:2d}: FAILED ({result.hard_failure_count} hard failure(s))")
            for f in result.hard_failures:
                hard_by_category[f.category] = hard_by_category.get(f.category, 0) + 1
                print(f"           [{f.category}] {f.claim}")
                print(f"            → {f.evidence}")
        else:
            weeks_passed += 1
            if has_soft:
                print(f"  Week {week_index:2d}: PASSED ({result.soft_failure_count} soft warning(s))")
            else:
                print(f"  Week {week_index:2d}: PASSED ({result.checks_run} checks)")

        if has_soft:
            total_soft += result.soft_failure_count
            for f in result.soft_failures:
                soft_by_category[f.category] = soft_by_category.get(f.category, 0) + 1
                if not has_hard:
                    # Only print soft details if no hard failures already printed
                    print(f"           [{f.category}] {f.claim}")

    print("=" * 72)
    print(f"Season summary: {weeks_passed} passed, {weeks_failed} failed out of {len(weeks)} weeks")
    print(f"Total checks: {total_checks}  |  Hard failures: {total_hard}  |  Soft warnings: {total_soft}")
    if hard_by_category:
        print(f"Hard by category: {', '.join(f'{k}={v}' for k, v in sorted(hard_by_category.items()))}")
    if soft_by_category:
        print(f"Soft by category: {', '.join(f'{k}={v}' for k, v in sorted(soft_by_category.items()))}")

    # ── Cross-week consistency check ──
    name_map = _load_franchise_names(args.db, args.league, args.season)
    reverse_name_map = _build_reverse_name_map(name_map)
    week_narratives = [
        (w, _extract_shareable_recap(t)) for w, t in weeks
    ]
    consistency_failures = verify_cross_week_consistency(
        week_narratives, reverse_name_map,
    )
    if consistency_failures:
        print()
        print(f"Cross-week consistency: {len(consistency_failures)} issue(s)")
        print("-" * 72)
        for f in consistency_failures:
            print(f"  [{f.category}] {f.claim}")
            print(f"   → {f.evidence}")
    else:
        print("\nCross-week consistency: no contradictions found.")


if __name__ == "__main__":
    main()
