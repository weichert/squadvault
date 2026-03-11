"""Tests for squadvault.ingest.auction_draft.

Covers: _parse_transaction_field, _extract_player_id, _extract_bid_amount,
derive_auction_event_envelopes_from_transactions, skip-on-no-player.
"""
from __future__ import annotations

import pytest

from squadvault.ingest.auction_draft import (
    _safe_get,
    _extract_type,
    _extract_timestamp_unix,
    _extract_franchise_id,
    _parse_transaction_field,
    _extract_player_id,
    _extract_bid_amount,
    _truncate_raw_json,
    _stable_external_id,
    derive_auction_event_envelopes_from_transactions,
)


# ── _parse_transaction_field ─────────────────────────────────────────

class TestParseTransactionField:
    def test_standard_auction_won(self):
        """Standard format: player_id|bid|"""
        player_id, bid = _parse_transaction_field({"transaction": "14223|1|"})
        assert player_id == "14223"
        assert bid == 1.0

    def test_no_bid(self):
        player_id, bid = _parse_transaction_field({"transaction": "14223||"})
        assert player_id == "14223"
        assert bid is None

    def test_missing_field(self):
        player_id, bid = _parse_transaction_field({})
        assert player_id == ""
        assert bid is None

    def test_at_transaction(self):
        player_id, bid = _parse_transaction_field({"@transaction": "100|5|"})
        assert player_id == "100"
        assert bid == 5.0


# ── _extract_player_id ───────────────────────────────────────────────

class TestExtractPlayerId:
    def test_direct_player_key(self):
        assert _extract_player_id({"player": "P100"}) == "P100"

    def test_player_id_key(self):
        assert _extract_player_id({"player_id": "P200"}) == "P200"

    def test_at_player(self):
        assert _extract_player_id({"@player": "P300"}) == "P300"

    def test_fallback_to_transaction(self):
        assert _extract_player_id({"transaction": "14223|1|"}) == "14223"

    def test_player_dict(self):
        assert _extract_player_id({"player": {"id": "P400"}}) == "P400"

    def test_missing(self):
        assert _extract_player_id({}) == ""


# ── _extract_bid_amount ──────────────────────────────────────────────

class TestExtractBidAmount:
    def test_bid_key(self):
        assert _extract_bid_amount({"bid": "25"}) == 25.0

    def test_price_key(self):
        assert _extract_bid_amount({"price": 10}) == 10.0

    def test_fallback_to_transaction(self):
        assert _extract_bid_amount({"transaction": "14223|42|"}) == 42.0

    def test_missing(self):
        assert _extract_bid_amount({}) is None


# ── derive_auction_event_envelopes ───────────────────────────────────

class TestDeriveAuctionEnvelopes:
    def test_basic_auction_won(self):
        txns = [{
            "type": "AUCTION_WON",
            "franchise": "0001",
            "timestamp": "1700000000",
            "transaction": "14223|50|",
        }]
        result = derive_auction_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        evt = result[0]
        assert evt["event_type"] == "DRAFT_PICK"
        assert evt["payload"]["mfl_type"] == "AUCTION_WON"
        assert evt["payload"]["player_id"] == "14223"
        assert evt["payload"]["bid_amount"] == 50.0
        assert evt["payload"]["franchise_id"] == "0001"
        assert evt["external_source"] == "MFL"
        assert len(evt["external_id"]) == 24

    def test_skips_non_auction_types(self):
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "transaction": "100|5|"}]
        result = derive_auction_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result == []

    def test_skips_when_no_player(self):
        """If player can't be identified, event is silently dropped."""
        txns = [{"type": "AUCTION_WON", "franchise": "0001", "timestamp": "1700000000"}]
        result = derive_auction_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result == []

    def test_deterministic_external_id(self):
        txns = [{
            "type": "AUCTION_WON",
            "franchise": "0001",
            "timestamp": "1700000000",
            "transaction": "14223|50|",
        }]
        r1 = derive_auction_event_envelopes_from_transactions(year=2024, league_id="L1", transactions=txns, source_url="x")
        r2 = derive_auction_event_envelopes_from_transactions(year=2024, league_id="L1", transactions=txns, source_url="x")
        assert r1[0]["external_id"] == r2[0]["external_id"]

    def test_empty_input(self):
        result = derive_auction_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=[], source_url="http://test",
        )
        assert result == []

    def test_draft_type_accepted(self):
        txns = [{
            "type": "DRAFT_PICK",
            "franchise": "0001",
            "timestamp": "1700000000",
            "player_id": "P100",
        }]
        result = derive_auction_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        assert result[0]["event_type"] == "DRAFT_PICK"

    def test_occurred_at_from_timestamp(self):
        txns = [{
            "type": "AUCTION_WON",
            "franchise": "0001",
            "timestamp": "1704067200",
            "transaction": "100|1|",
        }]
        result = derive_auction_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["occurred_at"] is not None
        assert result[0]["occurred_at"].startswith("2024-01-01")
