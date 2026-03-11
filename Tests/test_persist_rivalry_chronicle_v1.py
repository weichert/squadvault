"""Tests for squadvault.chronicle.persist_rivalry_chronicle_v1.

Covers: _insert_recap_artifact_row_schema_resilient, _next_version,
_latest_approved_chronicle_row, PersistedChronicleV1, SchemaError.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.chronicle.persist_rivalry_chronicle_v1 import (
    _insert_recap_artifact_row_schema_resilient,
    _latest_approved_chronicle_row,
    _next_version,
    PersistedChronicleV1,
)
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1
from squadvault.errors import SchemaError

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = 70985
SEASON = 2024
WEEK = 1
FP = "a" * 64


@pytest.fixture
def db(tmp_path):
    """Fresh DB from schema.sql."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


@pytest.fixture
def conn(db):
    """Open connection to fresh DB."""
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


# ── _insert_recap_artifact_row_schema_resilient ──────────────────────

class TestSchemaResilientInsert:
    def test_basic_insert(self, conn):
        """Insert creates a row with expected values."""
        _insert_recap_artifact_row_schema_resilient(
            conn,
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1, state="APPROVED",
            selection_fingerprint=FP,
            rendered_text="Chronicle text here.",
            created_at_utc="2024-12-01T00:00:00Z",
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM recap_artifacts WHERE league_id=? AND artifact_type=?",
            (LEAGUE, ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1),
        ).fetchone()
        assert row is not None
        assert row["state"] == "APPROVED"
        assert row["version"] == 1
        assert row["selection_fingerprint"] == FP
        assert "Chronicle text" in row["rendered_text"]

    def test_missing_required_columns_raises(self, tmp_path):
        """If recap_artifacts is missing required columns, raise SchemaError."""
        db = str(tmp_path / "bad.sqlite")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE recap_artifacts (id INTEGER PRIMARY KEY, league_id TEXT)")
        with pytest.raises(SchemaError, match="missing required columns"):
            _insert_recap_artifact_row_schema_resilient(
                con,
                league_id=LEAGUE, season=SEASON, week_index=WEEK,
                artifact_type="TEST", version=1, state="DRAFT",
                selection_fingerprint=FP, rendered_text="text",
                created_at_utc="2024-12-01T00:00:00Z",
            )
        con.close()


# ── _next_version ────────────────────────────────────────────────────

class TestNextVersion:
    def test_first_version(self, conn):
        """No existing artifacts → version 1."""
        assert _next_version(conn, LEAGUE, SEASON, WEEK) == 1

    def test_increments(self, conn):
        """After inserting v1, next should be v2."""
        _insert_recap_artifact_row_schema_resilient(
            conn,
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1, state="APPROVED",
            selection_fingerprint=FP, rendered_text="v1",
            created_at_utc="2024-12-01T00:00:00Z",
        )
        conn.commit()
        assert _next_version(conn, LEAGUE, SEASON, WEEK) == 2

    def test_different_week_independent(self, conn):
        """Version numbering is per-week."""
        _insert_recap_artifact_row_schema_resilient(
            conn,
            league_id=LEAGUE, season=SEASON, week_index=1,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=3, state="APPROVED",
            selection_fingerprint=FP, rendered_text="v3",
            created_at_utc="2024-12-01T00:00:00Z",
        )
        conn.commit()
        assert _next_version(conn, LEAGUE, SEASON, 2) == 1


# ── _latest_approved_chronicle_row ───────────────────────────────────

class TestLatestApprovedChronicleRow:
    def test_no_rows(self, conn):
        assert _latest_approved_chronicle_row(conn, LEAGUE, SEASON, WEEK) is None

    def test_finds_approved(self, conn):
        _insert_recap_artifact_row_schema_resilient(
            conn,
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1, state="APPROVED",
            selection_fingerprint=FP, rendered_text="text",
            created_at_utc="2024-12-01T00:00:00Z",
        )
        conn.commit()
        row = _latest_approved_chronicle_row(conn, LEAGUE, SEASON, WEEK)
        assert row is not None
        assert row["version"] == 1
        assert row["selection_fingerprint"] == FP

    def test_ignores_draft(self, conn):
        """DRAFT artifacts are not returned."""
        _insert_recap_artifact_row_schema_resilient(
            conn,
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1, state="DRAFT",
            selection_fingerprint=FP, rendered_text="text",
            created_at_utc="2024-12-01T00:00:00Z",
        )
        conn.commit()
        assert _latest_approved_chronicle_row(conn, LEAGUE, SEASON, WEEK) is None

    def test_returns_latest_version(self, conn):
        """When multiple APPROVED exist, returns highest version."""
        for v in [1, 2, 3]:
            _insert_recap_artifact_row_schema_resilient(
                conn,
                league_id=LEAGUE, season=SEASON, week_index=WEEK,
                artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
                version=v, state="APPROVED",
                selection_fingerprint=f"fp_v{v}" + "x" * (64 - 4 - len(str(v))),
                rendered_text=f"version {v}",
                created_at_utc="2024-12-01T00:00:00Z",
            )
        conn.commit()
        row = _latest_approved_chronicle_row(conn, LEAGUE, SEASON, WEEK)
        assert row["version"] == 3


# ── PersistedChronicleV1 dataclass ───────────────────────────────────

class TestPersistedChronicleV1:
    def test_frozen(self):
        p = PersistedChronicleV1(
            league_id=LEAGUE, season=SEASON, anchor_week_index=WEEK,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1, created_new=True,
        )
        with pytest.raises(AttributeError):
            p.version = 2

    def test_fields(self):
        p = PersistedChronicleV1(
            league_id=LEAGUE, season=SEASON, anchor_week_index=5,
            artifact_type="TEST", version=3, created_new=False,
        )
        assert p.anchor_week_index == 5
        assert p.version == 3
        assert p.created_new is False
