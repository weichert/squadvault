#!/usr/bin/env python3
"""Streak verb diagnostic harness — Step 3.2 of the four-step playbook.

Adapts the score-thread `step_1_score_diagnostic_harness.py` pattern
(which lived in /tmp during the score thread and is reconstructed
here) to streak categories per
`_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`
§8.

For each prompt_audit row in scope, the harness:

1. Parses the rendered NARRATIVE ANGLES block for STREAK lines.
2. For each STREAK line, identifies the canonical phrasing
   (T1/T2/T3/T4 status, T5/T6 outcome detail, T8/T9/T10 record).
3. Classifies the corresponding claim in the model's narrative_draft:

   * VERBATIM   — the canonical headline appears as a substring of
     the prose. (Outcome details T5/T6 are checked separately;
     verbatim on either headline or outcome counts as VERBATIM for
     that claim.)
   * PARAPHRASE — the franchise is named in the prose, the streak
     fact is plausibly preserved, but the canonical phrasing is not
     verbatim. (Pluralization corrections like "have" → "has"
     count as PARAPHRASE — they are legitimate language fixes.)
   * INVERTED   — the franchise is named in the prose AND a streak
     claim of the opposite direction or wrong verb appears in a
     200-character window around the franchise mention. This is the
     load-bearing failure category for the streak thread.
   * OMITTED    — the franchise is not named in the prose at all.
     Silence is preferred over fabrication, so OMITTED is reported
     as a coverage measurement, not a failure.

The harness is helper-bound: canonical phrases come from
`streak_strings_v1.format_streak_*`, never hand-written. Per the V8
follow-up lesson, hand-written format expectations leak silent
regressions.

Usage:

    scripts/py scripts/step_1_streak_diagnostic_harness.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --scope last10-approved

    scripts/py scripts/step_1_streak_diagnostic_harness.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --scope week --season 2024 --week-index 13

    scripts/py scripts/step_1_streak_diagnostic_harness.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --scope week --season 2025 --week-index 13 --show-snippets

Outputs:

* Per-row table (prompt_audit.id, season, week, attempt, claim
  template, canonical phrase, classification, [optional] prose
  snippet around the relevant franchise name).
* Aggregate counts by classification, total claims, total rows.
* If `--show-snippets`: a short prose snippet for each non-VERBATIM
  classification, to support manual classification audit.

Exit code is always 0 — this is observational, not a gate.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# Add src/ to path so the helper module resolves when the harness is
# invoked from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from squadvault.core.recaps.render.streak_strings_v1 import (  # noqa: E402
    format_streak_marker,
    format_streak_outcome,
    format_streak_phrase,
    format_streak_record,
    format_streak_status,
)

# Reference the helpers so static analyzers don't drop the imports.
# Each is wired into the harness's classifier (canonical-phrase
# generation) or kept available for future-iteration extensions
# (e.g. per-template verbatim windows).
_HELPERS = (
    format_streak_marker,
    format_streak_outcome,
    format_streak_phrase,
    format_streak_record,
    format_streak_status,
)


# ── Data classes ────────────────────────────────────────────────────


@dataclass(frozen=True)
class StreakClaim:
    """A streak claim emitted into the angles block, derived for classification."""

    franchise_name: str
    template_id: str          # T1, T2, T3, T4, T8, T9, T10
    direction: str            # "win" or "loss"
    canonical_headline: str   # what the helper emits, verbatim
    canonical_outcome: str    # T5/T6 clause if present in the angle line, else ""


@dataclass(frozen=True)
class PromptAuditRow:
    id: int
    league_id: str
    season: int
    week_index: int
    attempt: int
    captured_at: str
    narrative_angles_text: str
    narrative_draft: str
    verification_passed: int


@dataclass(frozen=True)
class Classification:
    row_id: int
    season: int
    week_index: int
    attempt: int
    claim: StreakClaim
    category: str             # VERBATIM | PARAPHRASE | INVERTED | OMITTED
    snippet: str              # short prose excerpt around franchise mention


# ── Angle-block parsing ─────────────────────────────────────────────


# Match the rendered angle line shape, optionally:
#   "  [HEADLINE] [RE: Wolves] Wolves on 5-game win streak — Record: 7-1. Beat Bears this week — streak continues."
_LINE_PREFIX_RE = re.compile(
    r"^\s*\[(?:HEADLINE|NOTABLE|MINOR)\]"          # strength label
    r"(?:\s*\[RE:[^\]]*\])?"                        # optional attribution tag
    r"\s*(?P<body>.*)$"                             # body
)

# Streak templates. Each tuple: (compiled regex, template_id, direction).
# Patterns match the HEADLINE part only (post-detail-split).
_STREAK_TEMPLATES = [
    # T1: long-form winning  — "Wolves on 5-game win streak"
    (re.compile(r"^(?P<name>.+?) on (?P<n>\d+)-game win streak$"), "T1", "win"),
    # T3: long-form losing   — "Wolves on 5-game losing streak"
    (re.compile(r"^(?P<name>.+?) on (?P<n>\d+)-game losing streak$"), "T3", "loss"),
    # T2: short-form winning — "Wolves has won 3 straight"
    (re.compile(r"^(?P<name>.+?) has won 3 straight$"), "T2", "win"),
    # T4: short-form losing  — "Wolves has lost 3 straight"
    (re.compile(r"^(?P<name>.+?) has lost 3 straight$"), "T4", "loss"),
    # T8: tied/broke winning record
    (re.compile(r"^(?P<name>.+?) tied/broke the league win streak record \(\d+ games\)$"), "T8", "win"),
    # T9: 1 win from record
    (re.compile(r"^(?P<name>.+?) is 1 win from the league win streak record \(\d+\)$"), "T9", "win"),
    # T10: tied/broke losing record
    (re.compile(r"^(?P<name>.+?) tied/broke the league loss streak record \(\d+ games\)$"), "T10", "loss"),
]


def parse_streak_claims(angles_text: str) -> list[StreakClaim]:
    """Extract STREAK claims from rendered narrative_angles_text."""
    claims: list[StreakClaim] = []
    for raw_line in angles_text.split("\n"):
        m = _LINE_PREFIX_RE.match(raw_line)
        if not m:
            continue
        body = m.group("body")
        # Split headline from detail on first " — " (em-dash separator
        # used by lifecycle's angle renderer).
        if " \u2014 " in body:
            headline, detail = body.split(" \u2014 ", 1)
        else:
            headline, detail = body, ""

        # Match streak templates against the headline.
        for pattern, template_id, direction in _STREAK_TEMPLATES:
            mm = pattern.match(headline)
            if not mm:
                continue
            franchise = mm.group("name").strip()
            # Outcome clause (T5/T6) is appended to detail for T1/T2/T3/T4
            # streaks. Extract just the outcome portion if present —
            # detail format is "Record: W-L. Beat <opp> this week — streak continues."
            outcome_clause = ""
            if detail:
                # The outcome clause is everything after the first ". "
                # (record string ends with period, then space, then verb).
                if ". " in detail:
                    after_record = detail.split(". ", 1)[1]
                    # Verb-bearing minimum span per memo §4
                    if "streak continues" in after_record or "streak extended" in after_record:
                        outcome_clause = after_record.rstrip()
            claims.append(StreakClaim(
                franchise_name=franchise,
                template_id=template_id,
                direction=direction,
                canonical_headline=headline,
                canonical_outcome=outcome_clause,
            ))
            break
    return claims


# ── Classification ──────────────────────────────────────────────────


# Inversion signals — phrases that contradict the canonical direction.
_WIN_INVERSION_RE = re.compile(
    r"\b(losing streak|loss streak|snapped|on a (\d+)-game (?:loss|losing)|"
    r"lost (?:\d+|three) (?:in a row|straight|consecutive))\b",
    re.IGNORECASE,
)
_LOSS_INVERSION_RE = re.compile(
    r"\b(win streak|on a (\d+)-game win|winning streak|"
    r"won (?:\d+|three) (?:in a row|straight|consecutive))\b",
    re.IGNORECASE,
)


def _extract_window(prose: str, name: str, before: int = 100, after: int = 200) -> str:
    """Return prose centered on the first occurrence of `name`, or ''."""
    idx = prose.find(name)
    if idx < 0:
        return ""
    start = max(0, idx - before)
    end = min(len(prose), idx + len(name) + after)
    return prose[start:end]


def classify(claim: StreakClaim, prose: str) -> tuple[str, str]:
    """Classify a single claim against the model's prose.

    Returns (category, snippet). Snippet is empty for VERBATIM/OMITTED;
    for PARAPHRASE/INVERTED it's the 100-before-200-after window
    around the franchise mention.
    """
    # VERBATIM: canonical headline as substring of prose.
    if claim.canonical_headline in prose:
        return ("VERBATIM", "")
    # VERBATIM via outcome clause (T1-T4 with appended T5/T6 detail).
    # If the headline isn't verbatim but the outcome clause is, count
    # this as VERBATIM for the streak claim — the model has carried
    # the verb-bearing minimum span. Memo §4 designates these as the
    # "verbatim-required" windows.
    if claim.canonical_outcome and claim.canonical_outcome in prose:
        return ("VERBATIM", "")

    # OMITTED: franchise not in prose at all.
    if claim.franchise_name not in prose:
        return ("OMITTED", "")

    # Franchise mentioned, headline not verbatim. Test for inversion.
    window = _extract_window(prose, claim.franchise_name)
    if claim.direction == "win" and _WIN_INVERSION_RE.search(window):
        return ("INVERTED", window)
    if claim.direction == "loss" and _LOSS_INVERSION_RE.search(window):
        return ("INVERTED", window)

    # Mentioned, neither verbatim nor inverted → PARAPHRASE.
    return ("PARAPHRASE", window)


# ── DB access ───────────────────────────────────────────────────────


_SCHEMA_PROBE_SQL = """
SELECT pa.id, pa.league_id, pa.season, pa.week_index, pa.attempt,
       pa.captured_at, pa.narrative_angles_text, pa.narrative_draft,
       pa.verification_passed
  FROM prompt_audit pa
"""


def fetch_rows_last10_approved(conn: sqlite3.Connection, league_id: str) -> list[PromptAuditRow]:
    """Last 10 APPROVED recaps cross-season; return the audit row whose
    captured_at most closely precedes each artifact's created_at."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, season, week_index, created_at
          FROM recap_artifacts
         WHERE league_id = ?
           AND state = 'APPROVED'
           AND artifact_type = 'WEEKLY_RECAP'
         ORDER BY created_at DESC
         LIMIT 10
        """,
        (league_id,),
    )
    artifacts = cur.fetchall()
    rows: list[PromptAuditRow] = []
    for _aid, season, week_index, created_at in artifacts:
        cur.execute(
            _SCHEMA_PROBE_SQL
            + " WHERE pa.league_id = ? AND pa.season = ? AND pa.week_index = ? "
              "AND pa.captured_at <= ? "
              "ORDER BY pa.captured_at DESC, pa.attempt DESC LIMIT 1",
            (league_id, season, week_index, created_at),
        )
        r = cur.fetchone()
        if r is not None:
            rows.append(PromptAuditRow(*r))
    return rows


def fetch_rows_week(
    conn: sqlite3.Connection, league_id: str, season: int, week_index: int
) -> list[PromptAuditRow]:
    """All prompt_audit rows for a single (league, season, week)."""
    cur = conn.cursor()
    cur.execute(
        _SCHEMA_PROBE_SQL
        + " WHERE pa.league_id = ? AND pa.season = ? AND pa.week_index = ? "
          "ORDER BY pa.id ASC",
        (league_id, season, week_index),
    )
    return [PromptAuditRow(*r) for r in cur.fetchall()]


# ── Output ──────────────────────────────────────────────────────────


def print_per_row(classifications: list[Classification], show_snippets: bool) -> None:
    print(
        "id\tseason\tweek\tattempt\ttemplate\tdirection\tcategory\tcanonical_headline"
    )
    for c in classifications:
        print(
            f"{c.row_id}\t{c.season}\t{c.week_index}\t{c.attempt}\t"
            f"{c.claim.template_id}\t{c.claim.direction}\t{c.category}\t"
            f"{c.claim.canonical_headline}"
        )
        if show_snippets and c.category in ("PARAPHRASE", "INVERTED") and c.snippet:
            snippet = c.snippet.replace("\n", " \u23CE ")
            print(f"    snippet: ...{snippet}...")


def print_aggregate(classifications: list[Classification]) -> None:
    cats = Counter(c.category for c in classifications)
    total = len(classifications)
    print()
    print("=== AGGREGATE ===")
    print(f"Total claims: {total}")
    if total == 0:
        print("(no STREAK claims detected — empty scope or angle parsing miss)")
        return
    for cat in ("VERBATIM", "PARAPHRASE", "INVERTED", "OMITTED"):
        count = cats.get(cat, 0)
        pct = (100.0 * count / total) if total else 0.0
        print(f"  {cat:11s}: {count:4d}  ({pct:5.1f}%)")
    # Per-template breakdown
    print()
    print("=== PER-TEMPLATE ===")
    by_template: dict[str, Counter] = {}
    for c in classifications:
        by_template.setdefault(c.claim.template_id, Counter())[c.category] += 1
    for template_id in sorted(by_template):
        tcounter = by_template[template_id]
        ttotal = sum(tcounter.values())
        line_parts = [f"{template_id} (n={ttotal})"]
        for cat in ("VERBATIM", "PARAPHRASE", "INVERTED", "OMITTED"):
            count = tcounter.get(cat, 0)
            line_parts.append(f"{cat[0]}={count}")
        print("  " + "  ".join(line_parts))


# ── CLI ─────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Step 3.2 streak verb diagnostic harness."
    )
    parser.add_argument("--db", required=True, help="Path to .sqlite database.")
    parser.add_argument("--league-id", required=True, help="League ID, e.g. 70985.")
    parser.add_argument(
        "--scope",
        required=True,
        choices=("last10-approved", "week"),
        help="Scope selector.",
    )
    parser.add_argument("--season", type=int, default=None, help="Required for --scope week.")
    parser.add_argument("--week-index", type=int, default=None, help="Required for --scope week.")
    parser.add_argument(
        "--show-snippets",
        action="store_true",
        help="Print prose snippets for non-VERBATIM classifications.",
    )
    args = parser.parse_args(argv)

    if args.scope == "week" and (args.season is None or args.week_index is None):
        parser.error("--scope week requires --season and --week-index.")

    conn = sqlite3.connect(args.db)
    conn.row_factory = None
    try:
        if args.scope == "last10-approved":
            rows = fetch_rows_last10_approved(conn, args.league_id)
        else:
            rows = fetch_rows_week(conn, args.league_id, args.season, args.week_index)
    finally:
        conn.close()

    classifications: list[Classification] = []
    for row in rows:
        for claim in parse_streak_claims(row.narrative_angles_text):
            category, snippet = classify(claim, row.narrative_draft)
            classifications.append(Classification(
                row_id=row.id,
                season=row.season,
                week_index=row.week_index,
                attempt=row.attempt,
                claim=claim,
                category=category,
                snippet=snippet,
            ))

    print_per_row(classifications, show_snippets=args.show_snippets)
    print_aggregate(classifications)
    return 0


if __name__ == "__main__":
    sys.exit(main())
