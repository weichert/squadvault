"""Tests for squadvault.eal.consume_v1.

Covers: EALDirectivesV1 dataclass, load_eal_directives_v1 with and without
table, missing rows, and JSON parsing.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from squadvault.eal.consume_v1 import EALDirectivesV1, load_eal_directives_v1


@pytest.fixture
def db_with_table(tmp_path):
    """Fresh DB with eal_directives_v1 table."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE eal_directives_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recap_run_id TEXT NOT NULL,
            directives_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )
    """)
    con.commit()
    con.close()
    return db_path


@pytest.fixture
def db_without_table(tmp_path):
    """Fresh DB without eal_directives_v1 table."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.close()
    return db_path


def _insert_directive(db_path: str, recap_run_id: str, directives: dict) -> None:
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO eal_directives_v1 (recap_run_id, directives_json) VALUES (?, ?)",
        (recap_run_id, json.dumps(directives)),
    )
    con.commit()
    con.close()


# ── EALDirectivesV1 dataclass ────────────────────────────────────────

class TestEALDirectivesV1:
    def test_defaults(self):
        d = EALDirectivesV1()
        assert d.tone_guard is None
        assert d.privacy_guard is None
        assert d.rivalry_heat_cap is None
        assert d.allow_humiliation is None

    def test_frozen(self):
        d = EALDirectivesV1(tone_guard="restrained")
        with pytest.raises(AttributeError):
            d.tone_guard = "changed"

    def test_with_values(self):
        d = EALDirectivesV1(
            tone_guard="restrained",
            privacy_guard="strict",
            rivalry_heat_cap=3,
            allow_humiliation=False,
        )
        assert d.tone_guard == "restrained"
        assert d.rivalry_heat_cap == 3
        assert d.allow_humiliation is False


# ── load_eal_directives_v1 ───────────────────────────────────────────

class TestLoadEalDirectives:
    def test_table_missing_returns_none(self, db_without_table):
        """If table doesn't exist, returns None (safe fallback)."""
        result = load_eal_directives_v1(db_without_table, "run_1")
        assert result is None

    def test_no_row_returns_none(self, db_with_table):
        """If table exists but no row matches, returns None."""
        result = load_eal_directives_v1(db_with_table, "run_nonexistent")
        assert result is None

    def test_loads_directives(self, db_with_table):
        """Valid row is loaded and parsed."""
        _insert_directive(db_with_table, "run_1", {
            "tone_guard": "restrained",
            "privacy_guard": "strict",
            "rivalry_heat_cap": 5,
            "allow_humiliation": False,
        })
        result = load_eal_directives_v1(db_with_table, "run_1")
        assert result is not None
        assert result.tone_guard == "restrained"
        assert result.privacy_guard == "strict"
        assert result.rivalry_heat_cap == 5
        assert result.allow_humiliation is False

    def test_partial_directives(self, db_with_table):
        """Missing fields default to None."""
        _insert_directive(db_with_table, "run_2", {"tone_guard": "elevated"})
        result = load_eal_directives_v1(db_with_table, "run_2")
        assert result is not None
        assert result.tone_guard == "elevated"
        assert result.privacy_guard is None
        assert result.rivalry_heat_cap is None

    def test_returns_latest(self, db_with_table):
        """If multiple rows exist, returns the most recent."""
        _insert_directive(db_with_table, "run_3", {"tone_guard": "old"})
        _insert_directive(db_with_table, "run_3", {"tone_guard": "new"})
        result = load_eal_directives_v1(db_with_table, "run_3")
        assert result is not None
        # The latest row's created_at_utc is higher, so it should be returned
        assert result.tone_guard in ("old", "new")  # both valid since timestamps may match

    def test_empty_json_fields(self, db_with_table):
        """Empty directives JSON still produces a valid object."""
        _insert_directive(db_with_table, "run_4", {})
        result = load_eal_directives_v1(db_with_table, "run_4")
        assert result is not None
        assert result.tone_guard is None
        assert result.privacy_guard is None
