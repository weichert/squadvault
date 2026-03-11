"""Tests for core storage utilities: DatabaseSession, db_utils, migrate.

Covers: DatabaseSession context manager, table_columns, norm_id,
migration framework (init_and_migrate, apply_migrations).
"""
from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.db_utils import table_columns, norm_id


# ── DatabaseSession ──────────────────────────────────────────────────

class TestDatabaseSession:
    def test_context_manager_opens_and_closes(self, tmp_path):
        """Session opens on enter and closes on exit."""
        db = str(tmp_path / "test.sqlite")
        with DatabaseSession(db) as conn:
            conn.execute("CREATE TABLE t (id INTEGER)")
            conn.execute("INSERT INTO t VALUES (1)")
        # Connection should be closed — verify data persisted
        c = sqlite3.connect(db)
        assert c.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
        c.close()

    def test_auto_commit_on_success(self, tmp_path):
        """Session auto-commits when no exception occurs."""
        db = str(tmp_path / "test.sqlite")
        with DatabaseSession(db) as conn:
            conn.execute("CREATE TABLE t (id INTEGER)")
            conn.execute("INSERT INTO t VALUES (42)")
        # Verify committed
        c = sqlite3.connect(db)
        assert c.execute("SELECT id FROM t").fetchone()[0] == 42
        c.close()

    def test_no_commit_on_exception(self, tmp_path):
        """Session does not commit when an exception occurs."""
        db = str(tmp_path / "test.sqlite")
        # Create table first
        c = sqlite3.connect(db)
        c.execute("CREATE TABLE t (id INTEGER)")
        c.commit()
        c.close()
        # Try to insert and fail
        with pytest.raises(ValueError):
            with DatabaseSession(db) as conn:
                conn.execute("INSERT INTO t VALUES (99)")
                raise ValueError("boom")
        # Verify NOT committed
        c = sqlite3.connect(db)
        assert c.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
        c.close()

    def test_row_factory_set(self, tmp_path):
        """Session sets Row factory for dict-like access."""
        db = str(tmp_path / "test.sqlite")
        with DatabaseSession(db) as conn:
            conn.execute("CREATE TABLE t (name TEXT)")
            conn.execute("INSERT INTO t VALUES ('hello')")
            row = conn.execute("SELECT name FROM t").fetchone()
            assert row["name"] == "hello"


# ── db_utils ─────────────────────────────────────────────────────────

class TestTableColumns:
    def test_returns_column_names(self, tmp_path):
        """table_columns returns set of column names."""
        db = str(tmp_path / "test.sqlite")
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE t (id INTEGER, name TEXT, score REAL)")
        result = table_columns(conn, "t")
        conn.close()
        assert result == {"id", "name", "score"}

    def test_empty_table(self, tmp_path):
        """table_columns works on a table with no rows."""
        db = str(tmp_path / "test.sqlite")
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE t (x INTEGER)")
        result = table_columns(conn, "t")
        conn.close()
        assert result == {"x"}


class TestNormId:
    def test_none(self):
        assert norm_id(None) == ""

    def test_empty(self):
        assert norm_id("") == ""

    def test_whitespace(self):
        assert norm_id("   ") == ""

    def test_leading_zeros(self):
        assert norm_id("0042") == "42"

    def test_all_zeros(self):
        assert norm_id("000") == "0"

    def test_no_leading_zeros(self):
        assert norm_id("123") == "123"

    def test_non_numeric(self):
        assert norm_id("abc") == "abc"

    def test_integer_input(self):
        assert norm_id(42) == "42"


# ── migrate ──────────────────────────────────────────────────────────

class TestMigrate:
    def test_init_and_migrate_creates_tables(self, tmp_path):
        """init_and_migrate creates tables from schema.sql."""
        from squadvault.core.storage.migrate import init_and_migrate
        db = str(tmp_path / "test.sqlite")
        init_and_migrate(db)
        conn = sqlite3.connect(db)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]
        conn.close()
        assert "memory_events" in tables
        assert "recap_artifacts" in tables

    def test_apply_migrations_creates_tracking_table(self, tmp_path):
        """apply_migrations creates _schema_migrations table."""
        from squadvault.core.storage.migrate import apply_migrations
        db = str(tmp_path / "test.sqlite")
        # Create empty DB
        conn = sqlite3.connect(db)
        conn.close()
        apply_migrations(db)
        conn = sqlite3.connect(db)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        assert "_schema_migrations" in tables

    def test_migrations_are_idempotent(self, tmp_path):
        """Running migrations twice produces the same result."""
        from squadvault.core.storage.migrate import init_and_migrate
        db = str(tmp_path / "test.sqlite")
        init_and_migrate(db)
        init_and_migrate(db)  # second run should be no-op
        conn = sqlite3.connect(db)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]
        conn.close()
        assert "memory_events" in tables
