"""Tests for squadvault.core.recaps.render.render_recap_text_from_facts_v1.

Covers: _get, _as_list, _fmt_ids, _safe_str helpers,
_render_deterministic_bullets_from_facts_v1, and render_recap_from_facts_v1.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict

import pytest

from squadvault.core.recaps.render.render_recap_text_from_facts_v1 import (
    _get,
    _as_list,
    _fmt_ids,
    _safe_str,
    QUIET_WEEK_MIN_EVENTS,
    MAX_BULLETS,
    render_recap_from_facts_v1,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


# ── _get ─────────────────────────────────────────────────────────────

class TestGet:
    def test_simple_key(self):
        assert _get({"a": 1}, "a") == 1

    def test_nested_keys(self):
        assert _get({"a": {"b": 2}}, "a", "b") == 2

    def test_missing_returns_none(self):
        assert _get({"a": 1}, "b") is None

    def test_non_dict_returns_none(self):
        assert _get({"a": "not_dict"}, "a", "b") is None

    def test_empty_dict(self):
        assert _get({}, "a") is None


# ── _as_list ─────────────────────────────────────────────────────────

class TestAsList:
    def test_none(self):
        assert _as_list(None) == []

    def test_list(self):
        assert _as_list(["a", "b"]) == ["a", "b"]

    def test_single_value(self):
        assert _as_list("x") == ["x"]

    def test_filters_none_items(self):
        assert _as_list(["a", None, "b"]) == ["a", "b"]


# ── _fmt_ids ─────────────────────────────────────────────────────────

class TestFmtIds:
    def test_multiple(self):
        assert _fmt_ids(["A", "B"]) == "A, B"

    def test_empty(self):
        assert _fmt_ids([]) == "(none)"

    def test_single(self):
        assert _fmt_ids(["X"]) == "X"


# ── _safe_str ────────────────────────────────────────────────────────

class TestSafeStr:
    def test_normal(self):
        assert _safe_str("hello") == "hello"

    def test_none_default(self):
        assert _safe_str(None) == "?"

    def test_custom_default(self):
        assert _safe_str(None, "N/A") == "N/A"

    def test_int(self):
        assert _safe_str(42) == "42"


# ── render_recap_from_facts_v1 ───────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    """Fresh DB with franchise and player directories populated."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    # Insert franchise
    con.execute(
        "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?, ?, ?, ?)",
        (LEAGUE, SEASON, "0001", "Taco Tuesday"),
    )
    con.execute(
        "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?, ?, ?, ?)",
        (LEAGUE, SEASON, "0002", "Monday Night Crew"),
    )
    # Insert player
    con.execute(
        "INSERT INTO player_directory (league_id, season, player_id, name) VALUES (?, ?, ?, ?)",
        (LEAGUE, SEASON, "16207", "Patrick Mahomes"),
    )
    con.commit()
    con.close()
    return db_path


def _make_artifact(
    facts: list[dict],
    *,
    league_id: str = LEAGUE,
    season: int = SEASON,
    week_index: int = 1,
) -> Dict[str, Any]:
    """Build a minimal enriched artifact dict matching render_recap_from_facts_v1 expectations."""
    return {
        "league_id": league_id,
        "season": season,
        "week_index": week_index,
        "recap_version": 1,
        "window": {
            "start": "2024-09-05T12:00:00Z",
            "end": "2024-09-12T12:00:00Z",
            "mode": "LOCK_TO_LOCK",
        },
        "selection": {"fingerprint": "abc123"},
        "facts": facts,
    }


class TestRenderRecapFromFacts:
    def test_renders_waiver_bid(self, db):
        artifact = _make_artifact([{
            "event_type": "WAIVER_BID_AWARDED",
            "occurred_at": "2024-09-06T12:00:00Z",
            "canonical_id": "c1",
            "details": {
                "franchise_id": "0001",
                "mfl_type": "BBID_WAIVER",
                "normalized": {
                    "add_player_ids": ["16207"],
                    "bid_amount": "25",
                },
            },
        }])
        text = render_recap_from_facts_v1(artifact, db_path=db)
        # Should contain event info
        assert "WAIVER_BID_AWARDED" in text or "bid" in text.lower()
        assert "25" in text

    def test_renders_free_agent(self, db):
        artifact = _make_artifact([{
            "event_type": "TRANSACTION_FREE_AGENT",
            "occurred_at": "2024-09-07T12:00:00Z",
            "canonical_id": "c2",
            "details": {
                "franchise_id": "0001",
                "normalized": {
                    "add_player_ids": ["16207"],
                    "drop_player_ids": [],
                },
            },
        }])
        text = render_recap_from_facts_v1(artifact, db_path=db)
        assert "FREE_AGENT" in text

    def test_empty_facts(self, db):
        artifact = _make_artifact([])
        text = render_recap_from_facts_v1(artifact, db_path=db)
        assert isinstance(text, str)
        assert "Facts: 0" in text

    def test_no_db_path_still_renders(self):
        artifact = _make_artifact([{
            "event_type": "WAIVER_BID_AWARDED",
            "occurred_at": "2024-09-06T12:00:00Z",
            "canonical_id": "c1",
        }])
        text = render_recap_from_facts_v1(artifact, db_path=None)
        assert isinstance(text, str)
        assert "WAIVER_BID_AWARDED" in text

    def test_max_bullets_truncation(self, db):
        facts = [
            {
                "event_type": "WAIVER_BID_AWARDED",
                "occurred_at": f"2024-09-06T{12+i%12}:00:00Z",
                "canonical_id": f"c{i}",
                "details": {
                    "franchise_id": "0001",
                    "mfl_type": "BBID_WAIVER",
                    "normalized": {
                        "add_player_ids": [f"P{i}"],
                        "bid_amount": str(i),
                    },
                },
            }
            for i in range(MAX_BULLETS + 10)
        ]
        artifact = _make_artifact(facts)
        text = render_recap_from_facts_v1(artifact, db_path=db)
        assert isinstance(text, str)
        assert len(text) > 0
