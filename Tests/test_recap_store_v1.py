"""Tests for squadvault.core.recaps.recap_store (legacy bridge)

Covers: get_latest_recap_version, insert_recap, recap_exists,
insert_recap_v1_if_missing, get_latest_recap_row, update_recap_status,
mark_latest_stale_if_needed, insert_regenerated_recap,
set_recap_artifact, ensure_weekly_recap_artifact_row_if_missing.
"""
from __future__ import annotations

import sqlite3
import pytest

from squadvault.core.recaps.recap_store import (
    get_latest_recap_version,
    insert_recap,
    recap_exists,
    insert_recap_v1_if_missing,
    get_latest_recap_row,
    update_recap_status,
    mark_latest_stale_if_needed,
    insert_regenerated_recap,
    set_recap_artifact,
    ensure_weekly_recap_artifact_row_if_missing,
)

LEAGUE = "test_league"
SEASON = 2024
WEEK = 5


def _make_db(tmp_path) -> str:
    db_path = str(tmp_path / "test.sqlite")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE recaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            week_index INTEGER NOT NULL,
            recap_version INTEGER NOT NULL,
            selection_version INTEGER NOT NULL DEFAULT 1,
            selection_fingerprint TEXT NOT NULL,
            window_start TEXT,
            window_end TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            artifact_path TEXT,
            artifact_json TEXT,
            UNIQUE (league_id, season, week_index, recap_version)
        );
        CREATE TABLE recap_artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            week_index INTEGER NOT NULL,
            artifact_type TEXT NOT NULL DEFAULT 'WEEKLY_RECAP',
            version INTEGER NOT NULL,
            state TEXT NOT NULL,
            selection_fingerprint TEXT NOT NULL,
            window_start TEXT,
            window_end TEXT,
            rendered_text TEXT,
            created_at TEXT NOT NULL DEFAULT '2024-01-01T00:00:00Z',
            created_by TEXT NOT NULL DEFAULT 'system',
            approved_at TEXT,
            approved_by TEXT,
            withheld_reason TEXT,
            supersedes_version INTEGER,
            UNIQUE (league_id, season, week_index, artifact_type, version)
        );
    """)
    conn.close()
    return db_path


# ── get_latest_recap_version ─────────────────────────────────────────

class TestGetLatestVersion:
    def test_no_recaps_returns_none(self, tmp_path):
        db = _make_db(tmp_path)
        assert get_latest_recap_version(db, LEAGUE, SEASON, WEEK) is None

    def test_returns_highest_version(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        insert_recap(db, LEAGUE, SEASON, WEEK, 2, "fp2", None, None)
        assert get_latest_recap_version(db, LEAGUE, SEASON, WEEK) == 2


# ── recap_exists ─────────────────────────────────────────────────────

class TestRecapExists:
    def test_false_when_empty(self, tmp_path):
        db = _make_db(tmp_path)
        assert recap_exists(db, LEAGUE, SEASON, WEEK) is False

    def test_true_after_insert(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        assert recap_exists(db, LEAGUE, SEASON, WEEK) is True


# ── insert_recap_v1_if_missing ───────────────────────────────────────

class TestInsertV1IfMissing:
    def test_inserts_when_missing(self, tmp_path):
        db = _make_db(tmp_path)
        result = insert_recap_v1_if_missing(db, LEAGUE, SEASON, WEEK, "fp1", "s", "e")
        assert result is True
        assert get_latest_recap_version(db, LEAGUE, SEASON, WEEK) == 1

    def test_noop_when_exists(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        result = insert_recap_v1_if_missing(db, LEAGUE, SEASON, WEEK, "fp2", "s", "e")
        assert result is False


# ── get_latest_recap_row ─────────────────────────────────────────────

class TestGetLatestRow:
    def test_none_when_empty(self, tmp_path):
        db = _make_db(tmp_path)
        assert get_latest_recap_row(db, LEAGUE, SEASON, WEEK) is None

    def test_returns_latest(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None, status="ACTIVE")
        insert_recap(db, LEAGUE, SEASON, WEEK, 2, "fp2", None, None, status="ACTIVE")
        row = get_latest_recap_row(db, LEAGUE, SEASON, WEEK)
        assert row[0] == 2  # version
        assert row[1] == "fp2"  # fingerprint
        assert row[2] == "ACTIVE"  # status


# ── update_recap_status ──────────────────────────────────────────────

class TestUpdateStatus:
    def test_updates_status(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None, status="ACTIVE")
        update_recap_status(db, LEAGUE, SEASON, WEEK, 1, "STALE")
        row = get_latest_recap_row(db, LEAGUE, SEASON, WEEK)
        assert row[2] == "STALE"


# ── mark_latest_stale_if_needed ──────────────────────────────────────

class TestMarkStale:
    def test_no_recap_returns_false(self, tmp_path):
        db = _make_db(tmp_path)
        assert mark_latest_stale_if_needed(db, LEAGUE, SEASON, WEEK, "fp1") is False

    def test_same_fingerprint_returns_false(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        assert mark_latest_stale_if_needed(db, LEAGUE, SEASON, WEEK, "fp1") is False

    def test_different_fingerprint_marks_stale(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        assert mark_latest_stale_if_needed(db, LEAGUE, SEASON, WEEK, "fp_new") is True
        row = get_latest_recap_row(db, LEAGUE, SEASON, WEEK)
        assert row[2] == "STALE"


# ── insert_regenerated_recap ─────────────────────────────────────────

class TestInsertRegenerated:
    def test_first_regeneration(self, tmp_path):
        db = _make_db(tmp_path)
        v = insert_regenerated_recap(db, LEAGUE, SEASON, WEEK, "fp1", "s", "e")
        assert v == 1

    def test_increments_version(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        v = insert_regenerated_recap(db, LEAGUE, SEASON, WEEK, "fp2", "s", "e")
        assert v == 2

    def test_supersedes_previous(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None, status="ACTIVE")
        insert_regenerated_recap(db, LEAGUE, SEASON, WEEK, "fp2", "s", "e")
        # Check that v1 is now SUPERSEDED
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT status FROM recaps WHERE recap_version=1 AND league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        conn.close()
        assert row[0] == "SUPERSEDED"


# ── set_recap_artifact ───────────────────────────────────────────────

class TestSetArtifact:
    def test_sets_artifact_fields(self, tmp_path):
        db = _make_db(tmp_path)
        insert_recap(db, LEAGUE, SEASON, WEEK, 1, "fp1", None, None)
        set_recap_artifact(db, LEAGUE, SEASON, WEEK, 1, "/path/to/art.json", '{"x":1}')
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT artifact_path, artifact_json FROM recaps WHERE recap_version=1 AND league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        conn.close()
        assert row[0] == "/path/to/art.json"
        assert row[1] == '{"x":1}'


# ── ensure_weekly_recap_artifact_row_if_missing ──────────────────────

class TestEnsureArtifactRow:
    def test_inserts_when_missing(self, tmp_path):
        db = _make_db(tmp_path)
        result = ensure_weekly_recap_artifact_row_if_missing(
            db, LEAGUE, SEASON, WEEK, 1,
            state="DRAFT", selection_fingerprint="fp1",
            window_start="s", window_end="e",
        )
        assert result is True

    def test_noop_when_exists(self, tmp_path):
        db = _make_db(tmp_path)
        ensure_weekly_recap_artifact_row_if_missing(
            db, LEAGUE, SEASON, WEEK, 1,
            state="DRAFT", selection_fingerprint="fp1",
            window_start="s", window_end="e",
        )
        result = ensure_weekly_recap_artifact_row_if_missing(
            db, LEAGUE, SEASON, WEEK, 1,
            state="APPROVED", selection_fingerprint="fp2",
            window_start="s2", window_end="e2",
        )
        assert result is False
        # Verify original state preserved
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT state, selection_fingerprint FROM recap_artifacts WHERE version=1 AND league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, WEEK),
        ).fetchone()
        conn.close()
        assert row[0] == "DRAFT"
        assert row[1] == "fp1"
