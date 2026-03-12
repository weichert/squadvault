"""Tests for storage utilities, migration framework, and error hierarchy.

Covers: table_columns, norm_id, apply_migrations, init_and_migrate,
error hierarchy and inheritance.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.storage.db_utils import table_columns, norm_id, row_to_dict, now_utc_iso
from squadvault.core.storage.migrate import apply_migrations, init_and_migrate
from squadvault.errors import (
    SquadVaultError,
    RecapNotFoundError,
    RecapStateError,
    RecapDataError,
    ChronicleError,
    ConfigError,
    SchemaError,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"


# ── table_columns ────────────────────────────────────────────────────

class TestTableColumns:
    def test_returns_columns(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE t (a TEXT, b INTEGER, c REAL)")
        con.commit()
        cols = table_columns(con, "t")
        con.close()
        assert cols == {"a", "b", "c"}

    def test_empty_table(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE t (x TEXT)")
        con.commit()
        cols = table_columns(con, "t")
        con.close()
        assert cols == {"x"}

    def test_schema_tables(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        con = sqlite3.connect(db)
        con.executescript(SCHEMA_PATH.read_text())
        cols = table_columns(con, "memory_events")
        con.close()
        assert "league_id" in cols
        assert "payload_json" in cols
        assert "event_type" in cols


# ── norm_id ──────────────────────────────────────────────────────────

class TestNormId:
    def test_normal_string(self):
        assert norm_id("abc") == "abc"

    def test_strips_whitespace(self):
        assert norm_id("  hello  ") == "hello"

    def test_none_returns_empty(self):
        assert norm_id(None) == ""

    def test_empty_returns_empty(self):
        assert norm_id("") == ""
        assert norm_id("   ") == ""

    def test_numeric_strips_leading_zeros(self):
        assert norm_id("007") == "7"
        assert norm_id("100") == "100"

    def test_all_zeros(self):
        assert norm_id("000") == "0"

    def test_non_numeric_preserved(self):
        assert norm_id("0x1F") == "0x1F"

    def test_int_input(self):
        assert norm_id(42) == "42"


# ── row_to_dict ──────────────────────────────────────────────────────

class TestRowToDict:
    def test_converts_row(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE t (a TEXT, b INTEGER)")
        con.execute("INSERT INTO t VALUES ('hello', 42)")
        con.commit()
        row = con.execute("SELECT * FROM t").fetchone()
        result = row_to_dict(row)
        con.close()
        assert result == {"a": "hello", "b": 42}

    def test_empty_values(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE t (a TEXT, b INTEGER)")
        con.execute("INSERT INTO t VALUES (NULL, NULL)")
        con.commit()
        row = con.execute("SELECT * FROM t").fetchone()
        result = row_to_dict(row)
        con.close()
        assert result == {"a": None, "b": None}


# ── now_utc_iso ──────────────────────────────────────────────────────

class TestNowUtcIso:
    def test_returns_z_suffix(self):
        ts = now_utc_iso()
        assert ts.endswith("Z")

    def test_iso_format(self):
        ts = now_utc_iso()
        assert "T" in ts
        assert len(ts) == 20  # "2024-01-01T00:00:00Z"

    def test_deterministic_within_second(self):
        t1 = now_utc_iso()
        t2 = now_utc_iso()
        # Within same second, should be identical
        assert t1 == t2 or t1 < t2


# ── apply_migrations ─────────────────────────────────────────────────

class TestMigrations:
    def test_init_and_migrate_creates_tables(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        init_and_migrate(db)
        con = sqlite3.connect(db)
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        con.close()
        assert "memory_events" in tables
        assert "canonical_events" in tables
        assert "recap_artifacts" in tables

    def test_apply_migrations_idempotent(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        init_and_migrate(db)
        # Second call should not fail
        applied = apply_migrations(db)
        assert isinstance(applied, list)

    def test_migrations_tracking_table(self, tmp_path):
        db = str(tmp_path / "test.sqlite")
        init_and_migrate(db)
        con = sqlite3.connect(db)
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        con.close()
        assert "_schema_migrations" in tables


# ── error hierarchy ──────────────────────────────────────────────────

class TestErrors:
    def test_all_inherit_from_base(self):
        for cls in [RecapNotFoundError, RecapStateError, RecapDataError,
                    ChronicleError, ConfigError, SchemaError]:
            assert issubclass(cls, SquadVaultError)
            assert issubclass(cls, Exception)

    def test_base_is_exception(self):
        assert issubclass(SquadVaultError, Exception)

    def test_can_raise_and_catch(self):
        with pytest.raises(SquadVaultError):
            raise RecapNotFoundError("test")

    def test_message_preserved(self):
        try:
            raise RecapDataError("missing data")
        except SquadVaultError as e:
            assert str(e) == "missing data"

    def test_specific_catch(self):
        with pytest.raises(ChronicleError):
            raise ChronicleError("chronicle fail")
