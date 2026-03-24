"""Schema init_and_migrate equivalence gate.

# SV_DEFECT5_INIT_MIGRATE_EQUIVALENCE
# Verifies that init_and_migrate(fresh_db) produces the same schema as
# executing schema.sql directly. If these diverge, migrations are not in
# sync with schema.sql and the fixture DB can drift silently.

Engineering Excellence Plan Phase F called this out:
  "Schema drift gate: a CI check that verifies every table in the
   fixture DB matches schema.sql column-for-column."

This test closes the remaining gap: schema.sql vs init_and_migrate().
"""
from __future__ import annotations

import os
import sqlite3

import pytest

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)


def _tables(con: sqlite3.Connection) -> list[str]:
    """Return sorted list of user tables (excluding internal sqlite tables and migration tracking)."""
    return sorted([
        r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name != '_schema_migrations'"
        ).fetchall()
    ])


def _columns(con: sqlite3.Connection, table: str) -> list[tuple[str, str]]:
    """Return sorted list of (name, type) for a table."""
    return sorted([
        (r[1], r[2]) for r in con.execute(f"PRAGMA table_info({table})").fetchall()
    ])


def _views(con: sqlite3.Connection) -> list[str]:
    """Return sorted list of views."""
    return sorted([
        r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        ).fetchall()
    ])


def _indexes(con: sqlite3.Connection) -> list[str]:
    """Return sorted list of user-created indexes."""
    return sorted([
        r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ])


@pytest.fixture
def schema_only_db(tmp_path):
    """Create a DB from schema.sql directly (no migration framework)."""
    db_path = str(tmp_path / "schema_only.sqlite")
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


@pytest.fixture
def migrated_db(tmp_path):
    """Create a DB via init_and_migrate (schema.sql + migration framework)."""
    from squadvault.core.storage.migrate import init_and_migrate
    db_path = str(tmp_path / "migrated.sqlite")
    init_and_migrate(db_path)
    return db_path


class TestInitMigrateEquivalence:
    """init_and_migrate must produce the same schema as raw schema.sql execution."""

    def test_same_tables(self, schema_only_db, migrated_db):
        """Both paths must create the same set of tables."""
        s_con = sqlite3.connect(schema_only_db)
        m_con = sqlite3.connect(migrated_db)
        s_tables = set(_tables(s_con))
        m_tables = set(_tables(m_con))
        s_con.close()
        m_con.close()

        only_schema = sorted(s_tables - m_tables)
        only_migrated = sorted(m_tables - s_tables)
        failures = []
        if only_schema:
            failures.append(f"Tables in schema.sql only: {only_schema}")
        if only_migrated:
            failures.append(f"Tables in init_and_migrate only: {only_migrated}")
        assert not failures, "\n".join(failures)

    def test_same_columns_per_table(self, schema_only_db, migrated_db):
        """Every shared table must have identical columns."""
        s_con = sqlite3.connect(schema_only_db)
        m_con = sqlite3.connect(migrated_db)
        shared = sorted(set(_tables(s_con)) & set(_tables(m_con)))
        failures = []
        for t in shared:
            s_cols = _columns(s_con, t)
            m_cols = _columns(m_con, t)
            if s_cols != m_cols:
                failures.append(f"{t}: schema.sql={s_cols} vs migrated={m_cols}")
        s_con.close()
        m_con.close()
        assert not failures, "Column drift:\n" + "\n".join(failures)

    def test_same_views(self, schema_only_db, migrated_db):
        """Both paths must create the same views."""
        s_con = sqlite3.connect(schema_only_db)
        m_con = sqlite3.connect(migrated_db)
        s_views = _views(s_con)
        m_views = _views(m_con)
        s_con.close()
        m_con.close()
        assert s_views == m_views, f"View drift: schema.sql={s_views} vs migrated={m_views}"

    def test_same_indexes(self, schema_only_db, migrated_db):
        """Both paths must create the same indexes."""
        s_con = sqlite3.connect(schema_only_db)
        m_con = sqlite3.connect(migrated_db)
        s_idx = _indexes(s_con)
        m_idx = _indexes(m_con)
        s_con.close()
        m_con.close()
        assert s_idx == m_idx, f"Index drift: schema.sql={s_idx} vs migrated={m_idx}"
