#!/usr/bin/env python3
"""scripts/diagnose_score_verbatim_drift.py — read-only Step 0 probe for the
SCORE_VERBATIM legacy-drift carry-forward thread.

For each ``prompt_audit_reverify`` row with at least one ``SCORE_VERBATIM``
hard failure under the latest verifier tag, the probe classifies the row
across four buckets via per-matchup form analysis of the captured
``narrative_draft``:

  ALL_LEGACY_HYPHEN          every failing matchup has at least one
                              hyphen-form score string present in the prose.
                              Clean legacy drift; row was generated under
                              the OLD prompt+data layer (pre-Wave-1) and
                              the prose contains the legacy form.
  ALL_NO_SCORE                every failing matchup has zero score forms
                              (hyphen OR "to") in the prose. Score elision;
                              the model wrote about the matchup without
                              naming either decimal score.
  MIXED_LEGACY_AND_NO_SCORE   partial coverage — some matchups have hyphen
                              form, others have neither.
  POST_FIX_TO_PRESENT         a "to"-form is present somewhere in the prose
                              for a matchup the verifier nonetheless flagged.
                              Verifier-construction-impossible; would
                              indicate a probe bug or a verifier-helper
                              drift since the captured run.

Cross-tabs each bucket against the Wave 1 ship date (2026-05-03) on
``prompt_audit.captured_at`` to confirm the drift cohort is pre-Wave-1.
Any post-Wave-1 row in the failing set is a real-bug signal distinct from
legacy drift and warrants a separate investigation.

Usage:

    PYTHONPATH=src python scripts/diagnose_score_verbatim_drift.py \\
        --db .local_squadvault.sqlite

    # Optional: target a specific reverify tag.
    PYTHONPATH=src python scripts/diagnose_score_verbatim_drift.py \\
        --db .local_squadvault.sqlite --tag 59846b0
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass

# Wave 1 (Step 2 data layer change at ff613a9 — score format hyphen→"to")
# shipped 2026-05-03. Prompt-audit rows captured before this date contain
# prose generated under the OLD prompt+data layer; rows captured after have
# the new "to"-form prompt instruction. Compared as ISO-prefix string.
_WAVE_1_SHIPPED_DATE = "2026-05-03"

# Parse the canonical scores out of the verifier's evidence string.
# Format from recap_verifier_v1.py:1093-1098:
#   "Neither '107.65 to 65.40' nor '65.40 to 107.65' appears verbatim
#    in recap text. Canonical scores: 107.65 (winner) / 65.40 (loser)."
_EVIDENCE_SCORES_RE = re.compile(
    r"Canonical scores:\s*"
    r"(?P<winner>\d+\.\d{2})\s*\(winner\)\s*/\s*"
    r"(?P<loser>\d+\.\d{2})\s*\(loser\)"
)


@dataclass(frozen=True)
class FailingMatchup:
    """One canonical (winner_score, loser_score) pair the verifier flagged."""

    winner_score: float
    loser_score: float

    def to_form_winner(self) -> str:
        """Canonical post-Wave-1 form, winner-first."""
        return f"{self.winner_score:.2f} to {self.loser_score:.2f}"

    def to_form_loser(self) -> str:
        """Canonical post-Wave-1 form, loser-first."""
        return f"{self.loser_score:.2f} to {self.winner_score:.2f}"

    def hyphen_form_winner(self) -> str:
        """Legacy pre-Wave-1 form, winner-first."""
        return f"{self.winner_score:.2f}-{self.loser_score:.2f}"

    def hyphen_form_loser(self) -> str:
        """Legacy pre-Wave-1 form, loser-first."""
        return f"{self.loser_score:.2f}-{self.winner_score:.2f}"


@dataclass(frozen=True)
class MatchupForms:
    """Which canonical forms appear in the prose for one failing matchup."""

    to_winner: bool
    to_loser: bool
    hy_winner: bool
    hy_loser: bool

    @property
    def has_to(self) -> bool:
        return self.to_winner or self.to_loser

    @property
    def has_hy(self) -> bool:
        return self.hy_winner or self.hy_loser

    @property
    def has_any(self) -> bool:
        return self.has_to or self.has_hy


@dataclass(frozen=True)
class RowClassification:
    """Per-prompt-audit-row classification result."""

    audit_id: int
    captured_at: str
    season: int
    week_index: int
    attempt: int
    original_passed: int
    n_failing_matchups: int
    n_with_to: int
    n_with_hy: int
    n_without: int
    bucket: str


def _parse_scores_from_evidence(evidence: str) -> FailingMatchup | None:
    """Extract canonical (winner, loser) from the verifier's evidence string.

    Returns None if the string doesn't match the expected format — that
    would indicate verifier evidence-string drift since the captured run.
    """
    match = _EVIDENCE_SCORES_RE.search(evidence)
    if match is None:
        return None
    try:
        return FailingMatchup(
            winner_score=float(match.group("winner")),
            loser_score=float(match.group("loser")),
        )
    except ValueError:
        return None


def _classify_matchup_in_prose(mu: FailingMatchup, prose: str) -> MatchupForms:
    """Test each canonical form against substring presence in prose."""
    return MatchupForms(
        to_winner=mu.to_form_winner() in prose,
        to_loser=mu.to_form_loser() in prose,
        hy_winner=mu.hyphen_form_winner() in prose,
        hy_loser=mu.hyphen_form_loser() in prose,
    )


def _classify_row(per_matchup: list[MatchupForms]) -> tuple[str, int, int, int]:
    """Classify one row from its failing matchups' form presence.

    Returns (bucket, n_with_to, n_with_hy, n_without).
    """
    n_with_to = sum(1 for m in per_matchup if m.has_to)
    n_with_hy = sum(1 for m in per_matchup if m.has_hy)
    n_without = sum(1 for m in per_matchup if not m.has_any)

    # POST_FIX_TO_PRESENT is verifier-construction-impossible. If it fires,
    # something has drifted between the captured reverify and the current
    # codebase (e.g., the verifier helper changed and the captured failures
    # encode a different canonical form than the current helper would emit).
    # Surface it loudly rather than absorbing into ALL_LEGACY_HYPHEN.
    if n_with_to > 0:
        return ("POST_FIX_TO_PRESENT", n_with_to, n_with_hy, n_without)

    n = len(per_matchup)
    if n_with_hy == n:
        return ("ALL_LEGACY_HYPHEN", n_with_to, n_with_hy, n_without)
    if n_without == n:
        return ("ALL_NO_SCORE", n_with_to, n_with_hy, n_without)
    return ("MIXED_LEGACY_AND_NO_SCORE", n_with_to, n_with_hy, n_without)


def _resolve_tag(conn: sqlite3.Connection, tag_arg: str | None) -> str:
    """Return the verifier_tag to scan. Defaults to latest by reverified_at."""
    if tag_arg is not None:
        return tag_arg
    cur = conn.execute(
        "SELECT verifier_tag FROM prompt_audit_reverify "
        "ORDER BY reverified_at DESC LIMIT 1"
    )
    row = cur.fetchone()
    if row is None:
        sys.exit(
            "FATAL: prompt_audit_reverify is empty. Run reverify_prompt_audit.py "
            "first to populate reverify rows under the current verifier surface."
        )
    return str(row[0])


def _scan(db_path: str, tag: str | None) -> int:
    conn = sqlite3.connect(db_path)
    try:
        resolved_tag = _resolve_tag(conn, tag)

        print("=" * 78)
        print("  SCORE_VERBATIM LEGACY-DRIFT STEP 0 PROBE")
        print(f"  verifier_tag: {resolved_tag}")
        print(f"  Wave 1 ship date: {_WAVE_1_SHIPPED_DATE}")
        print("=" * 78)

        n_total = conn.execute(
            "SELECT COUNT(*) FROM prompt_audit_reverify WHERE verifier_tag = ?",
            (resolved_tag,),
        ).fetchone()[0]
        print(f"\n  Total reverify rows under tag: {n_total}")

        # Pull every reverify row that contains SCORE_VERBATIM in result_json.
        # The LIKE filter is a fast pre-filter; we re-validate via JSON parse
        # to avoid false positives (e.g. literal string in claim text).
        rows = conn.execute(
            """
            SELECT pa.id, pa.captured_at, pa.season, pa.week_index,
                   pa.attempt, pa.verification_passed, pa.narrative_draft,
                   r.result_json
              FROM prompt_audit_reverify r
              JOIN prompt_audit pa ON pa.id = r.prompt_audit_id
             WHERE r.verifier_tag = ?
               AND r.passed = 0
               AND r.result_json LIKE '%SCORE_VERBATIM%'
             ORDER BY pa.captured_at, pa.id
            """,
            (resolved_tag,),
        ).fetchall()

        classifications: list[RowClassification] = []
        bucket_counts: dict[str, int] = defaultdict(int)
        bucket_x_era_counts: dict[tuple[str, str], int] = defaultdict(int)
        season_week_pairs: set[tuple[int, int]] = set()
        unparseable_evidence_rows: list[int] = []
        total_failures_in_bucket: dict[str, int] = defaultdict(int)

        for (
            pa_id,
            captured_at,
            season,
            week,
            attempt,
            original_passed,
            draft,
            result_json,
        ) in rows:
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError:
                continue

            score_failures = [
                f
                for f in result.get("hard_failures", [])
                if f.get("category") == "SCORE_VERBATIM"
            ]
            if not score_failures:
                continue

            per_matchup: list[MatchupForms] = []
            for failure in score_failures:
                evidence = failure.get("evidence", "")
                mu = _parse_scores_from_evidence(evidence)
                if mu is None:
                    unparseable_evidence_rows.append(pa_id)
                    continue
                per_matchup.append(_classify_matchup_in_prose(mu, draft or ""))

            if not per_matchup:
                continue

            bucket, n_with_to, n_with_hy, n_without = _classify_row(per_matchup)
            era = "pre-Wave-1" if captured_at < _WAVE_1_SHIPPED_DATE else "post-Wave-1"

            bucket_counts[bucket] += 1
            bucket_x_era_counts[(bucket, era)] += 1
            season_week_pairs.add((season, week))
            total_failures_in_bucket[bucket] += len(per_matchup)

            classifications.append(
                RowClassification(
                    audit_id=pa_id,
                    captured_at=captured_at,
                    season=season,
                    week_index=week,
                    attempt=attempt,
                    original_passed=original_passed,
                    n_failing_matchups=len(per_matchup),
                    n_with_to=n_with_to,
                    n_with_hy=n_with_hy,
                    n_without=n_without,
                    bucket=bucket,
                )
            )

        # ── Output ──
        print(f"\n  Failing rows analysed: {len(classifications)}")
        print(f"  Distinct (season, week) pairs: {len(season_week_pairs)}")
        if unparseable_evidence_rows:
            print(
                f"  WARN: {len(unparseable_evidence_rows)} failures had "
                f"unparseable evidence strings (audit_ids: "
                f"{unparseable_evidence_rows[:5]}...)"
            )

        # Per-row table.
        print("\n  -- PER-ROW CLASSIFICATIONS --")
        print(
            f"\n  {'audit_id':>8}  {'captured_at':<25}  "
            f"{'S':>4}  {'Wk':>3}  {'A':>2}  "
            f"{'orig':>4}  {'#fail':>5}  "
            f"{'#to':>3}  {'#hy':>3}  {'#none':>5}  Bucket"
        )
        print(
            f"  {'-' * 8}  {'-' * 25}  {'-' * 4}  {'-' * 3}  "
            f"{'-' * 2}  {'-' * 4}  {'-' * 5}  "
            f"{'-' * 3}  {'-' * 3}  {'-' * 5}  {'-' * 30}"
        )
        for c in classifications:
            print(
                f"  {c.audit_id:>8}  {c.captured_at:<25}  "
                f"{c.season:>4}  {c.week_index:>3}  {c.attempt:>2}  "
                f"{c.original_passed:>4}  {c.n_failing_matchups:>5}  "
                f"{c.n_with_to:>3}  {c.n_with_hy:>3}  {c.n_without:>5}  "
                f"{c.bucket}"
            )

        # Bucket aggregate.
        print("\n  -- BUCKET COUNTS --")
        bucket_order = [
            "ALL_LEGACY_HYPHEN",
            "ALL_NO_SCORE",
            "MIXED_LEGACY_AND_NO_SCORE",
            "POST_FIX_TO_PRESENT",
        ]
        for bucket in bucket_order:
            n_rows = bucket_counts.get(bucket, 0)
            n_failures = total_failures_in_bucket.get(bucket, 0)
            print(
                f"    {bucket:<32}  rows={n_rows:>3}  "
                f"failures={n_failures:>4}"
            )

        # Era cross-tab.
        print("\n  -- BUCKET x ERA CROSS-TAB --")
        print(f"    (era boundary: captured_at < {_WAVE_1_SHIPPED_DATE})")
        print(f"\n    {'Bucket':<32}  {'pre-Wave-1':>10}  {'post-Wave-1':>11}")
        print(f"    {'-' * 32}  {'-' * 10}  {'-' * 11}")
        for bucket in bucket_order:
            pre_n = bucket_x_era_counts.get((bucket, "pre-Wave-1"), 0)
            post_n = bucket_x_era_counts.get((bucket, "post-Wave-1"), 0)
            print(f"    {bucket:<32}  {pre_n:>10}  {post_n:>11}")

        # Verdict.
        print("\n  -- VERDICT --")
        post_wave_1_n = sum(
            n for (_, era), n in bucket_x_era_counts.items() if era == "post-Wave-1"
        )
        post_wave_1_to_present = bucket_x_era_counts.get(
            ("POST_FIX_TO_PRESENT", "post-Wave-1"), 0
        )
        if post_wave_1_n == 0:
            print("  All failing rows are pre-Wave-1.")
            print("  CLEAN LEGACY DRIFT — every failure is in the pre-Wave-1 cohort.")
            print("  Direction 1 (acceptance memo + close) is supported by evidence.")
        elif post_wave_1_to_present == post_wave_1_n:
            print(f"  {post_wave_1_n} post-Wave-1 row(s) with POST_FIX_TO_PRESENT.")
            print("  Verifier or helper drift since reverify capture; investigate.")
        else:
            n_real = post_wave_1_n - post_wave_1_to_present
            print(f"  {n_real} post-Wave-1 row(s) NOT in POST_FIX_TO_PRESENT bucket.")
            print(
                "  Real-bug signal: model produced hyphen-form or no-score prose "
                "under post-Wave-1 prompt+format. Distinct from legacy drift; "
                "warrants separate investigation thread."
            )
    finally:
        conn.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Step 0 probe for SCORE_VERBATIM legacy drift."
    )
    parser.add_argument("--db", required=True, help="Path to .sqlite database.")
    parser.add_argument(
        "--tag",
        default=None,
        help=(
            "Reverify verifier_tag. Defaults to the latest tag in "
            "prompt_audit_reverify by reverified_at."
        ),
    )
    args = parser.parse_args(argv)
    return _scan(args.db, args.tag)


if __name__ == "__main__":
    sys.exit(main())
