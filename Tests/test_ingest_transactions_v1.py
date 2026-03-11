"""Tests for squadvault.ingest.transactions.

Covers: _safe_get, _stable_external_id, _truncate_raw_json, _extract_type,
_extract_franchise_id, _extract_timestamp_unix, _extract_bid_amount,
_parse_mfl_transaction_field, derive_transaction_event_envelopes.
"""
from __future__ import annotations

import pytest

from squadvault.ingest.transactions import (
    _safe_get,
    _stable_external_id,
    _truncate_raw_json,
    _extract_type,
    _extract_franchise_id,
    _extract_timestamp_unix,
    _extract_bid_amount,
    _parse_mfl_transaction_field,
    derive_transaction_event_envelopes,
)


# ── _safe_get ────────────────────────────────────────────────────────

class TestSafeGet:
    def test_first_key(self):
        assert _safe_get({"a": 1, "b": 2}, "a") == 1

    def test_fallback_key(self):
        assert _safe_get({"b": 2}, "a", "b") == 2

    def test_missing_returns_none(self):
        assert _safe_get({}, "a", "b") is None


# ── _stable_external_id ─────────────────────────────────────────────

class TestStableExternalId:
    def test_deterministic(self):
        assert _stable_external_id("a", "b") == _stable_external_id("a", "b")

    def test_different_inputs_differ(self):
        assert _stable_external_id("a", "b") != _stable_external_id("a", "c")

    def test_length(self):
        assert len(_stable_external_id("x")) == 24

    def test_none_parts_handled(self):
        result = _stable_external_id("a", None, "b")
        assert len(result) == 24


# ── _truncate_raw_json ───────────────────────────────────────────────

class TestTruncateRawJson:
    def test_short_untouched(self):
        assert _truncate_raw_json("short", 100) == "short"

    def test_long_truncated(self):
        result = _truncate_raw_json("x" * 200, 50)
        assert len(result) < 200
        assert result.endswith("...(truncated)")

    def test_exact_limit(self):
        s = "x" * 50
        assert _truncate_raw_json(s, 50) == s


# ── _extract_type ────────────────────────────────────────────────────

class TestExtractType:
    def test_at_type(self):
        assert _extract_type({"@type": "FREE_AGENT"}) == "FREE_AGENT"

    def test_type_key(self):
        assert _extract_type({"type": "trade"}) == "TRADE"

    def test_missing(self):
        assert _extract_type({}) == ""


# ── _extract_franchise_id ────────────────────────────────────────────

class TestExtractFranchiseId:
    def test_at_franchise(self):
        assert _extract_franchise_id({"@franchise": "0001"}) == "0001"

    def test_franchise_key(self):
        assert _extract_franchise_id({"franchise": "0004"}) == "0004"

    def test_missing(self):
        assert _extract_franchise_id({}) == ""


# ── _extract_timestamp_unix ──────────────────────────────────────────

class TestExtractTimestampUnix:
    def test_valid(self):
        assert _extract_timestamp_unix({"@timestamp": "1700000000"}) == 1700000000

    def test_int_value(self):
        assert _extract_timestamp_unix({"timestamp": 1700000000}) == 1700000000

    def test_missing(self):
        assert _extract_timestamp_unix({}) is None

    def test_garbage(self):
        assert _extract_timestamp_unix({"timestamp": "not_a_number"}) is None


# ── _extract_bid_amount ──────────────────────────────────────────────

class TestExtractBidAmount:
    def test_bid_key(self):
        assert _extract_bid_amount({"bid": "25.50"}) == 25.5

    def test_amount_key(self):
        assert _extract_bid_amount({"amount": 10}) == 10.0

    def test_bbid_key(self):
        assert _extract_bid_amount({"bbid": "0.50"}) == 0.5

    def test_missing(self):
        assert _extract_bid_amount({}) is None

    def test_garbage(self):
        assert _extract_bid_amount({"bid": "not_a_number"}) is None


# ── _parse_mfl_transaction_field ─────────────────────────────────────

class TestParseMflTransactionField:
    def test_free_agent_format(self):
        adds, drops = _parse_mfl_transaction_field({"transaction": "16207,|14108,"})
        assert adds == ["16207"]
        assert drops == ["14108"]

    def test_bbid_waiver_format(self):
        adds, drops = _parse_mfl_transaction_field({"transaction": "14108,|16.00|12676,"})
        assert adds == ["14108"]
        assert drops == ["12676"]

    def test_adds_only(self):
        adds, drops = _parse_mfl_transaction_field({"transaction": "100,"})
        assert adds == ["100"]
        assert drops == []

    def test_missing(self):
        adds, drops = _parse_mfl_transaction_field({})
        assert adds == []
        assert drops == []

    def test_empty_string(self):
        adds, drops = _parse_mfl_transaction_field({"transaction": ""})
        assert adds == []
        assert drops == []

    def test_at_transaction(self):
        adds, drops = _parse_mfl_transaction_field({"@transaction": "200,|300,"})
        assert adds == ["200"]
        assert drops == ["300"]


# ── derive_transaction_event_envelopes ───────────────────────────────

class TestDeriveTransactionEventEnvelopes:
    def test_basic_free_agent(self):
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
                 "transaction": "16207,|14108,"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        evt = result[0]
        assert evt["event_type"] == "TRANSACTION_FREE_AGENT"
        assert evt["league_id"] == "L1"
        assert evt["season"] == 2024
        assert evt["payload"]["franchise_id"] == "0001"
        assert evt["payload"]["players_added_ids"] == ["16207"]
        assert evt["payload"]["players_dropped_ids"] == ["14108"]
        assert evt["external_source"] == "MFL"
        assert len(evt["external_id"]) == 24

    def test_excludes_auction_won(self):
        txns = [{"type": "AUCTION_WON", "franchise": "0001", "timestamp": "1700000000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result == []

    def test_excludes_bbid_waiver(self):
        txns = [{"type": "BBID_WAIVER", "franchise": "0001", "timestamp": "1700000000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result == []

    def test_empty_input(self):
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=[], source_url="http://test",
        )
        assert result == []

    def test_deterministic_external_id(self):
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
                 "transaction": "16207,|14108,"}]
        r1 = derive_transaction_event_envelopes(year=2024, league_id="L1", transactions=txns, source_url="x")
        r2 = derive_transaction_event_envelopes(year=2024, league_id="L1", transactions=txns, source_url="x")
        assert r1[0]["external_id"] == r2[0]["external_id"]

    def test_trade_event(self):
        txns = [{"type": "TRADE", "franchise": "0001", "timestamp": "1700000000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        assert result[0]["event_type"] == "TRANSACTION_TRADE"

    def test_occurred_at_from_timestamp(self):
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1704067200"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["occurred_at"] is not None
        assert result[0]["occurred_at"].startswith("2024-01-01")

    def test_missing_timestamp_still_works(self):
        txns = [{"type": "FREE_AGENT", "franchise": "0001"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        assert result[0]["occurred_at"] is None
