"""Tests for squadvault.core.recaps.recap_runs.

Covers: upsert, get state, update state, artifact-to-run sync,
idempotency, reason handling.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.recap_runs import (
    RecapRunRecord,
    _has_any_approved_artifact,
    _latest_artifact_state_for_week,
    get_recap_run_state,
    sync_recap_run_state_from_artifacts,
    update_recap_run_state,
    upsert_recap_run,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024
WEEK = 1


@pytest.fixture
def db(tmp_path):
    """Fresh DB from schema.sql."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


def _run(week: int = WEEK, state: str = "ELIGIBLE", **kw) -> RecapRunRecord:
    """Build a RecapRunRecord with defaults."""
    defaults = dict(
        league_id=LEAGUE, season=SEASON, week_index=week,
        state=state, window_mode="LOCK_TO_LOCK",
        window_start="2024-09-05T12:00:00Z",
        window_end="2024-09-12T12:00:00Z",
        selection_fingerprint="a" * 64,
        canonical_ids=["fp_1", "fp_2"],
        counts_by_type={"TRANSACTION_TRADE": 1, "WAIVER_BID_AWARDED": 1},
    )
    defaults.update(kw)
    return RecapRunRecord(**defaults)


def _insert_artifact(db_path, week, version, state, **kw):
    """Insert a recap_artifact row for testing sync."""
    con = sqlite3.connect(db_path)
    con.execute(
        """INSERT INTO recap_artifacts
           (league_id, season, week_index, artifact_type, version, state,
            selection_fingerprint, created_by)
           VALUES (?, ?, ?, 'WEEKLY_RECAP', ?, ?, ?, ?)""",
        (LEAGUE, SEASON, week, version, state, "a" * 64,
         kw.get("created_by", "system")),
    )
    con.commit()
    con.close()


# ── upsert_recap_run ─────────────────────────────────────────────────

class TestUpsertRecapRun:
    def test_insert_new(self, db):
        """Inserting a new run creates a row."""
        upsert_recap_run(db, _run())
        state = get_recap_run_state(db, LEAGUE, SEASON, WEEK)
        assert state == "ELIGIBLE"

    def test_upsert_overwrites(self, db):
        """Upserting the same week updates state."""
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        upsert_recap_run(db, _run(state="DRAFTED"))
        state = get_recap_run_state(db, LEAGUE, SEASON, WEEK)
        assert state == "DRAFTED"

    def test_canonical_ids_persisted(self, db):
        """canonical_ids_json round-trips correctly."""
        upsert_recap_run(db, _run(canonical_ids=["a", "b", "c"]))
        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        con.close()
        assert json.loads(row[0]) == ["a", "b", "c"]

    def test_counts_by_type_persisted(self, db):
        """counts_by_type_json round-trips correctly."""
        upsert_recap_run(db, _run(counts_by_type={"A": 3, "B": 1}))
        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT counts_by_type_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        con.close()
        assert json.loads(row[0]) == {"A": 3, "B": 1}

    def test_different_weeks_independent(self, db):
        """Different weeks have independent rows."""
        upsert_recap_run(db, _run(week=1, state="ELIGIBLE"))
        upsert_recap_run(db, _run(week=2, state="DRAFTED"))
        assert get_recap_run_state(db, LEAGUE, SEASON, 1) == "ELIGIBLE"
        assert get_recap_run_state(db, LEAGUE, SEASON, 2) == "DRAFTED"


# ── get_recap_run_state ──────────────────────────────────────────────

class TestGetRecapRunState:
    def test_nonexistent_returns_none(self, db):
        assert get_recap_run_state(db, LEAGUE, SEASON, 99) is None


# ── update_recap_run_state ───────────────────────────────────────────

class TestUpdateRecapRunState:
    def test_update_state(self, db):
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        update_recap_run_state(db, LEAGUE, SEASON, WEEK, "DRAFTED")
        assert get_recap_run_state(db, LEAGUE, SEASON, WEEK) == "DRAFTED"

    def test_update_with_reason(self, db):
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        update_recap_run_state(db, LEAGUE, SEASON, WEEK, "WITHHELD", reason="no events")
        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT state, reason FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        con.close()
        assert row[0] == "WITHHELD"
        assert row[1] == "no events"

    def test_update_clear_reason(self, db):
        upsert_recap_run(db, _run(state="ELIGIBLE", reason="initial"))
        update_recap_run_state(db, LEAGUE, SEASON, WEEK, "DRAFTED", reason=None)
        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT reason FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        con.close()
        assert row[0] is None

    def test_update_nonexistent_raises(self, db):
        with pytest.raises(RuntimeError, match="Expected exactly 1"):
            update_recap_run_state(db, LEAGUE, SEASON, 99, "DRAFTED")


# ── sync_recap_run_state_from_artifacts ──────────────────────────────

class TestSyncFromArtifacts:
    def test_draft_artifact_sets_review_required(self, db):
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        _insert_artifact(db, WEEK, 1, "DRAFT")
        result = sync_recap_run_state_from_artifacts(db, LEAGUE, SEASON, WEEK)
        assert result == "REVIEW_REQUIRED"
        assert get_recap_run_state(db, LEAGUE, SEASON, WEEK) == "REVIEW_REQUIRED"

    def test_withheld_artifact_sets_withheld(self, db):
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        _insert_artifact(db, WEEK, 1, "WITHHELD")
        result = sync_recap_run_state_from_artifacts(db, LEAGUE, SEASON, WEEK)
        assert result == "WITHHELD"

    def test_approved_artifact_sets_approved(self, db):
        upsert_recap_run(db, _run(state="REVIEW_REQUIRED"))
        _insert_artifact(db, WEEK, 1, "APPROVED")
        result = sync_recap_run_state_from_artifacts(db, LEAGUE, SEASON, WEEK)
        assert result == "APPROVED"

    def test_no_artifacts_returns_none(self, db):
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        result = sync_recap_run_state_from_artifacts(db, LEAGUE, SEASON, WEEK)
        assert result is None

    def test_no_run_row_returns_none(self, db):
        """If recap_runs row doesn't exist, sync is a no-op."""
        _insert_artifact(db, WEEK, 1, "DRAFT")
        result = sync_recap_run_state_from_artifacts(db, LEAGUE, SEASON, WEEK)
        assert result is None

    def test_superseded_with_approved_sibling(self, db):
        """If latest is SUPERSEDED but an APPROVED exists, state becomes APPROVED."""
        upsert_recap_run(db, _run(state="ELIGIBLE"))
        _insert_artifact(db, WEEK, 1, "APPROVED")
        _insert_artifact(db, WEEK, 2, "SUPERSEDED")
        # latest is v2 SUPERSEDED, but v1 is still APPROVED
        result = sync_recap_run_state_from_artifacts(db, LEAGUE, SEASON, WEEK)
        assert result == "APPROVED"


# ── _latest_artifact_state_for_week / _has_any_approved ──────────────

class TestArtifactHelpers:
    def test_latest_artifact_state(self, db):
        _insert_artifact(db, WEEK, 1, "DRAFT")
        _insert_artifact(db, WEEK, 2, "APPROVED")
        version, state = _latest_artifact_state_for_week(db, LEAGUE, SEASON, WEEK)
        assert version == 2
        assert state == "APPROVED"

    def test_latest_artifact_none(self, db):
        assert _latest_artifact_state_for_week(db, LEAGUE, SEASON, WEEK) is None

    def test_has_any_approved_true(self, db):
        _insert_artifact(db, WEEK, 1, "APPROVED")
        assert _has_any_approved_artifact(db, LEAGUE, SEASON, WEEK) is True

    def test_has_any_approved_false(self, db):
        _insert_artifact(db, WEEK, 1, "DRAFT")
        assert _has_any_approved_artifact(db, LEAGUE, SEASON, WEEK) is False

    def test_has_any_approved_empty(self, db):
        assert _has_any_approved_artifact(db, LEAGUE, SEASON, WEEK) is False
