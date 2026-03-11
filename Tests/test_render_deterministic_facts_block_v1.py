"""Tests for squadvault.core.recaps.render.render_deterministic_facts_block_v1

Covers: build_deterministic_facts_block_v1, _NameLookup, _norm_id,
_fetch_canonical_events_by_ids, _fetch_memory_payloads_by_ids,
quiet week threshold, empty IDs, chunked fetching.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import os

import pytest

from squadvault.core.recaps.render.render_deterministic_facts_block_v1 import (
    _fetch_canonical_events_by_ids,
    _fetch_memory_payloads_by_ids,
    _NameLookup,
    _norm_id,
    build_deterministic_facts_block_v1,
    QUIET_WEEK_MIN_EVENTS,
)

LEAGUE = "test_league"
SEASON = 2024


def _make_db(tmp_path: str) -> str:
    """Create a minimal DB with required tables and return path."""
    db_path = os.path.join(tmp_path, "test.sqlite")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE memory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            external_source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            occurred_at TEXT,
            ingested_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE canonical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            action_fingerprint TEXT NOT NULL,
            best_memory_event_id INTEGER NOT NULL,
            best_score INTEGER NOT NULL DEFAULT 0,
            selection_version INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            occurred_at TEXT,
            FOREIGN KEY(best_memory_event_id) REFERENCES memory_events(id)
        );
        CREATE TABLE franchise_directory (
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            franchise_id TEXT NOT NULL,
            name TEXT
        );
        CREATE TABLE player_directory (
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            player_id TEXT NOT NULL,
            name TEXT
        );
    """)
    conn.close()
    return db_path


def _insert_memory_event(conn, eid, league, season, event_type, payload, occurred_at="2024-10-01T12:00:00Z"):
    conn.execute(
        "INSERT INTO memory_events (id, league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json) VALUES (?,?,?,?,?,?,?,?,?)",
        (eid, league, season, "test", f"ext_{eid}", event_type, occurred_at, "2024-10-01T12:00:00Z", json.dumps(payload)),
    )


def _insert_canonical_event(conn, cid, league, season, event_type, mem_id, occurred_at="2024-10-01T12:00:00Z"):
    conn.execute(
        "INSERT INTO canonical_events (id, league_id, season, event_type, action_fingerprint, best_memory_event_id, updated_at, occurred_at) VALUES (?,?,?,?,?,?,?,?)",
        (cid, league, season, event_type, f"fp_{cid}", mem_id, "2024-10-01T12:00:00Z", occurred_at),
    )


# ── _norm_id ─────────────────────────────────────────────────────────

class TestNormId:
    def test_none(self):
        assert _norm_id(None) == ""

    def test_empty(self):
        assert _norm_id("") == ""

    def test_whitespace(self):
        assert _norm_id("   ") == ""

    def test_leading_zeros_stripped(self):
        assert _norm_id("0042") == "42"

    def test_all_zeros(self):
        assert _norm_id("000") == "0"

    def test_no_leading_zeros(self):
        assert _norm_id("123") == "123"

    def test_non_numeric(self):
        assert _norm_id("abc") == "abc"

    def test_integer_input(self):
        assert _norm_id(42) == "42"


# ── _fetch_canonical_events_by_ids ───────────────────────────────────

class TestFetchCanonicalEvents:
    def test_empty_ids(self):
        assert _fetch_canonical_events_by_ids("/nonexistent", LEAGUE, SEASON, []) == []

    def test_fetches_matching_rows(self, tmp_path):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        _insert_memory_event(conn, 1, LEAGUE, SEASON, "MATCHUP_RESULT", {"winner_franchise_id": "F1"})
        _insert_canonical_event(conn, 10, LEAGUE, SEASON, "MATCHUP_RESULT", 1)
        _insert_canonical_event(conn, 11, LEAGUE, SEASON, "TRADE", 1)
        conn.commit()
        conn.close()

        rows = _fetch_canonical_events_by_ids(db_path, LEAGUE, SEASON, [10])
        assert len(rows) == 1
        assert rows[0]["canonical_id"] == 10
        assert rows[0]["event_type"] == "MATCHUP_RESULT"

    def test_ignores_wrong_league(self, tmp_path):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        _insert_memory_event(conn, 1, "other_league", SEASON, "MATCHUP_RESULT", {})
        _insert_canonical_event(conn, 10, "other_league", SEASON, "MATCHUP_RESULT", 1)
        conn.commit()
        conn.close()

        rows = _fetch_canonical_events_by_ids(db_path, LEAGUE, SEASON, [10])
        assert rows == []


# ── _fetch_memory_payloads_by_ids ────────────────────────────────────

class TestFetchMemoryPayloads:
    def test_empty_ids(self):
        assert _fetch_memory_payloads_by_ids("/nonexistent", []) == {}

    def test_parses_json_payload(self, tmp_path):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        _insert_memory_event(conn, 1, LEAGUE, SEASON, "TRADE", {"from_franchise_id": "F1", "to_franchise_id": "F2"})
        conn.commit()
        conn.close()

        result = _fetch_memory_payloads_by_ids(db_path, [1])
        assert 1 in result
        assert result[1]["from_franchise_id"] == "F1"

    def test_invalid_json_returns_empty_dict(self, tmp_path):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO memory_events (id, league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json) VALUES (?,?,?,?,?,?,?,?,?)",
            (1, LEAGUE, SEASON, "test", "ext_1", "X", "2024-10-01", "2024-10-01", "NOT JSON"),
        )
        conn.commit()
        conn.close()

        result = _fetch_memory_payloads_by_ids(db_path, [1])
        assert result[1] == {}

    def test_non_dict_json_returns_empty(self, tmp_path):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO memory_events (id, league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json) VALUES (?,?,?,?,?,?,?,?,?)",
            (1, LEAGUE, SEASON, "test", "ext_1", "X", "2024-10-01", "2024-10-01", json.dumps([1, 2, 3])),
        )
        conn.commit()
        conn.close()

        result = _fetch_memory_payloads_by_ids(db_path, [1])
        assert result[1] == {}


# ── _NameLookup ──────────────────────────────────────────────────────

class TestNameLookup:
    def _setup_lookup(self, tmp_path, franchises=None, players=None):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        for fid, name in (franchises or []):
            conn.execute(
                "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
                (LEAGUE, SEASON, fid, name),
            )
        for pid, name in (players or []):
            conn.execute(
                "INSERT INTO player_directory (league_id, season, player_id, name) VALUES (?,?,?,?)",
                (LEAGUE, SEASON, pid, name),
            )
        conn.commit()
        conn.close()
        return _NameLookup(db_path, LEAGUE, SEASON)

    def test_franchise_found(self, tmp_path):
        lookup = self._setup_lookup(tmp_path, franchises=[("0001", "Eagles")])
        assert lookup.franchise_name("0001") == "Eagles"

    def test_franchise_not_found_returns_raw_id(self, tmp_path):
        lookup = self._setup_lookup(tmp_path)
        assert lookup.franchise_name("9999") == "9999"

    def test_franchise_normalized_fallback(self, tmp_path):
        """If exact match fails, tries normalized id (strip leading zeros)."""
        lookup = self._setup_lookup(tmp_path, franchises=[("1", "Eagles")])
        assert lookup.franchise_name("0001") == "Eagles"

    def test_franchise_none_returns_unknown(self, tmp_path):
        lookup = self._setup_lookup(tmp_path)
        assert lookup.franchise_name(None) == "Unknown team"

    def test_franchise_empty_returns_unknown(self, tmp_path):
        lookup = self._setup_lookup(tmp_path)
        assert lookup.franchise_name("") == "Unknown team"

    def test_player_found(self, tmp_path):
        lookup = self._setup_lookup(tmp_path, players=[("P100", "Joe Burrow")])
        assert lookup.player_name("P100") == "Joe Burrow"

    def test_player_not_found_returns_raw_id(self, tmp_path):
        lookup = self._setup_lookup(tmp_path)
        assert lookup.player_name("P999") == "P999"

    def test_player_none_returns_unknown(self, tmp_path):
        lookup = self._setup_lookup(tmp_path)
        assert lookup.player_name(None) == "Unknown player"

    def test_caching(self, tmp_path):
        """Second call hits cache, not DB."""
        lookup = self._setup_lookup(tmp_path, franchises=[("1", "Eagles")])
        assert lookup.franchise_name("1") == "Eagles"
        # Corrupt DB to prove cache is used
        os.remove(lookup.db_path)
        assert lookup.franchise_name("1") == "Eagles"


# ── build_deterministic_facts_block_v1 ───────────────────────────────

class TestBuildFactsBlock:
    def _setup_db(self, tmp_path, num_events=5):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)
        for i in range(1, num_events + 1):
            payload = {
                "winner_franchise_id": f"F{i}",
                "loser_franchise_id": f"F{i+10}",
                "winner_score": 100 + i,
                "loser_score": 80 + i,
            }
            _insert_memory_event(conn, i, LEAGUE, SEASON, "MATCHUP_RESULT", payload,
                                 occurred_at=f"2024-10-{i:02d}T12:00:00Z")
            _insert_canonical_event(conn, i, LEAGUE, SEASON, "MATCHUP_RESULT", i,
                                    occurred_at=f"2024-10-{i:02d}T12:00:00Z")
        conn.commit()
        conn.close()
        return db_path

    def test_below_quiet_threshold_returns_empty(self, tmp_path):
        db_path = self._setup_db(tmp_path, num_events=2)
        result = build_deterministic_facts_block_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            canonical_ids=[1, 2],
        )
        assert result == ""

    def test_empty_ids_returns_empty(self, tmp_path):
        db_path = self._setup_db(tmp_path, num_events=0)
        result = build_deterministic_facts_block_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            canonical_ids=[],
        )
        assert result == ""

    def test_normal_case_produces_header_and_bullets(self, tmp_path):
        db_path = self._setup_db(tmp_path, num_events=5)
        result = build_deterministic_facts_block_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            canonical_ids=[1, 2, 3, 4, 5],
        )
        assert result.startswith("What happened (facts)\n")
        assert result.endswith("\n\n")
        lines = result.strip().split("\n")
        # Header + 5 bullet lines
        assert len(lines) == 6
        for line in lines[1:]:
            assert line.startswith("- ")
            assert "beat" in line

    def test_name_resolution_from_directories(self, tmp_path):
        db_path = _make_db(str(tmp_path))
        conn = sqlite3.connect(db_path)

        payload = {"winner_franchise_id": "1", "loser_franchise_id": "2",
                    "winner_score": 110, "loser_score": 90}
        for i in range(1, QUIET_WEEK_MIN_EVENTS + 1):
            _insert_memory_event(conn, i, LEAGUE, SEASON, "MATCHUP_RESULT", payload,
                                 occurred_at=f"2024-10-{i:02d}T12:00:00Z")
            _insert_canonical_event(conn, i, LEAGUE, SEASON, "MATCHUP_RESULT", i,
                                    occurred_at=f"2024-10-{i:02d}T12:00:00Z")

        conn.execute("INSERT INTO franchise_directory VALUES (?,?,?,?)", (LEAGUE, SEASON, "1", "Eagles"))
        conn.execute("INSERT INTO franchise_directory VALUES (?,?,?,?)", (LEAGUE, SEASON, "2", "Hawks"))
        conn.commit()
        conn.close()

        result = build_deterministic_facts_block_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            canonical_ids=list(range(1, QUIET_WEEK_MIN_EVENTS + 1)),
        )
        assert "Eagles" in result
        assert "Hawks" in result

    def test_missing_canonical_ids_still_returns_available(self, tmp_path):
        """If some IDs don't exist in DB, only available ones produce bullets."""
        db_path = self._setup_db(tmp_path, num_events=5)
        result = build_deterministic_facts_block_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            canonical_ids=[1, 2, 3, 999, 998],  # 999, 998 don't exist
        )
        # 3 events found, exactly at threshold
        assert result.startswith("What happened (facts)\n")
        lines = [l for l in result.strip().split("\n") if l.startswith("- ")]
        assert len(lines) == 3
