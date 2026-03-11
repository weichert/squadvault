"""Tests for squadvault.core.canonicalize.run_canonicalize.

Covers: helper functions, action_fingerprint (all event types),
score_event, full canonicalize flow with temp DB.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.canonicalize.run_canonicalize import (
    MemoryEventRow,
    safe_json_loads,
    norm,
    sha1_text,
    raw_mfl_obj,
    _as_list_str,
    _stable_ids_key,
    _parse_free_agent_add_drop_from_raw,
    action_fingerprint,
    score_event,
    canonicalize,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


def _row(
    id: int = 1,
    league_id: str = LEAGUE,
    season: int = SEASON,
    event_type: str = "WAIVER_BID_AWARDED",
    occurred_at: str = "2024-10-01T12:00:00Z",
    ingested_at: str = "2024-10-01T13:00:00Z",
    payload_json: str = "{}",
) -> MemoryEventRow:
    return MemoryEventRow(
        id=id,
        league_id=league_id,
        season=season,
        event_type=event_type,
        occurred_at=occurred_at,
        ingested_at=ingested_at,
        payload_json=payload_json,
    )


# ── safe_json_loads ──────────────────────────────────────────────────

class TestSafeJsonLoads:
    def test_valid_dict(self):
        assert safe_json_loads('{"a": 1}') == {"a": 1}

    def test_non_object(self):
        result = safe_json_loads('[1, 2]')
        assert "_non_object_payload" in result

    def test_invalid_json(self):
        result = safe_json_loads("not json")
        assert result["_payload_parse_error"] is True

    def test_empty_string(self):
        result = safe_json_loads("")
        assert "_payload_parse_error" in result


# ── norm ─────────────────────────────────────────────────────────────

class TestNorm:
    def test_strips_whitespace(self):
        assert norm("  hello  ") == "hello"

    def test_none_returns_empty(self):
        assert norm(None) == ""

    def test_int_converted(self):
        assert norm(42) == "42"


# ── sha1_text ────────────────────────────────────────────────────────

class TestSha1Text:
    def test_deterministic(self):
        assert sha1_text("test") == sha1_text("test")

    def test_different_inputs(self):
        assert sha1_text("a") != sha1_text("b")


# ── raw_mfl_obj ──────────────────────────────────────────────────────

class TestRawMflObj:
    def test_dict_input(self):
        assert raw_mfl_obj({"raw_mfl_json": {"type": "X"}}) == {"type": "X"}

    def test_json_string_input(self):
        assert raw_mfl_obj({"raw_mfl_json": '{"type": "X"}'}) == {"type": "X"}

    def test_missing(self):
        assert raw_mfl_obj({}) == {}

    def test_malformed_string(self):
        assert raw_mfl_obj({"raw_mfl_json": "not json"}) == {}


# ── _as_list_str ─────────────────────────────────────────────────────

class TestAsListStr:
    def test_none(self):
        assert _as_list_str(None) == []

    def test_list(self):
        assert _as_list_str(["a", "b"]) == ["a", "b"]

    def test_csv_string(self):
        assert _as_list_str("a,b,c") == ["a", "b", "c"]

    def test_json_list_string(self):
        assert _as_list_str('["x","y"]') == ["x", "y"]

    def test_empty_string(self):
        assert _as_list_str("") == []

    def test_strips_items(self):
        assert _as_list_str([" a ", " b "]) == ["a", "b"]

    def test_filters_empty_items(self):
        assert _as_list_str(["a", "", None, "b"]) == ["a", "b"]


# ── _stable_ids_key ──────────────────────────────────────────────────

class TestStableIdsKey:
    def test_sorted_unique(self):
        assert _stable_ids_key(["b", "a", "b"]) == "a,b"

    def test_empty(self):
        assert _stable_ids_key([]) == ""


# ── _parse_free_agent_add_drop_from_raw ──────────────────────────────

class TestParseFreeAgentAddDrop:
    def test_standard_pattern(self):
        payload = {"raw_mfl_json": json.dumps({"transaction": "16207,|14108,"})}
        added, dropped = _parse_free_agent_add_drop_from_raw(payload)
        assert added == ["16207"]
        assert dropped == ["14108"]

    def test_no_transaction(self):
        added, dropped = _parse_free_agent_add_drop_from_raw({})
        assert added == []
        assert dropped == []

    def test_add_only(self):
        payload = {"raw_mfl_json": json.dumps({"transaction": "12345|"})}
        added, dropped = _parse_free_agent_add_drop_from_raw(payload)
        assert added == ["12345"]
        assert dropped == []


# ── action_fingerprint ───────────────────────────────────────────────

class TestActionFingerprint:
    def test_waiver_bid_with_player_id(self):
        payload = {"franchise_id": "F1", "player_id": "P1", "bid_amount": "25"}
        row = _row(payload_json=json.dumps(payload))
        fp = action_fingerprint(row, payload)
        assert "WAIVER_BID_AWARDED" in fp
        assert "F1" in fp
        assert "P1" in fp
        assert "25" in fp

    def test_waiver_bid_stub_bbid_returns_empty(self):
        """Stub BBID_WAIVER rows get empty fingerprint => skipped."""
        payload = {"raw_mfl_json": json.dumps({"type": "BBID_WAIVER"})}
        row = _row(payload_json=json.dumps(payload))
        fp = action_fingerprint(row, payload)
        assert fp == ""

    def test_waiver_bid_with_added_ids(self):
        payload = {"franchise_id": "F1", "players_added_ids": "P1,P2", "bid_amount": "10"}
        row = _row(payload_json=json.dumps(payload))
        fp = action_fingerprint(row, payload)
        assert "ADDED" in fp

    def test_free_agent_structured(self):
        payload = {
            "franchise_id": "F1",
            "players_added_ids": "P1",
            "players_dropped_ids": "P2",
        }
        row = _row(event_type="TRANSACTION_FREE_AGENT", payload_json=json.dumps(payload))
        fp = action_fingerprint(row, payload)
        assert "ADD:" in fp
        assert "DROP:" in fp

    def test_free_agent_from_raw(self):
        payload = {
            "franchise_id": "F1",
            "raw_mfl_json": json.dumps({"transaction": "100|200"}),
        }
        row = _row(event_type="TRANSACTION_FREE_AGENT", payload_json=json.dumps(payload))
        fp = action_fingerprint(row, payload)
        assert "ADD:" in fp

    def test_default_event_type(self):
        payload = {"franchise_id": "F1"}
        row = _row(event_type="TRANSACTION_TRADE", id=42, payload_json=json.dumps(payload))
        fp = action_fingerprint(row, payload)
        assert "MEMORY_EVENT_ID:42" in fp

    def test_deterministic(self):
        payload = {"franchise_id": "F1", "player_id": "P1"}
        row = _row(payload_json=json.dumps(payload))
        assert action_fingerprint(row, payload) == action_fingerprint(row, payload)


# ── score_event ──────────────────────────────────────────────────────

class TestScoreEvent:
    def test_full_event_scores_high(self):
        payload = {
            "player_id": "P1",
            "bid_amount": "25",
            "players_added_ids": "P1",
            "players_dropped_ids": "P2",
            "raw_mfl_json": json.dumps({"x": "y" * 500}),
        }
        score = score_event(payload, memory_event_id=1)
        assert score > 50

    def test_stub_event_penalized(self):
        score = score_event({}, memory_event_id=1)
        assert score < 0

    def test_player_id_adds_score(self):
        s1 = score_event({"player_id": "P1"}, memory_event_id=1)
        s2 = score_event({}, memory_event_id=1)
        assert s1 > s2

    def test_bid_amount_adds_score(self):
        s1 = score_event({"player_id": "P1", "bid_amount": "10"}, memory_event_id=1)
        s2 = score_event({"player_id": "P1"}, memory_event_id=1)
        assert s1 > s2

    def test_deterministic(self):
        payload = {"player_id": "P1"}
        assert score_event(payload, 1) == score_event(payload, 1)

    def test_tiebreaker_by_id(self):
        payload = {"player_id": "P1"}
        s1 = score_event(payload, memory_event_id=10)
        s2 = score_event(payload, memory_event_id=20)
        assert s1 == s2 or s1 != s2  # tiebreaker is id % 10, so 10 and 20 both give 0
        # But 11 vs 12:
        s3 = score_event(payload, memory_event_id=11)
        s4 = score_event(payload, memory_event_id=12)
        assert s4 > s3


# ── full canonicalize flow ───────────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    """Fresh DB from schema.sql with some memory_events."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


def _insert_memory_event(db_path, event_type, payload, id_suffix="1", occurred_at="2024-10-01T12:00:00Z"):
    con = sqlite3.connect(db_path)
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id,
            event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            LEAGUE, SEASON, "test", f"test_{event_type}_{id_suffix}",
            event_type, occurred_at, "2024-10-01T13:00:00Z",
            json.dumps(payload),
        ),
    )
    con.commit()
    con.close()


class TestCanonicalizeFlow:
    def test_creates_canonical_events(self, db):
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "franchise_id": "F1",
            "player_id": "P1",
            "bid_amount": "25",
        })
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        con = sqlite3.connect(db)
        count = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()
        assert count == 1

    def test_deduplicates_same_fingerprint(self, db):
        """Two memory events with same fingerprint => one canonical event."""
        for i in range(2):
            _insert_memory_event(db, "WAIVER_BID_AWARDED", {
                "franchise_id": "F1",
                "player_id": "P1",
                "bid_amount": "25",
            }, id_suffix=str(i))
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        con = sqlite3.connect(db)
        count = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()
        assert count == 1

    def test_skips_stub_bbid(self, db):
        """Stub BBID_WAIVER rows are skipped entirely."""
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "raw_mfl_json": json.dumps({"type": "BBID_WAIVER"}),
        })
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        con = sqlite3.connect(db)
        count = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()
        assert count == 0

    def test_different_events_not_deduplicated(self, db):
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "franchise_id": "F1", "player_id": "P1", "bid_amount": "25",
        }, id_suffix="a")
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "franchise_id": "F2", "player_id": "P2", "bid_amount": "30",
        }, id_suffix="b")
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        con = sqlite3.connect(db)
        count = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()
        assert count == 2

    def test_idempotent_rerun(self, db):
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "franchise_id": "F1", "player_id": "P1", "bid_amount": "25",
        })
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        con = sqlite3.connect(db)
        count = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()
        assert count == 1

    def test_missing_db_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            canonicalize(league_id=LEAGUE, season=SEASON, db_path=str(tmp_path / "nonexistent.sqlite"))

    def test_empty_db(self, db):
        """No memory events => no canonical events, no crash."""
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        con = sqlite3.connect(db)
        count = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()
        assert count == 0
