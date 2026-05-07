"""NOTABLE-saturation probe — read-only diagnostic for budget-loop behavior.

Per session brief at `_observations/session_brief_notable_saturation.md`
(commit `67aca15`) and Step 0b memo at `fa880f6`. This probe characterizes
*current* draft-pipeline NOTABLE budget behavior under current detector
code and current canonical data. It does NOT characterize historical
publication behavior — see Step 0b Findings 5-6 for why.

For each (season, week_index) in 2024-2025 with prompt_audit rows, the
probe selects the most-recent row (per Finding 6: latest captured_at
reflects latest detector-code snapshot) and reports:

    notable_count          : count of [NOTABLE] lines in narrative_angles_text
    notable_saturated      : (notable_count == 6)
    headline_count         : count of [HEADLINE] lines
    minor_count            : count of [MINOR] lines (visible; "+ N omitted" not parsed)
    angles_categories      : set of categories from angles_summary_json
    budgeted_categories    : set of categories from budgeted_summary_json
    evicted_categories     : angles minus budgeted (lost to budget loop)
    streak_in_angles       : True if STREAK present in angles_summary
    streak_in_budgeted     : True if STREAK present in budgeted_summary
    streak_evicted         : streak_in_angles AND NOT streak_in_budgeted
    bucket                 : NOTABLE_SATURATED_WITH_STREAK_EVICTED
                           | NOTABLE_SATURATED_NO_STREAK_EVICTED
                           | NOTABLE_NOT_SATURATED

Output is written to /tmp/notable_saturation_probe_output.txt.

Caveats:
- streak_evicted does not distinguish strength-2 (NOTABLE-tier) eviction
  from strength-1 (MINOR-tier) eviction. Without re-running detectors to
  recover strength info, this conflation cannot be resolved from existing
  prompt_audit data.
- Probe analyzes the latest prompt_audit row per (season, week). For
  weeks with multiple regen runs, earlier runs (with potentially
  different detector code) are not represented. This is intentional:
  the brief's mechanism re-derivation operates on current code, and
  current-code behavior is what direction-choice should respond to.
- No claim is made about what the published recap contained. Historical
  publications pre-date prompt_audit instrumentation (Step 0b Finding 5).
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DB_PATH = ".local_squadvault.sqlite"
OUTPUT_PATH = "/tmp/notable_saturation_probe_output.txt"

TIER_PATTERN = re.compile(r"^\s*\[(HEADLINE|NOTABLE|MINOR)\]", re.MULTILINE)


def _parse_tier_counts(narrative_angles_text: str) -> tuple[int, int, int]:
    """Count [HEADLINE], [NOTABLE], [MINOR] lines in narrative_angles_text."""
    headline = 0
    notable = 0
    minor = 0
    for match in TIER_PATTERN.finditer(narrative_angles_text):
        tier = match.group(1)
        if tier == "HEADLINE":
            headline += 1
        elif tier == "NOTABLE":
            notable += 1
        elif tier == "MINOR":
            minor += 1
    return headline, notable, minor


def _categories_from_summary(summary_json: str) -> set[str]:
    """Extract set of categories from angles_summary_json or budgeted_summary_json."""
    try:
        data = json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        return set()
    return {entry.get("category", "") for entry in data if isinstance(entry, dict)}


def _categories_counter_from_summary(summary_json: str) -> Counter:
    """Multiset of categories — for cap-pressure analysis."""
    try:
        data = json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        return Counter()
    return Counter(entry.get("category", "") for entry in data if isinstance(entry, dict))


def _classify_bucket(notable_saturated: bool, streak_evicted: bool) -> str:
    if not notable_saturated:
        return "NOTABLE_NOT_SATURATED"
    if streak_evicted:
        return "NOTABLE_SATURATED_WITH_STREAK_EVICTED"
    return "NOTABLE_SATURATED_NO_STREAK_EVICTED"


def main() -> int:
    if not Path(DB_PATH).exists():
        print(f"ERROR: database not found at {DB_PATH}", file=sys.stderr)
        return 1

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Get all (season, week_index) pairs with prompt_audit rows in 2024-2025,
    # selecting the most-recent row per pair (latest captured_at).
    cur.execute(
        """
        SELECT pa.id, pa.season, pa.week_index, pa.captured_at,
               pa.attempt, pa.verification_passed,
               pa.narrative_angles_text,
               pa.angles_summary_json,
               pa.budgeted_summary_json
        FROM prompt_audit pa
        INNER JOIN (
            SELECT season, week_index, MAX(captured_at) AS max_captured
            FROM prompt_audit
            WHERE season IN (2024, 2025)
            GROUP BY season, week_index
        ) latest
            ON pa.season = latest.season
            AND pa.week_index = latest.week_index
            AND pa.captured_at = latest.max_captured
        WHERE pa.season IN (2024, 2025)
        ORDER BY pa.season, pa.week_index
        """
    )
    rows = cur.fetchall()

    bucket_counts: Counter = Counter()
    evicted_category_counter: Counter = Counter()
    saturated_with_streak_weeks: list[tuple[int, int, int]] = []
    saturated_without_streak_weeks: list[tuple[int, int]] = []

    output_lines: list[str] = []
    output_lines.append("=" * 80)
    output_lines.append("NOTABLE-saturation probe output")
    output_lines.append("Brief: _observations/session_brief_notable_saturation.md (67aca15)")
    output_lines.append("Step 0b memo: fa880f6")
    output_lines.append("Scope: current draft-pipeline behavior, not historical publication")
    output_lines.append("=" * 80)
    output_lines.append("")
    output_lines.append(f"Total weeks analyzed: {len(rows)}")
    output_lines.append("")

    output_lines.append("Per-week classification:")
    output_lines.append("")
    output_lines.append(
        f"{'season':>6}  {'week':>4}  {'pa_id':>5}  {'attempt':>7}  "
        f"{'verified':>8}  {'H':>2}  {'N':>2}  {'M':>2}  "
        f"{'sat':>3}  {'streak_evict':>12}  bucket"
    )
    output_lines.append("-" * 100)

    for row in rows:
        pa_id = row["id"]
        season = row["season"]
        week = row["week_index"]
        attempt = row["attempt"]
        verified = row["verification_passed"]
        nat = row["narrative_angles_text"] or ""
        angles_json = row["angles_summary_json"] or "[]"
        budgeted_json = row["budgeted_summary_json"] or "[]"

        h_count, n_count, m_count = _parse_tier_counts(nat)
        notable_saturated = (n_count == 6)

        angles_cats = _categories_from_summary(angles_json)
        budgeted_cats = _categories_from_summary(budgeted_json)
        evicted_cats = angles_cats - budgeted_cats

        streak_in_angles = "STREAK" in angles_cats
        streak_in_budgeted = "STREAK" in budgeted_cats
        streak_evicted = streak_in_angles and not streak_in_budgeted

        bucket = _classify_bucket(notable_saturated, streak_evicted)
        bucket_counts[bucket] += 1

        if notable_saturated and streak_evicted:
            saturated_with_streak_weeks.append((season, week, pa_id))
        elif notable_saturated:
            saturated_without_streak_weeks.append((season, week))

        for cat in evicted_cats:
            evicted_category_counter[cat] += 1

        sat_marker = "YES" if notable_saturated else "no"
        evict_marker = "YES" if streak_evicted else "no"

        output_lines.append(
            f"{season:>6}  {week:>4}  {pa_id:>5}  {attempt:>7}  "
            f"{verified:>8}  {h_count:>2}  {n_count:>2}  {m_count:>2}  "
            f"{sat_marker:>3}  {evict_marker:>12}  {bucket}"
        )

    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("Bucket totals")
    output_lines.append("=" * 80)
    for bucket in [
        "NOTABLE_SATURATED_WITH_STREAK_EVICTED",
        "NOTABLE_SATURATED_NO_STREAK_EVICTED",
        "NOTABLE_NOT_SATURATED",
    ]:
        count = bucket_counts.get(bucket, 0)
        output_lines.append(f"  {bucket}: {count}")
    output_lines.append("")

    output_lines.append("=" * 80)
    output_lines.append("NOTABLE_SATURATED_WITH_STREAK_EVICTED weeks (the brief's failure mode)")
    output_lines.append("=" * 80)
    if saturated_with_streak_weeks:
        for season, week, pa_id in saturated_with_streak_weeks:
            output_lines.append(f"  ({season}, week={week}, pa_id={pa_id})")
    else:
        output_lines.append("  (none)")
    output_lines.append("")

    output_lines.append("=" * 80)
    output_lines.append("NOTABLE_SATURATED_NO_STREAK_EVICTED weeks (saturation without integrity-loss)")
    output_lines.append("=" * 80)
    if saturated_without_streak_weeks:
        for season, week in saturated_without_streak_weeks:
            output_lines.append(f"  ({season}, week={week})")
    else:
        output_lines.append("  (none)")
    output_lines.append("")

    output_lines.append("=" * 80)
    output_lines.append("Top 10 most-evicted categories (across all weeks)")
    output_lines.append("=" * 80)
    for cat, count in evicted_category_counter.most_common(10):
        output_lines.append(f"  {cat}: {count}")
    output_lines.append("")

    output_lines.append("=" * 80)
    output_lines.append("Brief evidence-gate disposition (per brief Step 0 evidence gate)")
    output_lines.append("=" * 80)
    saturated_with_streak_count = bucket_counts.get(
        "NOTABLE_SATURATED_WITH_STREAK_EVICTED", 0
    )
    distinct_weeks = len({(s, w) for s, w, _ in saturated_with_streak_weeks})
    output_lines.append(
        f"  NOTABLE_SATURATED_WITH_STREAK_EVICTED count: {saturated_with_streak_count}"
    )
    output_lines.append(f"  Distinct weeks: {distinct_weeks}")
    output_lines.append("")
    if distinct_weeks >= 2:
        output_lines.append("  Editorial-tier gate: PASS (>= 2 distinct weeks)")
        output_lines.append("  Recommendation: ship Step 1 per brief")
    elif distinct_weeks == 1:
        output_lines.append("  Defer-tier: single specimen in already-processed corpus")
        output_lines.append("  Recommendation: defer Step 1; Steve elects per brief preamble")
    else:
        output_lines.append("  No NOTABLE_SATURATED_WITH_STREAK_EVICTED weeks found")
        output_lines.append("  Recommendation: thread does not have empirical support; reconsider")
    output_lines.append("")

    output_lines.append("=" * 80)
    output_lines.append("End of probe output")
    output_lines.append("=" * 80)

    Path(OUTPUT_PATH).write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"Probe output written to {OUTPUT_PATH}")
    print(f"Total weeks analyzed: {len(rows)}")
    for bucket in [
        "NOTABLE_SATURATED_WITH_STREAK_EVICTED",
        "NOTABLE_SATURATED_NO_STREAK_EVICTED",
        "NOTABLE_NOT_SATURATED",
    ]:
        count = bucket_counts.get(bucket, 0)
        print(f"  {bucket}: {count}")

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
