"""Phase 1B — EAL Window Independence Test.

Invariant: EAL evaluation for week N is independent of any persisted
directive from week N-1. Persisted directives in recap_runs are audit
metadata only and must never influence subsequent evaluations.

This test verifies the contract distinction between:
- "EAL evaluation is window-scoped and non-durable" (true)
- "EAL directives are persisted as audit metadata in recap_runs" (also true)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.eal.editorial_attunement_v1 import (
    EAL_AMBIGUITY_PREFER_SILENCE,
    EAL_LOW_CONFIDENCE_RESTRAINT,
    EAL_MODERATE_CONFIDENCE_ONLY,
    EALMeta,
    evaluate_editorial_attunement_v1,
)
from squadvault.recaps.weekly_recap_lifecycle import (
    _persist_editorial_attunement_v1_to_recap_runs,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "eal_independence_test"
SEASON = 2024


@pytest.fixture
def db(tmp_path):
    """Fresh DB from schema.sql with recap_runs rows for two weeks."""
    db_path = str(tmp_path / "eal_test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())

    # Insert recap_runs entries for week 1 and week 2 with different signal counts
    for week_index, canonical_ids, state in [
        (1, ["c1", "c2", "c3", "c4", "c5"], "DRAFT"),
        (2, ["c10", "c11"], "DRAFT"),
    ]:
        con.execute(
            """INSERT INTO recap_runs
               (league_id, season, week_index, state,
                selection_fingerprint, canonical_ids_json, counts_by_type_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                LEAGUE, SEASON, week_index, state,
                f"fp_week{week_index}",
                json.dumps(canonical_ids),
                json.dumps({"MATCHUP_RESULT": len(canonical_ids)}),
            ),
        )
    con.commit()
    con.close()
    return db_path


class TestEALWindowIndependence:
    """Prove EAL evaluation is window-scoped and not contaminated by persisted state."""

    def test_evaluate_is_pure_function(self):
        """EAL evaluation depends only on its EALMeta input, not external state.

        This is the fundamental contract: evaluate_editorial_attunement_v1
        is a pure function. Two calls with identical inputs produce identical
        outputs regardless of any persisted state anywhere.
        """
        meta_high = EALMeta(has_selection_set=True, has_window=True, included_count=5)
        meta_low = EALMeta(has_selection_set=True, has_window=True, included_count=1)

        result_high = evaluate_editorial_attunement_v1(meta_high)
        result_low = evaluate_editorial_attunement_v1(meta_low)

        assert result_high == EAL_MODERATE_CONFIDENCE_ONLY
        assert result_low == EAL_LOW_CONFIDENCE_RESTRAINT
        assert result_high != result_low, "Different metadata must produce different directives"

    def test_week2_unaffected_by_week1_persisted_directive(self, db):
        """Persist a HIGH_CONFIDENCE directive for week 1, then evaluate week 2.

        Week 2 has only 2 signals (should produce LOW_CONFIDENCE_RESTRAINT).
        The persisted week 1 directive must not influence this result.
        """
        # Persist a strong directive for week 1 (as if week 1 had many signals)
        _persist_editorial_attunement_v1_to_recap_runs(
            db_path=db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            directive=EAL_MODERATE_CONFIDENCE_ONLY,
        )

        # Verify persistence succeeded
        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT editorial_attunement_v1 FROM recap_runs WHERE league_id=? AND season=? AND week_index=1",
            (LEAGUE, SEASON),
        ).fetchone()
        con.close()
        assert row[0] == EAL_MODERATE_CONFIDENCE_ONLY, "Week 1 directive should be persisted"

        # Now evaluate EAL for week 2 using week 2's own metadata
        # Week 2 has 2 signals → should produce LOW_CONFIDENCE_RESTRAINT
        con = sqlite3.connect(db)
        eal_row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=2",
            (LEAGUE, SEASON),
        ).fetchone()
        con.close()

        ids = json.loads(eal_row[0])
        meta_week2 = EALMeta(
            has_selection_set=True,
            has_window=True,
            included_count=len(ids),
            excluded_count=None,
        )
        result_week2 = evaluate_editorial_attunement_v1(meta_week2)

        assert result_week2 == EAL_LOW_CONFIDENCE_RESTRAINT, (
            f"Week 2 with 2 signals should get LOW_CONFIDENCE_RESTRAINT, "
            f"got {result_week2}. Week 1 persisted directive must not leak."
        )

    def test_persisted_directive_does_not_alter_evaluation_path(self, db):
        """Even if we persist a directive for week 2, re-evaluating with the
        same metadata produces the same result — persistence is write-only audit."""
        meta = EALMeta(has_selection_set=True, has_window=True, included_count=2)

        # Evaluate before persistence
        result_before = evaluate_editorial_attunement_v1(meta)

        # Persist a DIFFERENT directive value (simulating a hypothetical override)
        _persist_editorial_attunement_v1_to_recap_runs(
            db_path=db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=2,
            directive=EAL_MODERATE_CONFIDENCE_ONLY,  # "wrong" value for 2 signals
        )

        # Re-evaluate with the same metadata
        result_after = evaluate_editorial_attunement_v1(meta)

        assert result_before == result_after == EAL_LOW_CONFIDENCE_RESTRAINT, (
            "Persisted directive must never influence evaluation. "
            "Evaluation is pure: same metadata → same output."
        )

    def test_none_included_count_defaults_to_restraint(self):
        """When included_count is unknown, EAL defaults to restraint regardless
        of what any other week's persisted state might say."""
        meta = EALMeta(has_selection_set=True, has_window=True, included_count=None)
        result = evaluate_editorial_attunement_v1(meta)
        assert result == EAL_LOW_CONFIDENCE_RESTRAINT

    def test_all_directive_levels_reachable_independently(self):
        """Each directive level is reachable based purely on metadata,
        proving no hidden state dependency."""
        cases = [
            (EALMeta(has_selection_set=False, has_window=True), EAL_AMBIGUITY_PREFER_SILENCE),
            (EALMeta(has_selection_set=True, has_window=False), EAL_AMBIGUITY_PREFER_SILENCE),
            (EALMeta(has_selection_set=True, has_window=True, included_count=0), EAL_AMBIGUITY_PREFER_SILENCE),
            (EALMeta(has_selection_set=True, has_window=True, included_count=None), EAL_LOW_CONFIDENCE_RESTRAINT),
            (EALMeta(has_selection_set=True, has_window=True, included_count=2), EAL_LOW_CONFIDENCE_RESTRAINT),
            (EALMeta(has_selection_set=True, has_window=True, included_count=5), EAL_MODERATE_CONFIDENCE_ONLY),
        ]
        for meta, expected in cases:
            actual = evaluate_editorial_attunement_v1(meta)
            assert actual == expected, f"Meta {meta} → expected {expected}, got {actual}"
