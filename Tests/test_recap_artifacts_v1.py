"""Tests for squadvault.core.recaps.recap_artifacts.

Covers: state machine (DRAFT→APPROVED→SUPERSEDED, DRAFT→WITHHELD),
idempotency, versioning, transition guards, fingerprint matching.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.recap_artifacts import (
    _ALLOWED_TRANSITIONS,
    ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
    _assert_transition,
    _normalize_withheld_reason,
    approve_recap_artifact,
    create_recap_artifact_draft_idempotent,
    latest_approved_version,
    supersede_approved_recap_artifact,
    withhold_recap_artifact,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024
WEEK = 1
FP = "a" * 64


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


# ── _assert_transition ───────────────────────────────────────────────

class TestAssertTransition:
    def test_allowed_transitions(self):
        for old, new in _ALLOWED_TRANSITIONS:
            _assert_transition(old, new)  # should not raise

    def test_forbidden_transition(self):
        with pytest.raises(ValueError, match="Invalid artifact transition"):
            _assert_transition("APPROVED", "DRAFT")

    def test_withheld_cannot_approve(self):
        with pytest.raises(ValueError):
            _assert_transition("WITHHELD", "APPROVED")

    def test_superseded_cannot_approve(self):
        with pytest.raises(ValueError):
            _assert_transition("SUPERSEDED", "APPROVED")


# ── _normalize_withheld_reason ───────────────────────────────────────

class TestNormalizeWithheldReason:
    def test_empty_defaults(self):
        assert _normalize_withheld_reason("") == "WITHHELD"
        assert _normalize_withheld_reason("  ") == "WITHHELD"
        assert _normalize_withheld_reason(None) == "WITHHELD"

    def test_stable_prefix_preserved(self):
        assert _normalize_withheld_reason("WINDOW_MISSING") == "WINDOW_MISSING"
        assert _normalize_withheld_reason("DNG_NO_EVENTS") == "DNG_NO_EVENTS"

    def test_custom_reason_preserved(self):
        assert _normalize_withheld_reason("custom reason") == "custom reason"


# ── create_recap_artifact_draft_idempotent ───────────────────────────

class TestCreateDraft:
    def test_creates_version_1(self, db):
        v, created = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            "2024-09-05T12:00:00Z", "2024-09-12T12:00:00Z",
            "Test recap text",
        )
        assert v == 1
        assert created is True

    def test_idempotent_same_fingerprint(self, db):
        v1, c1 = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            "2024-09-05T12:00:00Z", "2024-09-12T12:00:00Z",
            "Test recap text",
        )
        v2, c2 = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            "2024-09-05T12:00:00Z", "2024-09-12T12:00:00Z",
            "Test recap text again",
        )
        assert v1 == v2
        assert c2 is False

    def test_different_fingerprint_new_version(self, db):
        v1, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            "2024-09-05T12:00:00Z", "2024-09-12T12:00:00Z",
            "Text v1",
        )
        # Approve first, then new fingerprint creates v2
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v1, "founder")
        v2, c2 = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, "b" * 64,
            "2024-09-05T12:00:00Z", "2024-09-12T12:00:00Z",
            "Text v2",
        )
        assert v2 == 2
        assert c2 is True

    def test_force_creates_even_with_same_fingerprint(self, db):
        """Force bypasses fingerprint match on approved artifacts."""
        v1, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            None, None, "v1",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v1, "founder")
        v2, c2 = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            None, None, "v2 forced", force=True,
        )
        assert v2 == 2
        assert c2 is True

    def test_rivalry_chronicle_type(self, db):
        v, created = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP,
            None, None, "Chronicle text",
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
        )
        assert v == 1
        assert created is True


# ── approve_recap_artifact ───────────────────────────────────────────

class TestApprove:
    def test_approve_draft(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")

        con = sqlite3.connect(db)
        state = con.execute(
            "SELECT state FROM recap_artifacts WHERE version=?", (v,)
        ).fetchone()[0]
        con.close()
        assert state == "APPROVED"

    def test_approve_sets_approved_at(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")

        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT approved_at, approved_by FROM recap_artifacts WHERE version=?", (v,)
        ).fetchone()
        con.close()
        assert row[0] is not None
        assert row[1] == "founder"

    def test_approve_nonexistent_raises(self, db):
        with pytest.raises(RuntimeError, match="not found"):
            approve_recap_artifact(db, LEAGUE, SEASON, WEEK, 99, "founder")

    def test_double_approve_raises(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")
        with pytest.raises((ValueError, RuntimeError)):
            approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")


# ── withhold_recap_artifact ──────────────────────────────────────────

class TestWithhold:
    def test_withhold_draft(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        withhold_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "DNG_NO_EVENTS")

        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT state, withheld_reason FROM recap_artifacts WHERE version=?", (v,)
        ).fetchone()
        con.close()
        assert row[0] == "WITHHELD"
        assert row[1] == "DNG_NO_EVENTS"

    def test_withhold_approved_raises(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")
        with pytest.raises((ValueError, RuntimeError)):
            withhold_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "reason")


# ── supersede_approved_recap_artifact ────────────────────────────────

class TestSupersede:
    def test_supersede_approved(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")
        supersede_approved_recap_artifact(db, LEAGUE, SEASON, WEEK, v)

        con = sqlite3.connect(db)
        state = con.execute(
            "SELECT state FROM recap_artifacts WHERE version=?", (v,)
        ).fetchone()[0]
        con.close()
        assert state == "SUPERSEDED"

    def test_supersede_draft_raises(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        with pytest.raises((ValueError, RuntimeError)):
            supersede_approved_recap_artifact(db, LEAGUE, SEASON, WEEK, v)


# ── latest_approved_version ──────────────────────────────────────────

class TestLatestApprovedVersion:
    def test_no_artifacts(self, db):
        assert latest_approved_version(db, LEAGUE, SEASON, WEEK) is None

    def test_draft_only(self, db):
        create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        assert latest_approved_version(db, LEAGUE, SEASON, WEEK) is None

    def test_returns_approved(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")
        assert latest_approved_version(db, LEAGUE, SEASON, WEEK) == v

    def test_superseded_not_returned(self, db):
        v, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "text",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v, "founder")
        supersede_approved_recap_artifact(db, LEAGUE, SEASON, WEEK, v)
        assert latest_approved_version(db, LEAGUE, SEASON, WEEK) is None


# ── versioning sequence ──────────────────────────────────────────────

class TestVersionSequence:
    def test_sequential_versions(self, db):
        v1, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "v1",
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v1, "founder")

        v2, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, "b" * 64, None, None, "v2",
        )
        assert v2 == v1 + 1

        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v2, "founder")
        v3, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, "c" * 64, None, None, "v3",
        )
        assert v3 == v2 + 1
