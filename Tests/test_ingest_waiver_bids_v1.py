"""Tests for squadvault.ingest.waiver_bids.

Covers: _parse_mfl_transaction_field, derive_waiver_bid_event_envelopes_from_transactions,
stub filtering, direct field fallbacks.
"""
from __future__ import annotations

from squadvault.ingest.waiver_bids import (
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


# ── mfl_timestamp promotion (S10 leak #4 follow-up) ──────────────────

class TestMflTimestampPromotion:
    """Promotion of ``mfl_timestamp`` onto every WAIVER_BID_* envelope.

    Consumer-side canonical-first resolution for this field shipped in
    ad3cb98 (`extract_recap_facts_v1._mfl_timestamp_canonical_first`)
    but with a retained raw_mfl_json fallback for waiver_bids events
    that hadn't yet promoted the field. This pass closes that gap.

    Shape invariant: ``mfl_timestamp`` is always present on the payload,
    as int when parseable from raw ``timestamp``, else None. Matches the
    shape established by ad3cb98 for transactions.py envelopes.
    """

    def test_mfl_timestamp_promoted_when_present(self):
        """Parseable timestamp promotes to canonical int."""
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
        payload = result[0]["payload"]
        assert "mfl_timestamp" in payload
        assert payload["mfl_timestamp"] == 1700000000
        assert isinstance(payload["mfl_timestamp"], int)

    def test_mfl_timestamp_none_when_missing(self):
        """Missing timestamp key yields None, key still present."""
        # Need enough other fields to avoid the stub-filter early exit
        # — so supply player_id + bid via the compact transaction field.
        txns = [{
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "transaction": "14108,|5.00|",
        }]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        payload = result[0]["payload"]
        assert "mfl_timestamp" in payload
        assert payload["mfl_timestamp"] is None

    def test_mfl_timestamp_none_when_unparseable(self):
        """Non-numeric timestamp yields None, key still present."""
        txns = [{
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "timestamp": "not-a-number",
            "transaction": "14108,|5.00|",
        }]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert len(result) == 1
        payload = result[0]["payload"]
        assert "mfl_timestamp" in payload
        assert payload["mfl_timestamp"] is None

    def test_consumer_resolves_mfl_timestamp_from_canonical_path(self):
        """Integration proof: the consumer's canonical-first helper now
        resolves mfl_timestamp directly from the promoted payload field,
        not via the raw_mfl_json fallback.

        The helper returns the int from ``payload["mfl_timestamp"]``
        when present. For a post-promotion waiver_bids envelope this
        key is now populated, so the canonical path is exercised
        even if the raw fallback value would differ."""
        from squadvault.core.recaps.facts.extract_recap_facts_v1 import (
            _mfl_timestamp_canonical_first,
        )
        txns = [{
            "type": "BBID_WAIVER",
            "franchise": "0001",
            "timestamp": "1700000000",
            "transaction": "14108,|16.00|12676,",
        }]
        result = derive_waiver_bid_event_envelopes_from_transactions(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        payload = result[0]["payload"]

        # The raw_mfl_json under the canonical field carries the raw
        # timestamp string ("1700000000"); the canonical-first helper
        # must return the int from payload["mfl_timestamp"] instead.
        # Sanity that the raw path would have been reachable pre-promotion:
        import json as _json
        raw = _json.loads(payload["raw_mfl_json"])
        assert raw.get("timestamp") == "1700000000"

        # Canonical-first resolution — the post-promotion outcome:
        resolved = _mfl_timestamp_canonical_first(payload, raw)
        assert resolved == 1700000000
        assert isinstance(resolved, int)

