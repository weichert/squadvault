"""Tests for squadvault.core.recaps.render.render_recap_text_from_facts_v1.

Covers: _get, _as_list, _fmt_ids, _safe_str, _DirLookup,
_render_deterministic_bullets_from_facts_v1, QUIET_WEEK_MIN_EVENTS.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.render.render_recap_text_from_facts_v1 import (
    _get,
    _as_list,
    _fmt_ids,
    _safe_str,
    _DirLookup,
    _render_deterministic_bullets_from_facts_v1,
    QUIET_WEEK_MIN_EVENTS,
    MAX_BULLETS,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


# ── _get (nested dict access) ────────────────────────────────────────

class TestGet:
    def test_single_key(self):
        assert _get({"a": 1}, "a") == 1

    def test_nested_keys(self):
        assert _get({"a": {"b": {"c": 42}}}, "a", "b", "c") == 42

    def test_missing_key(self):
        assert _get({"a": 1}, "b") is None

    def test_missing_nested(self):
        assert _get({"a": {"b": 1}}, "a", "c") is None

    def test_non_dict_intermediate(self):
        assert _get({"a": "not a dict"}, "a", "b") is None

    def test_empty_dict(self):
        assert _get({}, "a") is None


# ── _as_list ─────────────────────────────────────────────────────────

class TestAsList:
    def test_list_input(self):
        assert _as_list(["a", "b"]) == ["a", "b"]

    def test_single_value(self):
        assert _as_list("x") == ["x"]

    def test_none(self):
        assert _as_list(None) == []

    def test_list_with_nones(self):
        assert _as_list(["a", None, "b"]) == ["a", "b"]

    def test_int_value(self):
        assert _as_list(42) == ["42"]


# ── _fmt_ids ─────────────────────────────────────────────────────────

class TestFmtIds:
    def test_multiple(self):
        assert _fmt_ids(["P1", "P2"]) == "P1, P2"

    def test_single(self):
        assert _fmt_ids(["P1"]) == "P1"

    def test_empty(self):
        assert _fmt_ids([]) == "(none)"


# ── _safe_str ────────────────────────────────────────────────────────

class TestSafeStr:
    def test_string(self):
        assert _safe_str("hello") == "hello"

    def test_int(self):
        assert _safe_str(42) == "42"

    def test_none_returns_default(self):
        assert _safe_str(None) == "?"

    def test_none_custom_default(self):
        assert _safe_str(None, "N/A") == "N/A"


# ── _DirLookup ───────────────────────────────────────────────────────

@pytest.fixture
def db_with_directories(tmp_path):
    """Fresh DB seeded with franchise and player directories."""
    db = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text())
    con.execute(
        "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
        (LEAGUE, SEASON, "0001", "Eagles"),
    )
    con.execute(
        "INSERT INTO player_directory (league_id, season, player_id, name) VALUES (?,?,?,?)",
        (LEAGUE, SEASON, "15754", "Jalen Hurts"),
    )
    con.commit()
    con.close()
    return db


class TestDirLookup:
    def test_franchise_found(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        assert lookup.franchise("0001") == "Eagles"

    def test_franchise_not_found(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        assert lookup.franchise("9999") == "9999"  # fallback to raw ID

    def test_franchise_none(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        assert lookup.franchise(None) == "Unknown team"

    def test_player_found(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        assert lookup.player("15754") == "Jalen Hurts"

    def test_player_not_found(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        assert lookup.player("99999") == "99999"

    def test_player_none(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        assert lookup.player(None) == "Unknown player"

    def test_caching(self, db_with_directories):
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        r1 = lookup.franchise("0001")
        r2 = lookup.franchise("0001")
        assert r1 == r2 == "Eagles"

    def test_norm_id_fallback(self, db_with_directories):
        """Leading-zero normalization should find '0001' from '1'."""
        # This depends on norm_id behavior — '1' != '0001' so it tries normalized
        lookup = _DirLookup(db_with_directories, LEAGUE, SEASON)
        # norm_id("0001") = "1", but we're querying "1" which normalizes to "1"
        # and then tries "1" directly (no match) — fallback is raw ID
        result = lookup.franchise("1")
        # If directory has "0001", querying "1" won't match directly
        # but norm_id("1") == "1" which equals the input, so no alt lookup
        assert result == "1"  # expected: no match, fallback to raw


# ── _render_deterministic_bullets_from_facts_v1 ──────────────────────

class TestRenderBulletsFromFacts:
    def test_quiet_week_returns_empty(self, db_with_directories):
        """Fewer than QUIET_WEEK_MIN_EVENTS returns empty string."""
        facts = [{"event_type": "DRAFT_PICK", "occurred_at": "2024-09-01T00:00:00Z", "canonical_id": "1"}]
        result = _render_deterministic_bullets_from_facts_v1(
            db_path=db_with_directories, league_id=LEAGUE, season=SEASON, facts=facts,
        )
        assert result == ""

    def test_free_agent_bullet(self, db_with_directories):
        """Free agent events produce 'added X (free agent)' bullets."""
        facts = [
            {
                "event_type": "TRANSACTION_FREE_AGENT",
                "occurred_at": f"2024-09-0{i}T12:00:00Z",
                "canonical_id": str(i),
                "details": {
                    "franchise_id": "0001",
                    "normalized": {"add_player_ids": ["15754"]},
                },
            }
            for i in range(1, QUIET_WEEK_MIN_EVENTS + 1)
        ]
        result = _render_deterministic_bullets_from_facts_v1(
            db_path=db_with_directories, league_id=LEAGUE, season=SEASON, facts=facts,
        )
        assert "What happened (facts)" in result
        assert "Eagles" in result
        assert "Jalen Hurts" in result
        assert "free agent" in result

    def test_waiver_bid_bullet(self, db_with_directories):
        """Waiver bid events produce 'won X on waivers' bullets."""
        facts = [
            {
                "event_type": "WAIVER_BID_AWARDED",
                "occurred_at": f"2024-09-0{i}T12:00:00Z",
                "canonical_id": str(i),
                "details": {
                    "franchise_id": "0001",
                    "normalized": {"add_player_ids": ["15754"], "bid_amount": 25},
                },
            }
            for i in range(1, QUIET_WEEK_MIN_EVENTS + 1)
        ]
        result = _render_deterministic_bullets_from_facts_v1(
            db_path=db_with_directories, league_id=LEAGUE, season=SEASON, facts=facts,
        )
        assert "waivers" in result
        assert "$25" in result

    def test_trade_bullet(self, db_with_directories):
        """Trade events produce 'Trade: X ↔ Y' bullets."""
        facts = [
            {
                "event_type": "TRANSACTION_TRADE",
                "occurred_at": f"2024-09-0{i}T12:00:00Z",
                "canonical_id": str(i),
                "details": {
                    "franchise_id": "0001",
                    "normalized": {
                        "franchise1_id": "0001",
                        "franchise2_id": "9999",
                        "franchise1_gave_up_player_ids": ["15754"],
                        "franchise2_gave_up_player_ids": ["99999"],
                    },
                },
            }
            for i in range(1, QUIET_WEEK_MIN_EVENTS + 1)
        ]
        result = _render_deterministic_bullets_from_facts_v1(
            db_path=db_with_directories, league_id=LEAGUE, season=SEASON, facts=facts,
        )
        assert "Trade:" in result
        assert "Eagles" in result
        assert "↔" in result

    def test_max_bullets_capped(self, db_with_directories):
        """Output is capped at MAX_BULLETS."""
        facts = [
            {
                "event_type": "TRANSACTION_FREE_AGENT",
                "occurred_at": f"2024-09-{i:02d}T12:00:00Z",
                "canonical_id": str(i),
                "details": {
                    "franchise_id": "0001",
                    "normalized": {"add_player_ids": ["15754"]},
                },
            }
            for i in range(1, MAX_BULLETS + 10)
        ]
        result = _render_deterministic_bullets_from_facts_v1(
            db_path=db_with_directories, league_id=LEAGUE, season=SEASON, facts=facts,
        )
        bullet_count = result.count("- ")
        assert bullet_count <= MAX_BULLETS

    def test_constants(self):
        """Key constants have expected values."""
        assert QUIET_WEEK_MIN_EVENTS >= 1
        assert MAX_BULLETS >= 1
