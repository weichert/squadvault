"""Re-verify captured prompt_audit drafts through the current verifier.

Iterates every prompt_audit row for a league, runs verify_recap_v1
against the stored narrative_draft, and writes results to the
prompt_audit_reverify sidecar table. Prints a 4-way delta summary
comparing new results against original verification_passed captures.

The 4-way delta is the merge gate for verifier code changes:
  still-pass:  original passed, reverify passed
  still-fail:  original failed, reverify failed
  fail→pass:   original failed, reverify passed
  pass→fail:   original passed, reverify failed  ← must be 0

When --baseline-tag is provided, the script additionally computes
per-category hard-failure counts for both the current and baseline
verifier tags and shifts the regression verdict from row-level
pass→fail to category-NEW. This codifies the merge-gate technique
captured in earlier observation memos: legacy-drift row counts
fluctuate but a category appearing at zero failures in baseline and
>0 in current indicates genuine new failure surface.

Usage:
    scripts/py scripts/reverify_prompt_audit.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --verifier-tag $(git rev-parse --short HEAD)

    # With baseline comparison (merge-gate use case):
    scripts/py scripts/reverify_prompt_audit.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --verifier-tag $(git rev-parse --short HEAD) \\
        --baseline-tag <prior-tag>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from squadvault.core.recaps.verification.recap_verifier_v1 import (
    VerificationResult,
    verify_recap_v1,
)
from squadvault.core.storage.session import DatabaseSession

DB_PATH = ".local_squadvault.sqlite"

_CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS prompt_audit_reverify (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_audit_id       INTEGER NOT NULL,
    reverified_at         TEXT    NOT NULL,
    verifier_tag          TEXT    NOT NULL,
    passed                INTEGER NOT NULL,
    hard_failure_count    INTEGER NOT NULL,
    soft_failure_count    INTEGER NOT NULL,
    result_json           TEXT    NOT NULL,
    FOREIGN KEY (prompt_audit_id) REFERENCES prompt_audit(id)
);
"""

_CREATE_INDEX_SOURCE_SQL = """\
CREATE INDEX IF NOT EXISTS idx_reverify_source
    ON prompt_audit_reverify (prompt_audit_id);
"""

_CREATE_INDEX_TAG_SQL = """\
CREATE INDEX IF NOT EXISTS idx_reverify_tag
    ON prompt_audit_reverify (verifier_tag);
"""


def _ensure_table(db_path: str) -> None:
    """Create prompt_audit_reverify table and indexes if absent."""
    with DatabaseSession(db_path) as con:
        con.executescript(
            _CREATE_TABLE_SQL + _CREATE_INDEX_SOURCE_SQL + _CREATE_INDEX_TAG_SQL
        )


def _result_to_json(result: VerificationResult) -> str:
    """Serialize a VerificationResult to the canonical JSON shape."""
    return json.dumps(
        {
            "passed": result.passed,
            "hard_failures": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "claim": f.claim,
                    "evidence": f.evidence,
                }
                for f in result.hard_failures
            ],
            "soft_failures": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "claim": f.claim,
                    "evidence": f.evidence,
                }
                for f in result.soft_failures
            ],
            "checks_run": result.checks_run,
        },
        indent=None,
    )


def _category_counts_for_tag(db_path: str, tag: str) -> dict[str, int]:
    """Return {category: count} of hard_failures across all reverify rows for tag."""
    with DatabaseSession(db_path) as con:
        cur = con.execute(
            """SELECT json_extract(je.value, '$.category') AS cat,
                      COUNT(*) AS n
               FROM prompt_audit_reverify r,
                    json_each(r.result_json, '$.hard_failures') je
               WHERE r.verifier_tag = ?
               GROUP BY cat""",
            (tag,),
        )
        return {row[0]: row[1] for row in cur.fetchall() if row[0] is not None}


def _validate_baseline_tag_exists(db_path: str, baseline_tag: str) -> None:
    """Exit with helpful error if baseline_tag has no reverify rows."""
    with DatabaseSession(db_path) as con:
        cur = con.execute(
            "SELECT COUNT(*) FROM prompt_audit_reverify WHERE verifier_tag = ?",
            (baseline_tag,),
        )
        n = int(cur.fetchone()[0])
    if n == 0:
        sys.exit(
            f"FATAL: baseline-tag {baseline_tag!r} has 0 rows in "
            f"prompt_audit_reverify. Run reverify with that tag first, "
            f"or verify the tag string."
        )


def _print_category_attribution_summary(
    db_path: str, current_tag: str, baseline_tag: str
) -> int:
    """Print per-category baseline/current/delta table; return NEW-category count.

    A category is NEW when baseline_count == 0 and current_count > 0. This is
    the merge-gate criterion documented in the SCORE_VERBATIM Step 0 closure
    memo: legacy-drift counts fluctuate, but the appearance of a previously-
    absent failure category indicates genuine new failure surface.
    """
    current_cats = _category_counts_for_tag(db_path, current_tag)
    baseline_cats = _category_counts_for_tag(db_path, baseline_tag)
    all_cats = sorted(set(current_cats) | set(baseline_cats))

    print()
    print("=" * 72)
    print(
        f"Category attribution: tag={current_tag}  baseline={baseline_tag}"
    )
    print()
    if not all_cats:
        print("  (no hard-failure categories in either tag)")
        return 0

    print(
        f"  {'Category':<32}  {'Baseline':>8}  {'Current':>7}  "
        f"{'Delta':>6}  Status"
    )
    print(
        f"  {'-' * 32}  {'-' * 8}  {'-' * 7}  {'-' * 6}  {'-' * 9}"
    )

    n_new = 0
    for cat in all_cats:
        baseline_n = baseline_cats.get(cat, 0)
        current_n = current_cats.get(cat, 0)
        delta = current_n - baseline_n
        if baseline_n == 0 and current_n > 0:
            status = "NEW"
            n_new += 1
        elif baseline_n > 0 and current_n == 0:
            status = "cleared"
        elif delta > 0:
            status = "+drift"
        elif delta < 0:
            status = "-drift"
        else:
            status = "unchanged"
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(
            f"  {cat:<32}  {baseline_n:>8}  {current_n:>7}  "
            f"{delta_str:>6}  {status}"
        )

    return n_new


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-verify captured prompt_audit drafts.",
    )
    parser.add_argument("--db", type=str, default=DB_PATH)
    parser.add_argument("--league-id", type=str, default="70985")
    parser.add_argument("--verifier-tag", type=str, required=True)
    parser.add_argument(
        "--baseline-tag",
        type=str,
        default=None,
        help=(
            "Optional prior verifier_tag to compare against. When provided, "
            "the regression verdict shifts from row-level pass->fail to "
            "category-NEW (any category with baseline=0, current>0)."
        ),
    )
    args = parser.parse_args()

    if args.baseline_tag is not None:
        _validate_baseline_tag_exists(args.db, args.baseline_tag)

    _ensure_table(args.db)

    # Load all prompt_audit rows for this league
    with DatabaseSession(args.db) as con:
        rows = con.execute(
            """SELECT id, season, week_index, attempt,
                      narrative_draft, verification_passed,
                      narrative_angles_text
               FROM prompt_audit
               WHERE league_id = ?
               ORDER BY season, week_index, attempt""",
            (args.league_id,),
        ).fetchall()

    if not rows:
        print(
            f"No prompt_audit rows found for league_id={args.league_id}"
        )
        sys.exit(1)

    print(
        f"Re-verifying {len(rows)} prompt_audit rows: "
        f"league={args.league_id} tag={args.verifier_tag}"
    )
    print("=" * 72)

    now = datetime.now(timezone.utc).isoformat()

    # Counters for the 4-way delta
    still_pass = 0
    still_fail = 0
    fail_to_pass = 0
    pass_to_fail = 0

    for row in rows:
        pa_id = row[0]
        season = int(row[1])
        week_index = int(row[2])
        attempt = int(row[3])
        narrative_draft = str(row[4]) if row[4] else ""
        original_passed = bool(row[5])
        narrative_angles_text = str(row[6]) if row[6] else None

        if not narrative_draft.strip():
            # Empty draft — nothing to verify, write a trivial pass
            result_json = json.dumps(
                {
                    "passed": True,
                    "hard_failures": [],
                    "soft_failures": [],
                    "checks_run": 0,
                },
            )
            with DatabaseSession(args.db) as con:
                con.execute(
                    """INSERT INTO prompt_audit_reverify
                       (prompt_audit_id, reverified_at, verifier_tag,
                        passed, hard_failure_count, soft_failure_count,
                        result_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (pa_id, now, args.verifier_tag, 1, 0, 0, result_json),
                )
            if original_passed:
                still_pass += 1
            else:
                fail_to_pass += 1
            continue

        result = verify_recap_v1(
            narrative_draft,
            db_path=args.db,
            league_id=args.league_id,
            season=season,
            week=week_index,
            narrative_angles_text=narrative_angles_text,
        )

        result_json = _result_to_json(result)

        with DatabaseSession(args.db) as con:
            con.execute(
                """INSERT INTO prompt_audit_reverify
                   (prompt_audit_id, reverified_at, verifier_tag,
                    passed, hard_failure_count, soft_failure_count,
                    result_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    pa_id,
                    now,
                    args.verifier_tag,
                    1 if result.passed else 0,
                    result.hard_failure_count,
                    result.soft_failure_count,
                    result_json,
                ),
            )

        # 4-way delta classification
        if original_passed and result.passed:
            still_pass += 1
        elif not original_passed and not result.passed:
            still_fail += 1
            # Print survivor detail
            cats = [f.category for f in result.hard_failures]
            claim_preview = (
                result.hard_failures[0].claim[:60]
                if result.hard_failures
                else "?"
            )
            print(
                f"  still-fail: row {pa_id}  "
                f"{season} w{week_index} a{attempt}  "
                f"{','.join(cats)}  {claim_preview}"
            )
        elif not original_passed and result.passed:
            fail_to_pass += 1
            print(
                f"  fail→pass:  row {pa_id}  "
                f"{season} w{week_index} a{attempt}"
            )
        else:
            # pass→fail — regression
            pass_to_fail += 1
            cats = [f.category for f in result.hard_failures]
            claim_preview = (
                result.hard_failures[0].claim[:60]
                if result.hard_failures
                else "?"
            )
            print(
                f"  pass→fail:  row {pa_id}  "
                f"{season} w{week_index} a{attempt}  "
                f"{','.join(cats)}  {claim_preview}"
            )

    # Summary
    total = still_pass + still_fail + fail_to_pass + pass_to_fail
    print()
    print("=" * 72)
    print(f"Reverify summary: tag={args.verifier_tag}  rows={total}")
    print(f"  still-pass:  {still_pass}")
    print(f"  still-fail:  {still_fail}")
    print(f"  fail→pass:   {fail_to_pass}")
    print(f"  pass→fail:   {pass_to_fail}")

    if args.baseline_tag is not None:
        n_new = _print_category_attribution_summary(
            args.db, args.verifier_tag, args.baseline_tag
        )
        print()
        if n_new > 0:
            print(
                f"*** REGRESSION: {n_new} NEW category/categories — "
                f"do NOT merge. ***"
            )
            sys.exit(1)
        else:
            print(
                f"No regressions in new categories. "
                f"Row-level pass→fail={pass_to_fail} is legacy drift."
            )
    else:
        if pass_to_fail > 0:
            print()
            print("*** REGRESSION: pass→fail > 0 — do NOT merge. ***")
            sys.exit(1)
        else:
            print()
            print("No regressions (pass→fail = 0).")


if __name__ == "__main__":
    main()
