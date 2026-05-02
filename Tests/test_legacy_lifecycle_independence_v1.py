"""Phase 3 — Legacy Lifecycle Independence Test.

Invariant: generate_weekly_recap_draft can produce a DRAFT artifact
using only recap_runs data, without reading from the legacy recaps table.

This test verifies the core Phase 3B deliverable: the canonical lifecycle
is self-sufficient when recap_runs contains valid selection data.
"""
from __future__ import annotations

import sqlite3

import pytest

from squadvault.core.recaps.recap_artifacts import (
    latest_approved_version,
)
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.storage.migrate import init_and_migrate
from squadvault.errors import RecapNotFoundError
from squadvault.recaps.weekly_recap_lifecycle import (
    _render_text_from_recap_runs,
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)

LEAGUE = "legacy_independence_test"
SEASON = 2024


@pytest.fixture
def db_no_recaps_data(tmp_path):
    """Fresh DB with schema but NO data in the legacy recaps table.

    Has recap_runs data for week 1 to prove the canonical path works.
    """
    db_path = str(tmp_path / "no_legacy.sqlite")
    init_and_migrate(db_path)

    # Populate recap_runs with valid selection data
    canonical_ids = [101, 102, 103, 104, 105]
    upsert_recap_run(db_path, RecapRunRecord(
        league_id=LEAGUE,
        season=SEASON,
        week_index=1,
        state="ELIGIBLE",
        window_mode="LOCK_TO_LOCK",
        window_start="2024-09-05T12:00:00Z",
        window_end="2024-09-12T12:00:00Z",
        selection_fingerprint="abcdef1234567890" * 4,
        canonical_ids=[str(c) for c in canonical_ids],
        counts_by_type={"WAIVER_BID_AWARDED": 3, "TRANSACTION_FREE_AGENT": 2},
        reason=None,
    ))

    # The legacy recaps table no longer exists in schema.sql —
    # lifecycle independence is guaranteed by architecture.

    return db_path


class TestLegacyLifecycleIndependence:
    """Prove the canonical lifecycle works without the legacy recaps table."""

    def test_render_from_recap_runs_produces_text(self, db_no_recaps_data):
        """_render_text_from_recap_runs returns rendered text from recap_runs data."""
        text = _render_text_from_recap_runs(
            db_no_recaps_data, LEAGUE, SEASON, 1,
        )
        assert text is not None
        assert "SquadVault Weekly Recap" in text
        assert LEAGUE in text
        assert "2024-09-05T12:00:00Z" in text
        assert "2024-09-12T12:00:00Z" in text
        assert "Events selected: 5" in text
        assert "WAIVER_BID_AWARDED" in text

    def test_render_from_recap_runs_returns_none_for_missing_week(self, db_no_recaps_data):
        """_render_text_from_recap_runs returns None when no recap_runs data exists."""
        text = _render_text_from_recap_runs(
            db_no_recaps_data, LEAGUE, SEASON, 99,
        )
        assert text is None

    def test_generate_draft_without_recaps_table_data(self, db_no_recaps_data):
        """generate_weekly_recap_draft succeeds with NO data in the recaps table.

        This is the key Phase 3B acceptance test: the canonical path reads
        from recap_runs only, rendering text directly from selection metadata.
        """
        result = generate_weekly_recap_draft(
            db_path=db_no_recaps_data,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="phase3_test",
        )

        assert result.version == 1
        assert result.created_new is True
        assert result.selection_fingerprint == "abcdef1234567890" * 4
        assert result.window_start == "2024-09-05T12:00:00Z"
        assert result.window_end == "2024-09-12T12:00:00Z"

    def test_draft_contains_rendered_text(self, db_no_recaps_data):
        """The created DRAFT artifact contains non-empty rendered text."""
        generate_weekly_recap_draft(
            db_path=db_no_recaps_data,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="phase3_test",
        )

        con = sqlite3.connect(db_no_recaps_data)
        row = con.execute(
            """SELECT rendered_text FROM recap_artifacts
               WHERE league_id=? AND season=? AND week_index=? AND state='DRAFT'""",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()

        assert row is not None
        assert row[0] is not None
        assert len(row[0]) > 0
        assert "SquadVault Weekly Recap" in row[0]

    def test_full_lifecycle_without_recaps_table(self, db_no_recaps_data):
        """Draft -> Approve works end-to-end without any recaps table data."""
        # Draft
        draft = generate_weekly_recap_draft(
            db_path=db_no_recaps_data,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="phase3_lifecycle_test",
        )
        assert draft.version == 1

        # Approve
        approval = approve_latest_weekly_recap(
            db_path=db_no_recaps_data,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            approved_by="test_founder",
        )
        assert approval.approved_version == 1

        # Verify
        v = latest_approved_version(db_no_recaps_data, LEAGUE, SEASON, 1)
        assert v == 1

    def test_no_recap_runs_row_raises(self, db_no_recaps_data):
        """Missing recap_runs row raises RecapNotFoundError."""
        with pytest.raises(RecapNotFoundError):
            generate_weekly_recap_draft(
                db_path=db_no_recaps_data,
                league_id=LEAGUE,
                season=SEASON,
                week_index=99,
                reason="should_fail",
            )

    def test_eal_persistence_works_without_recaps(self, db_no_recaps_data):
        """EAL directive is persisted to recap_runs even on the canonical path."""
        generate_weekly_recap_draft(
            db_path=db_no_recaps_data,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="eal_test",
        )

        con = sqlite3.connect(db_no_recaps_data)
        row = con.execute(
            "SELECT editorial_attunement_v1 FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()

        assert row is not None
        assert row[0] is not None
        # 5 signals -> MODERATE_CONFIDENCE_ONLY
        assert row[0] == "MODERATE_CONFIDENCE_ONLY"
