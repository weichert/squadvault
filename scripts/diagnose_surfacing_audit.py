#!/usr/bin/env python3
"""Writing Room Surfacing Audit — diagnostic script (read-only).

Traces where narrative angles get dropped between Signal Scout detection
and budget selection, answering the Phase 10 Observation v3 question:
"between Signal Scout intake and recap_artifacts.rendered_text, where
do D4 and D49 angles get dropped?"

Reads prompt_audit rows and computes per-detector:
  - Total detected (appeared in angles_summary_json)
  - Total budgeted (appeared in budgeted_summary_json)
  - Budget rate (budgeted / detected)
  - Strength distribution for dropped detectors

Output: summary tables to stdout + detailed CSV to /tmp/.

Read-only: no DB writes, no LLM calls, no external API contact.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ── Helpers ──────────────────────────────────────────────────────────


def _parse_summary(raw: str) -> list[dict]:
    """Parse an angles_summary_json or budgeted_summary_json string."""
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except (ValueError, TypeError):
        pass
    return []


def _cat_to_detector(entries: list[dict]) -> Counter[str]:
    """Count detector occurrences in a summary list."""
    c: Counter[str] = Counter()
    for entry in entries:
        det = entry.get("detector", "UNMAPPED")
        c[det] += 1
    return c


def _cat_counter(entries: list[dict]) -> Counter[str]:
    """Count category occurrences in a summary list."""
    c: Counter[str] = Counter()
    for entry in entries:
        cat = entry.get("category", "UNKNOWN")
        c[cat] += 1
    return c


# ── Main ─────────────────────────────────────────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(
        description="Writing Room surfacing audit (diagnostic, read-only)."
    )
    p.add_argument("--db", required=True, help="Path to SQLite database")
    p.add_argument("--league-id", default="70985")
    p.add_argument(
        "--season", type=int, action="append", dest="seasons",
        help="Season(s) to audit (repeatable). Default: all available.",
    )
    p.add_argument(
        "--attempt", type=int, default=1,
        help="Filter to this attempt number (default: 1, the initial detection).",
    )
    p.add_argument(
        "--csv-out", default="/tmp/surfacing_audit.csv",
        help="Path for detailed per-row CSV output.",
    )
    args = p.parse_args()

    from squadvault.core.storage.session import DatabaseSession

    # ── Load prompt_audit rows ───────────────────────────────────────

    sql = """
        SELECT id, captured_at, season, week_index, attempt,
               angles_summary_json, budgeted_summary_json,
               verification_passed, narrative_angles_text
        FROM prompt_audit
        WHERE league_id = ?
    """
    params: list = [args.league_id]

    if args.seasons:
        placeholders = ",".join("?" for _ in args.seasons)
        sql += f" AND season IN ({placeholders})"
        params.extend(args.seasons)

    if args.attempt is not None:
        sql += " AND attempt = ?"
        params.append(args.attempt)

    sql += " ORDER BY season, week_index, attempt, id"

    with DatabaseSession(args.db) as con:
        rows = con.execute(sql, params).fetchall()

    if not rows:
        print("No prompt_audit rows found for the given filters.", file=sys.stderr)
        return 1

    print(f"Loaded {len(rows)} prompt_audit rows "
          f"(league={args.league_id}, attempt={args.attempt})")
    print()

    # ── Per-detector aggregation ─────────────────────────────────────

    # Aggregate across all rows
    detected_by_det: Counter[str] = Counter()    # detector → total detected
    budgeted_by_det: Counter[str] = Counter()    # detector → total budgeted
    detected_by_cat: Counter[str] = Counter()    # category → total detected
    budgeted_by_cat: Counter[str] = Counter()    # category → total budgeted

    # Per-row detail for CSV
    csv_rows: list[dict] = []

    # Budget composition tracking
    budget_sizes: list[int] = []
    detected_sizes: list[int] = []

    # Per-week: which detectors are budgeted
    weeks_with_detector_budgeted: defaultdict[str, int] = defaultdict(int)
    total_weeks = 0

    # Per-(season, week) cache for the BUDGET-dropped drill-down.
    # Keyed on (season, week) so we can look up what was budgeted and
    # which [MINOR] lines the prompt showed for any week a void
    # category was detected.
    week_cache: dict[tuple[int, int], dict] = {}

    for row in rows:
        (row_id, captured_at, season, week, attempt,
         ang_json, bud_json, vpass, narr_text) = row

        detected = _parse_summary(ang_json)
        budgeted = _parse_summary(bud_json)

        det_counts = _cat_to_detector(detected)
        bud_counts = _cat_to_detector(budgeted)
        cat_detected = _cat_counter(detected)
        cat_budgeted = _cat_counter(budgeted)

        detected_by_det += det_counts
        budgeted_by_det += bud_counts
        detected_by_cat += cat_detected
        budgeted_by_cat += cat_budgeted

        detected_sizes.append(len(detected))
        budget_sizes.append(len(budgeted))
        total_weeks += 1

        for det in bud_counts:
            weeks_with_detector_budgeted[det] += 1

        # CSV detail
        csv_rows.append({
            "id": row_id,
            "season": season,
            "week": week,
            "attempt": attempt,
            "detected_count": len(detected),
            "budgeted_count": len(budgeted),
            "verification_passed": vpass,
            "detected_detectors": json.dumps(dict(det_counts), sort_keys=True),
            "budgeted_detectors": json.dumps(dict(bud_counts), sort_keys=True),
            "detected_categories": json.dumps(dict(cat_detected), sort_keys=True),
            "budgeted_categories": json.dumps(dict(cat_budgeted), sort_keys=True),
        })

        # Cache for BUDGET-dropped drill-down. Last write wins if a
        # (season, week) appears in multiple rows; attempt filter
        # (default 1) ensures this is already one row per week in the
        # common case.
        week_cache[(season, week)] = {
            "cat_detected": cat_detected,
            "cat_budgeted": cat_budgeted,
            "budgeted_detectors_list": [
                e.get("detector", "UNMAPPED") for e in budgeted
            ],
            "budgeted_categories_list": [
                e.get("category", "UNKNOWN") for e in budgeted
            ],
            "narrative_angles_text": narr_text or "",
            "attempt": attempt,
        }

    # ── Summary: budget composition ──────────────────────────────────

    print("=" * 70)
    print("BUDGET COMPOSITION SUMMARY")
    print("=" * 70)
    avg_detected = sum(detected_sizes) / len(detected_sizes) if detected_sizes else 0
    avg_budgeted = sum(budget_sizes) / len(budget_sizes) if budget_sizes else 0
    print(f"  Rows analyzed:     {total_weeks}")
    print(f"  Avg detected:      {avg_detected:.1f} angles/week")
    print(f"  Avg budgeted:      {avg_budgeted:.1f} angles/week")
    print(f"  Budget range:      {min(budget_sizes)}–{max(budget_sizes)}")
    print(f"  Detected range:    {min(detected_sizes)}–{max(detected_sizes)}")
    print()

    # ── Summary: per-detector surfacing rates ────────────────────────

    all_detectors = sorted(set(detected_by_det.keys()) | set(budgeted_by_det.keys()))

    print("=" * 70)
    print("PER-DETECTOR SURFACING RATES")
    print("=" * 70)
    print(f"{'Detector':<8} {'Detected':>10} {'Budgeted':>10} {'Rate':>8} {'Weeks':>8}")
    print("-" * 50)

    void_detectors: list[tuple[str, int]] = []

    for det in all_detectors:
        d = detected_by_det[det]
        b = budgeted_by_det[det]
        rate = f"{b/d*100:.0f}%" if d > 0 else "n/a"
        weeks = weeks_with_detector_budgeted.get(det, 0)
        print(f"{det:<8} {d:>10} {b:>10} {rate:>8} {weeks:>6}/{total_weeks}")

        if d > 0 and b == 0:
            void_detectors.append((det, d))

    print()

    # ── Summary: per-category surfacing rates ────────────────────────

    all_cats = sorted(set(detected_by_cat.keys()) | set(budgeted_by_cat.keys()))

    print("=" * 70)
    print("PER-CATEGORY SURFACING RATES")
    print("=" * 70)
    print(f"{'Category':<35} {'Detected':>10} {'Budgeted':>10} {'Rate':>8}")
    print("-" * 67)

    for cat in all_cats:
        d = detected_by_cat[cat]
        b = budgeted_by_cat[cat]
        rate = f"{b/d*100:.0f}%" if d > 0 else "n/a"
        marker = " ◀ VOID" if d > 5 and b == 0 else ""
        print(f"{cat:<35} {d:>10} {b:>10} {rate:>8}{marker}")

    print()

    # ── Surfacing void summary ───────────────────────────────────────

    if void_detectors:
        print("=" * 70)
        print("SURFACING VOID — detectors with 0% budget rate")
        print("=" * 70)
        for det, count in sorted(void_detectors, key=lambda x: -x[1]):
            # Find the categories for this detector
            cats = [cat for cat in all_cats
                    if any(e.get("detector") == det
                           for row in rows
                           for e in _parse_summary(row[5])
                           if e.get("category") == cat)]
            print(f"  {det}: {count} detections, 0 budgeted")
            if cats:
                for cat in cats:
                    print(f"    └ {cat}: {detected_by_cat[cat]} detected")
        print()
    else:
        print("No surfacing void detected — all firing detectors have >0 budget rate.")
        print()

    # ── Per-week BUDGET-dropped drill-down ───────────────────────────
    #
    # For each category flagged ◀ VOID (detected > 5, budgeted == 0),
    # list every (season, week) where it was detected, dump the full
    # budgeted categories for that week, and extract the [MINOR]-tagged
    # lines from narrative_angles_text. This is the empirical
    # "what displaced us" evidence the D12 Finding 1 resolution
    # established as the canonical way to verify a BUDGET drop stage.

    void_categories = sorted(
        cat for cat in all_cats
        if detected_by_cat[cat] > 5 and budgeted_by_cat[cat] == 0
    )

    if void_categories:
        print("=" * 70)
        print("BUDGET-DROPPED WEEK DETAIL — per void category")
        print("=" * 70)
        print("For each ◀ VOID category, every (season, week) where it was")
        print("detected but not budgeted. Shows the full budgeted-categories")
        print("list and the [MINOR]-tagged lines that consumed the 4 MINOR")
        print("slots in place of the void category. Establishes the drop")
        print("stage empirically per the D12 Finding 1 precedent.")
        print()

        # Aggregate tally: across all void-category drop events, which
        # other categories most often appeared in those same budgets?
        displacer_counter: Counter[str] = Counter()

        for cat in void_categories:
            # Find all (season, week) tuples where this category was detected.
            hit_weeks = sorted(
                (s, w) for (s, w), info in week_cache.items()
                if info["cat_detected"].get(cat, 0) > 0
            )
            total_detections = sum(
                info["cat_detected"].get(cat, 0)
                for (s, w), info in week_cache.items()
            )

            print(f"── {cat} ── detected on {len(hit_weeks)} weeks, "
                  f"{total_detections} total instances, 0 budgeted")
            print()

            for (s, w) in hit_weeks:
                info = week_cache[(s, w)]
                n_detected = info["cat_detected"].get(cat, 0)
                budgeted_cats = info["budgeted_categories_list"]
                print(f"  • {s} W{w:<2}  ({n_detected} detections this week, "
                      f"attempt={info['attempt']})")
                print(f"    budgeted ({len(budgeted_cats)}): "
                      f"{', '.join(budgeted_cats)}")

                # Extract [MINOR] lines from narrative_angles_text. The
                # format is set by weekly_recap_lifecycle.py:815 —
                # "  [MINOR][RE: <fnames>] <headline> — <detail>"
                narr = info["narrative_angles_text"]
                minor_lines = [
                    ln.strip() for ln in narr.splitlines() if "[MINOR]" in ln
                ]
                if minor_lines:
                    print(f"    [MINOR] slots ({len(minor_lines)}):")
                    for ml in minor_lines:
                        print(f"      {ml}")
                else:
                    print("    [MINOR] slots: (none visible in narrative text)")

                # Tally for the aggregate "who displaced the voids" table
                for bc in budgeted_cats:
                    displacer_counter[bc] += 1
                print()

        # Aggregate displacer table
        print("=" * 70)
        print("DISPLACER AGGREGATE — categories most often budgeted on weeks")
        print("where a void category was detected-but-dropped")
        print("=" * 70)
        print("(Counts across all void-category drop events. A category")
        print(" listed here was present in the budget of at least one week")
        print(" where a void category was detected and not budgeted.)")
        print()
        print(f"{'Category':<35} {'Times in budget':>18}")
        print("-" * 55)
        for cat, n in displacer_counter.most_common(25):
            print(f"{cat:<35} {n:>18}")
        print()

    # ── Write CSV ────────────────────────────────────────────────────

    csv_path = Path(args.csv_out)
    if csv_rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"Detailed per-row CSV written to: {csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
