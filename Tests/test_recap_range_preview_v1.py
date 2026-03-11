"""Tests for squadvault.consumers.recap_range_preview pure functions.

Covers: _score_event, _dedupe_key, _pick_notable, _extract_trade_fields,
format_headline, _as_float, _csv_ids, _collect_player_ids_from_events,
_collect_franchise_ids_from_events.
"""
from __future__ import annotations

import pytest

from squadvault.consumers.recap_range_preview import (
    _as_float,
    _csv_ids,
    _collect_franchise_ids_from_events,
    _collect_player_ids_from_events,
    _dedupe_key,
    _extract_trade_fields,
    _pick_notable,
    _score_event,
    format_headline,
)


# ── _as_float ────────────────────────────────────────────────────────

class TestAsFloat:
    def test_normal_float(self):
        assert _as_float(3.14) == 3.14

    def test_string_float(self):
        assert _as_float("42.5") == 42.5

    def test_integer(self):
        assert _as_float(10) == 10.0

    def test_none_returns_default(self):
        assert _as_float(None) == 0.0

    def test_garbage_returns_default(self):
        assert _as_float("abc", 99.0) == 99.0


# ── _csv_ids ─────────────────────────────────────────────────────────

class TestCsvIds:
    def test_comma_separated(self):
        assert _csv_ids("1,2,3") == ["1", "2", "3"]

    def test_trailing_comma(self):
        assert _csv_ids("15754,") == ["15754"]

    def test_already_list(self):
        assert _csv_ids(["a", "b"]) == ["a", "b"]

    def test_none_returns_empty(self):
        assert _csv_ids(None) == []

    def test_empty_string(self):
        assert _csv_ids("") == []

    def test_single_value(self):
        assert _csv_ids("42") == ["42"]


# ── _score_event ─────────────────────────────────────────────────────

class TestScoreEvent:
    def test_trade_highest(self):
        assert _score_event({"event_type": "TRANSACTION_TRADE"}) == 120.0

    def test_waiver_bid_scales_with_amount(self):
        score = _score_event({
            "event_type": "WAIVER_BID_AWARDED",
            "payload": {"bid_amount": 25},
        })
        assert score == 40.0 + min(60.0, 25 * 2.0)

    def test_waiver_bid_no_amount(self):
        score = _score_event({
            "event_type": "WAIVER_BID_AWARDED",
            "payload": {},
        })
        assert score == 40.0

    def test_free_agent(self):
        assert _score_event({"event_type": "TRANSACTION_FREE_AGENT"}) == 15.0

    def test_unknown_type_zero(self):
        assert _score_event({"event_type": "TRANSACTION_LOCK_ALL_PLAYERS"}) == 0.0

    def test_missing_type_zero(self):
        assert _score_event({}) == 0.0


# ── _dedupe_key ──────────────────────────────────────────────────────

class TestDedupeKey:
    def test_trade_uses_raw_json(self):
        key = _dedupe_key({
            "event_type": "TRANSACTION_TRADE",
            "payload": {"raw_mfl_json": '{"a":1}'},
        })
        assert key == 'TRADE:{"a":1}'

    def test_non_trade_uses_source_id(self):
        key = _dedupe_key({
            "event_type": "WAIVER_BID_AWARDED",
            "external_source": "mfl",
            "external_id": "evt_123",
        })
        assert key == "mfl:evt_123"


# ── _pick_notable ────────────────────────────────────────────────────

class TestPickNotable:
    def test_empty_input(self):
        assert _pick_notable([], 10) == []

    def test_respects_max_items(self):
        events = [
            {"event_type": "TRANSACTION_TRADE", "external_source": "x", "external_id": f"t{i}",
             "payload": {"raw_mfl_json": f'{{"id":{i}}}'}}
            for i in range(10)
        ]
        result = _pick_notable(events, 3)
        assert len(result) == 3

    def test_trades_ranked_above_free_agents(self):
        events = [
            {"event_type": "TRANSACTION_FREE_AGENT", "external_source": "x", "external_id": "fa1"},
            {"event_type": "TRANSACTION_TRADE", "external_source": "x", "external_id": "t1",
             "payload": {"raw_mfl_json": '{"x":1}'}},
        ]
        result = _pick_notable(events, 5)
        assert result[0]["event_type"] == "TRANSACTION_TRADE"

    def test_deduplicates(self):
        events = [
            {"event_type": "TRANSACTION_TRADE", "external_source": "x", "external_id": "t1",
             "payload": {"raw_mfl_json": '{"same":"data"}'}},
            {"event_type": "TRANSACTION_TRADE", "external_source": "x", "external_id": "t2",
             "payload": {"raw_mfl_json": '{"same":"data"}'}},
        ]
        result = _pick_notable(events, 10)
        assert len(result) == 1

    def test_zero_score_events_excluded(self):
        events = [
            {"event_type": "TRANSACTION_LOCK_ALL_PLAYERS", "external_source": "x", "external_id": "l1"},
        ]
        result = _pick_notable(events, 10)
        assert result == []


# ── _extract_trade_fields ────────────────────────────────────────────

class TestExtractTradeFields:
    def test_direct_payload_fields(self):
        payload = {
            "franchise_id": "F1",
            "franchise2": "F2",
            "franchise1_gave_up": "P1,P2",
            "franchise2_gave_up": "P3",
        }
        f1, f2, gave1, gave2 = _extract_trade_fields(payload)
        assert f1 == "F1"
        assert f2 == "F2"
        assert gave1 == ["P1", "P2"]
        assert gave2 == ["P3"]

    def test_missing_fields_return_question_marks(self):
        f1, f2, gave1, gave2 = _extract_trade_fields({})
        assert f1 == "?"
        assert f2 == "?"

    def test_raw_mfl_json_fallback(self):
        import json
        payload = {
            "raw_mfl_json": json.dumps({
                "franchise": "F1",
                "franchise2": "F2",
                "franchise1_gave_up": "P1",
                "franchise2_gave_up": "P2",
            })
        }
        f1, f2, gave1, gave2 = _extract_trade_fields(payload)
        assert f1 == "F1"
        assert f2 == "F2"


# ── format_headline ──────────────────────────────────────────────────

class TestFormatHeadline:
    def test_trade_headline(self):
        e = {
            "event_type": "TRANSACTION_TRADE",
            "payload": {
                "franchise_id": "F1",
                "franchise2": "F2",
                "franchise1_gave_up": "P1",
                "franchise2_gave_up": "P2",
            },
        }
        result = format_headline(e)
        assert "TRADE" in result
        assert "F1" in result
        assert "F2" in result

    def test_waiver_win_headline(self):
        e = {
            "event_type": "WAIVER_BID_AWARDED",
            "payload": {
                "franchise_id": "F3",
                "bid_amount": 25.0,
                "player_id": "P100",
            },
        }
        result = format_headline(e)
        assert "WAIVER WIN" in result
        assert "F3" in result
        assert "$25.00" in result

    def test_free_agent_headline(self):
        e = {
            "event_type": "TRANSACTION_FREE_AGENT",
            "payload": {
                "franchise_id": "F4",
                "players_added_ids": ["P200"],
            },
        }
        result = format_headline(e)
        assert "FREE AGENT" in result
        assert "F4" in result

    def test_unknown_type_fallback(self):
        e = {"event_type": "SOME_NEW_TYPE", "payload": {"franchise_id": "F5"}}
        result = format_headline(e)
        assert "SOME_NEW_TYPE" in result


# ── _collect_*_ids_from_events ───────────────────────────────────────

class TestCollectIds:
    def test_collect_player_ids(self):
        events = [
            {"payload": {"player_id": "P1"}},
            {"payload": {"players_added_ids": ["P2", "P3"]}},
            {"payload": {}},
        ]
        ids = _collect_player_ids_from_events(events)
        assert "P1" in ids
        assert "P2" in ids
        assert "P3" in ids

    def test_collect_franchise_ids(self):
        events = [
            {"payload": {"franchise_id": "F1"}},
            {"payload": {"franchise2": "F3"}},
        ]
        ids = _collect_franchise_ids_from_events(events)
        assert "F1" in ids
        assert "F3" in ids

    def test_empty_events(self):
        assert _collect_player_ids_from_events([]) == set()
        assert _collect_franchise_ids_from_events([]) == set()
