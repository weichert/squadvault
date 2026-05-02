"""Tests for squadvault.consumers.editorial_actions.

Covers: ensure_editorial_tables, insert_editorial_action, fetch_editorial_log,
action validation. Table is now created by schema.sql, not at runtime.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.consumers.editorial_actions import (
    ACTIONS,
    ensure_editorial_tables,
    fetch_editorial_log,
    insert_editorial_action,
    utc_now_iso,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"


@pytest.fixture
def conn(tmp_path):
    """Fresh DB from schema.sql."""
    db_path = str(tmp_path / "test.sqlite")
    c = sqlite3.connect(db_path)
    c.executescript(SCHEMA_PATH.read_text())
    yield c
    c.close()


# ── utc_now_iso ──────────────────────────────────────────────────────

class TestUtcNowIso:
    def test_format(self):
        result = utc_now_iso()
        assert result.endswith("Z")
        assert "T" in result
        assert len(result) == 20  # 2024-01-01T00:00:00Z


# ── ensure_editorial_tables ──────────────────────────────────────────

class TestEnsureEditorialTables:
    def test_table_exists_from_schema(self, conn):
        """editorial_actions table is created by schema.sql, not runtime."""
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        assert "editorial_actions" in tables

    def test_ensure_is_safe_noop(self, conn):
        """ensure_editorial_tables is a no-op and does not fail."""
        ensure_editorial_tables(conn)
        ensure_editorial_tables(conn)  # second call also safe
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='editorial_actions'"
        ).fetchone()[0]
        assert count == 1


# ── insert_editorial_action ──────────────────────────────────────────

class TestInsertEditorialAction:
    def test_insert_valid_action(self, conn):
        insert_editorial_action(
            conn,
            league_id="L1", season=2024, week_index=1,
            artifact_kind="WEEKLY_RECAP", artifact_version=1,
            selection_fingerprint="fp1",
            action="OPEN", actor="steve", notes_md=None,
        )
        rows = conn.execute("SELECT COUNT(*) FROM editorial_actions").fetchone()[0]
        assert rows == 1

    def test_all_valid_actions(self, conn):
        for action in ACTIONS:
            insert_editorial_action(
                conn,
                league_id="L1", season=2024, week_index=1,
                artifact_kind="WEEKLY_RECAP", artifact_version=1,
                selection_fingerprint=None,
                action=action, actor="steve", notes_md=None,
            )
        rows = conn.execute("SELECT COUNT(*) FROM editorial_actions").fetchone()[0]
        assert rows == len(ACTIONS)

    def test_invalid_action_raises(self, conn):
        with pytest.raises(ValueError, match="Invalid action"):
            insert_editorial_action(
                conn,
                league_id="L1", season=2024, week_index=1,
                artifact_kind="WEEKLY_RECAP", artifact_version=1,
                selection_fingerprint=None,
                action="INVALID", actor="steve", notes_md=None,
            )

    def test_notes_persisted(self, conn):
        insert_editorial_action(
            conn,
            league_id="L1", season=2024, week_index=1,
            artifact_kind="WEEKLY_RECAP", artifact_version=1,
            selection_fingerprint=None,
            action="NOTES", actor="steve", notes_md="This is a note.",
        )
        row = conn.execute("SELECT notes_md FROM editorial_actions").fetchone()
        assert row[0] == "This is a note."


# ── fetch_editorial_log ──────────────────────────────────────────────

class TestFetchEditorialLog:
    def test_empty_log(self, conn):
        result = list(fetch_editorial_log(
            conn, league_id="L1", season=2024, week_index=1,
        ))
        assert result == []

    def test_returns_inserted_actions(self, conn):
        insert_editorial_action(
            conn,
            league_id="L1", season=2024, week_index=1,
            artifact_kind="WEEKLY_RECAP", artifact_version=1,
            selection_fingerprint="fp1",
            action="OPEN", actor="steve", notes_md=None,
        )
        insert_editorial_action(
            conn,
            league_id="L1", season=2024, week_index=1,
            artifact_kind="WEEKLY_RECAP", artifact_version=1,
            selection_fingerprint="fp1",
            action="APPROVE", actor="steve", notes_md=None,
        )
        result = list(fetch_editorial_log(
            conn, league_id="L1", season=2024, week_index=1,
        ))
        assert len(result) == 2
        # Most recent first (ORDER BY id DESC)
        assert result[0][2] == "APPROVE"
        assert result[1][2] == "OPEN"

    def test_filters_by_league_season_week(self, conn):
        insert_editorial_action(
            conn,
            league_id="L1", season=2024, week_index=1,
            artifact_kind="WEEKLY_RECAP", artifact_version=1,
            selection_fingerprint=None,
            action="OPEN", actor="steve", notes_md=None,
        )
        insert_editorial_action(
            conn,
            league_id="L1", season=2024, week_index=2,
            artifact_kind="WEEKLY_RECAP", artifact_version=1,
            selection_fingerprint=None,
            action="OPEN", actor="steve", notes_md=None,
        )
        result_w1 = list(fetch_editorial_log(
            conn, league_id="L1", season=2024, week_index=1,
        ))
        result_w2 = list(fetch_editorial_log(
            conn, league_id="L1", season=2024, week_index=2,
        ))
        assert len(result_w1) == 1
        assert len(result_w2) == 1

    def test_respects_limit(self, conn):
        for i in range(10):
            insert_editorial_action(
                conn,
                league_id="L1", season=2024, week_index=1,
                artifact_kind="WEEKLY_RECAP", artifact_version=1,
                selection_fingerprint=None,
                action="OPEN", actor="steve", notes_md=None,
            )
        result = list(fetch_editorial_log(
            conn, league_id="L1", season=2024, week_index=1, limit=3,
        ))
        assert len(result) == 3
