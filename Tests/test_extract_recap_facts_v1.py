"""Tests for squadvault.core.recaps.facts.extract_recap_facts_v1.

Covers: JSON parsing, raw MFL parsing, event-type-specific field extraction,
CSV ID splitting, detail routing.
"""
from __future__ import annotations

import json

import pytest

from squadvault.core.recaps.facts.extract_recap_facts_v1 import (
    EventFact,
    _extract_bbid_waiver_fields,
    _extract_details,
    _extract_free_agent_fields,
    _extract_trade_fields,
    _extract_waiver_bid_awarded_fields,
    _json_load,
    _parse_raw_mfl_json,
    _split_csv_ids,
)

# ── _json_load ───────────────────────────────────────────────────────

class TestJsonLoad:
    def test_valid_json_object(self):
        assert _json_load('{"a": 1}') == {"a": 1}

    def test_valid_json_non_object(self):
        result = _json_load('"just a string"')
        assert "_raw" in result

    def test_invalid_json(self):
        result = _json_load("not json at all")
        assert result.get("_parse_error") is True

    def test_empty_string(self):
        assert _json_load("") == {}

    def test_none_like(self):
        assert _json_load(None) == {}


# ── _parse_raw_mfl_json ─────────────────────────────────────────────

class TestParseRawMflJson:
    def test_nested_json_string(self):
        payload = {"raw_mfl_json": json.dumps({"type": "TRADE", "franchise": "F1"})}
        result = _parse_raw_mfl_json(payload)
        assert result["type"] == "TRADE"
        assert result["franchise"] == "F1"

    def test_already_dict(self):
        """If raw_mfl_json is a dict (not string), returns empty — only strings parsed."""
        payload = {"raw_mfl_json": {"type": "FREE_AGENT"}}
        result = _parse_raw_mfl_json(payload)
        assert result == {}  # Non-string raw_mfl_json is ignored

    def test_no_raw_mfl_json(self):
        assert _parse_raw_mfl_json({}) == {}

    def test_invalid_json_string(self):
        payload = {"raw_mfl_json": "not json"}
        result = _parse_raw_mfl_json(payload)
        assert result.get("_parse_error") is True or result == {}


# ── _split_csv_ids ───────────────────────────────────────────────────

class TestSplitCsvIds:
    def test_comma_separated(self):
        assert _split_csv_ids("1,2,3") == ["1", "2", "3"]

    def test_trailing_comma(self):
        assert _split_csv_ids("100,") == ["100"]

    def test_none(self):
        assert _split_csv_ids(None) == []

    def test_empty(self):
        assert _split_csv_ids("") == []

    def test_single(self):
        assert _split_csv_ids("42") == ["42"]

    def test_int_input(self):
        assert _split_csv_ids(42) == ["42"]


# ── _extract_bbid_waiver_fields ──────────────────────────────────────

class TestExtractBbidWaiverFields:
    def test_basic_fields(self):
        """Pre-promotion fallback: empty payload, raw carries all fields."""
        raw = {
            "transaction": "15754,|0.50|16149,",
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "timestamp": "1700000000",
        }
        result = _extract_bbid_waiver_fields({}, raw)
        assert result["add_player_ids"] == ["15754"]
        assert result["bid_amount"] == 0.5
        assert result["drop_player_ids"] == ["16149"]
        assert result["mfl_timestamp"] == 1700000000

    def test_missing_timestamp(self):
        """Pre-promotion fallback: raw has no timestamp, mfl_timestamp is None."""
        raw = {"transaction": "100,|5.00|"}
        result = _extract_bbid_waiver_fields({}, raw)
        assert "add_player_ids" in result
        assert result.get("mfl_timestamp") is None

    def test_canonical_path_populated(self):
        """S10: canonical payload fields populate normalized output; raw is not consulted."""
        payload = {
            "players_added_ids": ["CANON_ADD"],
            "players_dropped_ids": ["CANON_DROP"],
            "bid_amount": 99.5,
            "mfl_timestamp": 1234567890,
        }
        # Empty raw: canonical path must supply everything.
        result = _extract_bbid_waiver_fields(payload, {})
        assert result["add_player_ids"] == ["CANON_ADD"]
        assert result["drop_player_ids"] == ["CANON_DROP"]
        assert result["bid_amount"] == 99.5
        assert result["mfl_timestamp"] == 1234567890

    def test_canonical_wins_over_raw(self):
        """S10: when both canonical and raw carry values, canonical takes precedence."""
        payload = {
            "players_added_ids": ["CANON_ADD"],
            "players_dropped_ids": ["CANON_DROP"],
            "bid_amount": 99.5,
            "mfl_timestamp": 1234567890,
        }
        # Divergent raw: must not leak through.
        raw = {
            "transaction": "RAW_ADD,|77.0|RAW_DROP,",
            "timestamp": "9999999999",
        }
        result = _extract_bbid_waiver_fields(payload, raw)
        assert result["add_player_ids"] == ["CANON_ADD"]
        assert result["drop_player_ids"] == ["CANON_DROP"]
        assert result["bid_amount"] == 99.5
        assert result["mfl_timestamp"] == 1234567890


# ── _extract_waiver_bid_awarded_fields ───────────────────────────────

class TestExtractWaiverBidAwardedFields:
    def test_full_fields(self):
        payload = {
            "bid_amount": 25,
            "player_id": "P100",
            "players_added_ids": ["P100"],
            "players_dropped_ids": ["P200"],
        }
        raw = {"timestamp": "1700000000"}
        result = _extract_waiver_bid_awarded_fields(payload, raw)
        assert result["bid_amount"] == 25
        assert result["player_id"] == "P100"
        assert result["add_player_ids"] == ["P100"]
        assert result["drop_player_ids"] == ["P200"]
        assert result["mfl_timestamp"] == 1700000000

    def test_minimal_fields(self):
        result = _extract_waiver_bid_awarded_fields({}, {})
        assert "bid_amount" not in result

    def test_mfl_timestamp_canonical_wins_over_raw(self):
        """S10: canonical mfl_timestamp is preferred over raw["timestamp"].

        (Currently only applicable to synthetic fixtures; waiver_bids.py
        ingest does not yet promote mfl_timestamp. See module docstring.)
        """
        payload = {"mfl_timestamp": 1234567890}
        raw = {"timestamp": "9999999999"}
        result = _extract_waiver_bid_awarded_fields(payload, raw)
        assert result["mfl_timestamp"] == 1234567890


# ── _extract_free_agent_fields ───────────────────────────────────────

class TestExtractFreeAgentFields:
    def test_with_adds_and_drops(self):
        payload = {
            "players_added_ids": ["P1"],
            "players_dropped_ids": ["P2"],
        }
        result = _extract_free_agent_fields(payload, {})
        assert result["add_player_ids"] == ["P1"]
        assert result["drop_player_ids"] == ["P2"]

    def test_empty_payload(self):
        result = _extract_free_agent_fields({}, {})
        assert "add_player_ids" not in result

    def test_mfl_timestamp_canonical_wins_over_raw(self):
        """S10: canonical mfl_timestamp is preferred over raw["timestamp"]."""
        payload = {
            "players_added_ids": ["P1"],
            "mfl_timestamp": 1234567890,
        }
        raw = {"timestamp": "9999999999"}
        result = _extract_free_agent_fields(payload, raw)
        assert result["mfl_timestamp"] == 1234567890


# ── _extract_trade_fields ────────────────────────────────────────────

class TestExtractTradeFields:
    def test_full_trade(self):
        """Pre-promotion fallback: empty canonical, raw carries all fields."""
        raw = {
            "franchise": "F1",
            "franchise2": "F2",
            "franchise1_gave_up": "P1,P2",
            "franchise2_gave_up": "P3",
            "timestamp": "1700000000",
        }
        result = _extract_trade_fields({}, raw)
        assert result["franchise1_id"] == "F1"
        assert result["franchise2_id"] == "F2"
        assert result["franchise1_gave_up_player_ids"] == ["P1", "P2"]
        assert result["franchise2_gave_up_player_ids"] == ["P3"]
        assert result["mfl_timestamp"] == 1700000000

    def test_empty_raw(self):
        result = _extract_trade_fields({}, {})
        assert result["franchise1_gave_up_player_ids"] == []
        assert result["franchise2_gave_up_player_ids"] == []

    def test_with_comments_and_expires(self):
        raw = {
            "franchise": "F1",
            "franchise2": "F2",
            "comments": "Test trade",
            "expires": "1700100000",
        }
        result = _extract_trade_fields({}, raw)
        assert result["comments"] == "Test trade"
        assert result["expires_timestamp"] == 1700100000

    def test_canonical_path_all_fields(self):
        """S10: fully-promoted trade envelope resolves entirely from canonical payload.

        Empty raw proves the canonical path isn't secretly relying on raw
        fallback for any field.
        """
        payload = {
            "franchise_ids_involved": ["F1", "F2"],
            "trade_franchise_a_gave_up": ["P1", "P2"],
            "trade_franchise_b_gave_up": ["P3"],
            "trade_comments": "Rental deadline deal",
            "trade_expires_timestamp": 1700100000,
            "mfl_timestamp": 1700000000,
        }
        result = _extract_trade_fields(payload, {})
        assert result["franchise1_id"] == "F1"
        assert result["franchise2_id"] == "F2"
        assert result["franchise1_gave_up_player_ids"] == ["P1", "P2"]
        assert result["franchise2_gave_up_player_ids"] == ["P3"]
        assert result["comments"] == "Rental deadline deal"
        assert result["expires_timestamp"] == 1700100000
        assert result["mfl_timestamp"] == 1700000000

    def test_canonical_franchise_ids_from_involved(self):
        """S10: franchise1/2 IDs are derived from ``franchise_ids_involved`` positions.

        6eab1e0's query-side parser guarantees initiator is position [0]
        and counterparty is position [1]. This test pins that contract
        at the fact-extraction layer.
        """
        payload = {"franchise_ids_involved": ["INIT", "COUNTER"]}
        raw = {"franchise": "RAW_INIT_WRONG", "franchise2": "RAW_COUNTER_WRONG"}
        result = _extract_trade_fields(payload, raw)
        # Canonical positions win, not raw franchise/franchise2 keys.
        assert result["franchise1_id"] == "INIT"
        assert result["franchise2_id"] == "COUNTER"

    def test_canonical_wins_over_raw(self):
        """S10: when canonical and raw disagree, canonical is authoritative.

        Mirrors the discipline in b26e93f's trade-loader: the ingest-
        promoted fields are the source of truth; raw is consulted only
        for pre-promotion events.
        """
        payload = {
            "franchise_ids_involved": ["CANON_A", "CANON_B"],
            "trade_franchise_a_gave_up": ["CANON_P1"],
            "trade_franchise_b_gave_up": ["CANON_P2"],
            "trade_comments": "Canonical",
            "trade_expires_timestamp": 1700100000,
            "mfl_timestamp": 1700000000,
        }
        # Every raw field diverges from canonical.
        raw = {
            "franchise": "RAW_A",
            "franchise2": "RAW_B",
            "franchise1_gave_up": "RAW_P1,",
            "franchise2_gave_up": "RAW_P2,",
            "comments": "Raw",
            "expires": "9999999999",
            "timestamp": "9999999999",
        }
        result = _extract_trade_fields(payload, raw)
        assert result["franchise1_id"] == "CANON_A"
        assert result["franchise2_id"] == "CANON_B"
        assert result["franchise1_gave_up_player_ids"] == ["CANON_P1"]
        assert result["franchise2_gave_up_player_ids"] == ["CANON_P2"]
        assert result["comments"] == "Canonical"
        assert result["expires_timestamp"] == 1700100000
        assert result["mfl_timestamp"] == 1700000000

    def test_fallback_retained_for_pre_promotion(self):
        """S10: empty canonical payload + populated raw = fully raw-sourced result.

        This is the key test for historical events: the ledger is
        append-only, so pre-promotion trades must continue to resolve
        from raw_mfl_json indefinitely.
        """
        payload: dict[str, object] = {}
        raw = {
            "franchise": "HIST_A",
            "franchise2": "HIST_B",
            "franchise1_gave_up": "H1,H2,",
            "franchise2_gave_up": "H3,",
            "comments": "Historical deal",
            "expires": "1600100000",
            "timestamp": "1600000000",
        }
        result = _extract_trade_fields(payload, raw)
        assert result["franchise1_id"] == "HIST_A"
        assert result["franchise2_id"] == "HIST_B"
        assert result["franchise1_gave_up_player_ids"] == ["H1", "H2"]
        assert result["franchise2_gave_up_player_ids"] == ["H3"]
        assert result["comments"] == "Historical deal"
        assert result["expires_timestamp"] == 1600100000
        assert result["mfl_timestamp"] == 1600000000


# ── _extract_details routing ─────────────────────────────────────────

class TestExtractDetails:
    def test_always_includes_payload(self):
        payload = {"franchise_id": "F1", "mfl_type": "BBID_WAIVER"}
        result = _extract_details("TRANSACTION_BBID_WAIVER", payload)
        assert result["payload"] == payload
        assert result["franchise_id"] == "F1"

    def test_common_fields_extracted(self):
        payload = {"source_url": "http://example.com", "player_id": "P1"}
        result = _extract_details("SOME_TYPE", payload)
        assert result["source_url"] == "http://example.com"
        assert result["player_id"] == "P1"

    def test_trade_routing(self):
        raw_json = json.dumps({
            "type": "TRADE", "franchise": "F1", "franchise2": "F2",
            "franchise1_gave_up": "P1", "franchise2_gave_up": "P2",
        })
        payload = {"raw_mfl_json": raw_json}
        result = _extract_details("TRANSACTION_TRADE", payload)
        assert "normalized" in result
        assert result["normalized"]["franchise1_id"] == "F1"

    def test_waiver_bid_routing(self):
        raw_json = json.dumps({"type": "BBID_WAIVER", "franchise": "F1"})
        payload = {"raw_mfl_json": raw_json, "bid_amount": 10}
        result = _extract_details("WAIVER_BID_AWARDED", payload)
        assert "normalized" in result
        assert result["normalized"]["bid_amount"] == 10


# ── EventFact dataclass ──────────────────────────────────────────────

class TestEventFact:
    def test_frozen(self):
        fact = EventFact(canonical_id=1, event_type="DRAFT_PICK", occurred_at="2024-10-01", details={})
        with pytest.raises(AttributeError):
            fact.canonical_id = 2

    def test_fields(self):
        fact = EventFact(canonical_id=42, event_type="TRADE", occurred_at=None, details={"k": "v"})
        assert fact.canonical_id == 42
        assert fact.event_type == "TRADE"
        assert fact.occurred_at is None
        assert fact.details == {"k": "v"}
