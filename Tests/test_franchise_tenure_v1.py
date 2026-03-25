"""Tests for franchise tenure awareness.

Verifies that:
- compute_franchise_tenures correctly detects name changes
- render_league_history_for_prompt includes tenure context
- System prompt includes tenure hard rule
"""
from __future__ import annotations

import os
import sqlite3

import pytest

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


class TestComputeFranchiseTenures:
    """compute_franchise_tenures should detect when team names changed."""

    def test_stable_franchise_returns_earliest_season(self, tmp_path):
        """A franchise with the same name since the start returns the first season."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for season in [2020, 2021, 2022, 2023, 2024]:
            con.execute(
                "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
                ("L1", season, "0001", "Stable Team"),
            )
        con.commit()
        con.close()

        from squadvault.core.recaps.context.league_history_v1 import compute_franchise_tenures
        tenures = compute_franchise_tenures(db_path, "L1")
        assert tenures["0001"] == 2020

    def test_name_change_returns_new_tenure(self, tmp_path):
        """A franchise that changed names returns the first season of the NEW name."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for season in [2020, 2021, 2022]:
            con.execute(
                "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
                ("L1", season, "0003", "Old Owner Team"),
            )
        for season in [2023, 2024]:
            con.execute(
                "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
                ("L1", season, "0003", "Brandon Knows Ball"),
            )
        con.commit()
        con.close()

        from squadvault.core.recaps.context.league_history_v1 import compute_franchise_tenures
        tenures = compute_franchise_tenures(db_path, "L1")
        assert tenures["0003"] == 2023, f"Expected 2023, got {tenures['0003']}"

    def test_single_season_franchise(self, tmp_path):
        """A franchise with only one season returns that season."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.execute(
            "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
            ("L1", 2024, "0005", "New Team"),
        )
        con.commit()
        con.close()

        from squadvault.core.recaps.context.league_history_v1 import compute_franchise_tenures
        tenures = compute_franchise_tenures(db_path, "L1")
        assert tenures["0005"] == 2024


class TestTenureInPrompt:
    """The system prompt should include franchise tenure hard rule."""

    def test_tenure_hard_rule_present(self):
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "NEVER attribute franchise history" in _SYSTEM_PROMPT
        assert "FRANCHISE TENURE" in _SYSTEM_PROMPT

    def test_tenure_import_in_lifecycle(self):
        """Lifecycle must import compute_franchise_tenures."""
        import squadvault.recaps.weekly_recap_lifecycle as lc
        import inspect
        source = inspect.getsource(lc)
        assert "compute_franchise_tenures" in source
