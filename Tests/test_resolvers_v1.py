"""Tests for squadvault.core.resolvers.

Covers: _csv_ids, PlayerResolver, FranchiseResolver — load, resolve, fail-safe.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.resolvers import FranchiseResolver, PlayerResolver, _csv_ids

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.execute(
        "INSERT INTO player_directory (league_id, season, player_id, name, position, team) VALUES (?, ?, ?, ?, ?, ?)",
        (LEAGUE, SEASON, "P100", "Patrick Mahomes", "QB", "KC"),
    )
    con.execute(
        "INSERT INTO player_directory (league_id, season, player_id, name, position, team) VALUES (?, ?, ?, ?, ?, ?)",
        (LEAGUE, SEASON, "P200", "Tyreek Hill", "WR", "MIA"),
    )
    con.execute(
        "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?, ?, ?, ?)",
        (LEAGUE, SEASON, "0001", "Taco Tuesday"),
    )
    con.execute(
        "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?, ?, ?, ?)",
        (LEAGUE, SEASON, "0002", "Monday Night Crew"),
    )
    con.commit()
    con.close()
    return db_path


# ── _csv_ids ─────────────────────────────────────────────────────────

class TestCsvIds:
    def test_none(self):
        assert _csv_ids(None) == []

    def test_empty_string(self):
        assert _csv_ids("") == []

    def test_single_id(self):
        assert _csv_ids("P100") == ["P100"]

    def test_csv(self):
        assert _csv_ids("P100,P200") == ["P100", "P200"]

    def test_trailing_comma(self):
        assert _csv_ids("P100,") == ["P100"]

    def test_list_input(self):
        assert _csv_ids(["P100", "P200"]) == ["P100", "P200"]

    def test_list_with_empty(self):
        assert _csv_ids(["P100", "", "P200"]) == ["P100", "P200"]

    def test_int_input(self):
        assert _csv_ids(42) == ["42"]

    def test_whitespace_stripped(self):
        assert _csv_ids(" P100 , P200 ") == ["P100", "P200"]


# ── PlayerResolver ───────────────────────────────────────────────────

class TestPlayerResolver:
    def test_resolves_known_player(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"P100"})
        assert "Patrick Mahomes" in r.one("P100")
        assert "QB" in r.one("P100")

    def test_unknown_returns_raw_id(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"P999"})
        assert r.one("P999") == "P999"

    def test_none_returns_placeholder(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids(set())
        assert r.one(None) == "<?>"

    def test_empty_returns_placeholder(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids(set())
        assert r.one("") == "<?>"

    def test_many_resolves_list(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"P100", "P200"})
        names = r.many("P100,P200")
        assert len(names) == 2
        assert "Patrick Mahomes" in names[0]

    def test_requested_and_resolved_counts(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"P100", "P200", "P999"})
        assert r.requested == 3
        assert r.resolved == 2

    def test_load_idempotent(self, db):
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"P100"})
        r.load_for_ids({"P200"})  # should be no-op
        assert r.requested == 1  # only first call counted

    def test_missing_table_safe(self, tmp_path):
        """No player_directory table → loads but resolves nothing."""
        db = str(tmp_path / "empty.sqlite")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE dummy (x TEXT)")
        con.commit()
        con.close()
        r = PlayerResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"P100"})
        assert r.one("P100") == "P100"


# ── FranchiseResolver ────────────────────────────────────────────────

class TestFranchiseResolver:
    def test_resolves_known_franchise(self, db):
        r = FranchiseResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"0001"})
        assert r.one("0001") == "Taco Tuesday"

    def test_unknown_returns_raw_id(self, db):
        r = FranchiseResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"9999"})
        assert r.one("9999") == "9999"

    def test_none_returns_placeholder(self, db):
        r = FranchiseResolver(db, LEAGUE, SEASON)
        r.load_for_ids(set())
        assert r.one(None) == "?"

    def test_requested_and_resolved_counts(self, db):
        r = FranchiseResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"0001", "0002", "9999"})
        assert r.requested == 3
        assert r.resolved == 2

    def test_load_idempotent(self, db):
        r = FranchiseResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"0001"})
        r.load_for_ids({"0002"})  # no-op
        assert r.requested == 1

    def test_missing_table_safe(self, tmp_path):
        db = str(tmp_path / "empty.sqlite")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE dummy (x TEXT)")
        con.commit()
        con.close()
        r = FranchiseResolver(db, LEAGUE, SEASON)
        r.load_for_ids({"0001"})
        assert r.one("0001") == "0001"
