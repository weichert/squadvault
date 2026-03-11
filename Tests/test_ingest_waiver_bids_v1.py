"""Tests for squadvault.ingest.waiver_bids.

Covers: _parse_mfl_transaction_field, derive_waiver_bid_event_envelopes_from_transactions,
stub filtering, direct field fallbacks.
"""
from __future__ import annotations

import pytest

from squadvault.ingest.waiver_bids import (
    _truncate_raw_json,
    _safe_get,
    _extract_type,
    _extract_franchise_id,
    _extract_timestamp_unix,
    _parse_mfl_transaction_field,
    derive_waiver_bid_event_envelopes_from_transactions,
)


# ── _parse_mfl_transaction_field ─────────────────────────────────────

class TestParseMflTransactionField:
    def test_bbid_waiver_full(self):
        """Standard BBID_WAIVER: adds|bid|drops."""
        adds, bid, drops = _parse_mfl_transaction_field({"transaction": "14108,|16.00|12676,"})
        assert adds == ["14108"]
        assert bid == 16.0
        assert drops == ["12676"]

    def test_adds_only(self):
        adds, bid, drops = _parse_mfl_transaction_field({"transaction": "14108,"})
        assert adds == ["14108"]
        assert bid is None
        assert drops == []

    def test_adds_and_bid_no_drops(self):
        adds, bid, drops = _parse_mfl_transaction_field({"transaction": "14108,|5.00|"})
        assert adds == ["14108"]
        assert bid == 5.0
        assert drops == []

    def test_multiple_adds_and_drops(self):
        adds, bid, drops = _parse_mfl_transaction_field({"transaction": "100,200,|10.00|300,400,"})
        assert adds == ["100", "200"]
        assert bid == 10.0
        assert drops == ["300", "400"]

    def test_missing_transaction(self):
        adds, bid, drops = _parse_mfl_transaction_field({})
        assert adds == []
        assert bid is None
        assert drops == []

    def test_empty_transaction(self):
        adds, bid, drops = _parse_mfl_transaction_field({"transaction": ""})
        assert adds == []
        assert bid is None
        assert drops == []

    def test_at_transaction_key(self):
        adds, bid, drops = _parse_mfl_transaction_field({"@transaction": "100,|5.00|200,"})
        assert adds == ["100"]
        assert bid == 5.0
        assert drops == ["200"]

    def test_invalid_bid_returns_none(self):
        adds, bid, drops = _parse_mfl_transaction_field({"transaction": "100,|not_a_number|200,"})
        assert adds == ["100"]
        assert bid is None
        assert drops == ["200"]


# ── derive_waiver_bid_event_envelopes ────────────────────────────────

class TestDeriveWaiverBidEnvelopes:
    def test_basic_bbid_waiver(self):
        txns = [{
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "timestamp": "1700000000",
            "transaction": "14108,|16.00|12676,",
        }]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        evt = result[0]
        assert evt["event_type"] == "WAIVER_BID_AWARDED"
        assert evt["payload"]["bid_amount"] == 16.0
        assert evt["payload"]["players_added_ids"] == "14108"
        assert evt["payload"]["players_dropped_ids"] == "12676"
        assert evt["payload"]["player_id"] == "14108"

    def test_bbid_waiver_request(self):
        txns = [{
            "type": "BBID_WAIVER_REQUEST",
            "franchise": "0001",
            "timestamp": "1700000000",
            "transaction": "14108,|5.00|",
        }]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        assert result[0]["event_type"] == "WAIVER_BID_REQUEST"

    def test_skips_non_waiver_types(self):
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000"}]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result == []

    def test_skips_stub_events(self):
        """Events with no parseable details are filtered out."""
        txns = [{"type": "BBID_WAIVER", "franchise": "0001", "timestamp": "1700000000"}]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result == []

    def test_direct_player_id_fallback(self):
        """If transaction field is empty, fall back to player_id field."""
        txns = [{
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "timestamp": "1700000000",
            "player_id": "P100",
            "bid": "10",
        }]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        assert result[0]["payload"]["player_id"] == "P100"
        assert result[0]["payload"]["bid_amount"] == 10.0

    def test_deterministic_external_id(self):
        txns = [{
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "timestamp": "1700000000",
            "transaction": "14108,|16.00|12676,",
        }]
        r1 = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="x",
        )
        r2 = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="x",
        )
        assert r1[0]["external_id"] == r2[0]["external_id"]

    def test_empty_input(self):
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=[], source_url="http://test",
        )
        assert result == []
