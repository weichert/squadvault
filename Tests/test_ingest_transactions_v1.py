"""Tests for squadvault.ingest.transactions.

Covers: _safe_get, _stable_external_id, _truncate_raw_json, _extract_type,
_extract_franchise_id, _extract_all_franchise_ids, _extract_timestamp_unix,
_extract_bid_amount, _parse_mfl_transaction_field, _parse_trade_gave_up,
_extract_trade_comments, _extract_trade_expires_timestamp,
derive_transaction_event_envelopes.
"""
from __future__ import annotations

from squadvault.ingest.transactions import (
    _extract_all_franchise_ids,
    _extract_bid_amount,
    _extract_franchise_id,
    _extract_timestamp_unix,
    _extract_trade_comments,
    _extract_trade_expires_timestamp,
    _extract_type,
    _parse_mfl_transaction_field,
    _parse_trade_gave_up,
    _safe_get,
    _stable_external_id,
    _truncate_raw_json,
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


# ── _extract_all_franchise_ids (S10 promotion helper) ────────────────

class TestExtractAllFranchiseIds:
    def test_single_franchise_non_trade(self):
        """Non-trade transactions: only the initiator is surfaced."""
        assert _extract_all_franchise_ids({"@franchise": "0001"}) == ["0001"]

    def test_franchise_key_only(self):
        """'franchise' key (no '@') is equally valid as initiator."""
        assert _extract_all_franchise_ids({"franchise": "0004"}) == ["0004"]

    def test_trade_with_counterparty(self):
        """Trade: initiator first, counterparty second, in MFL key order."""
        txn = {"@franchise": "0001", "franchise2": "0010", "type": "TRADE"}
        assert _extract_all_franchise_ids(txn) == ["0001", "0010"]

    def test_trade_with_multiple_counterparties(self):
        """Three-way trades are represented as the full franchise list."""
        txn = {"franchise": "0001", "franchise2": "0010", "franchise3": "0007"}
        assert _extract_all_franchise_ids(txn) == ["0001", "0010", "0007"]

    def test_dedupes_initiator_appearing_twice(self):
        """If both '@franchise' and 'franchise' carry the same value, only once in output."""
        txn = {"@franchise": "0001", "franchise": "0001", "franchise2": "0010"}
        assert _extract_all_franchise_ids(txn) == ["0001", "0010"]

    def test_at_prefixed_counterparties(self):
        """@franchise2 (some feed shapes) is recognized."""
        txn = {"@franchise": "0001", "@franchise2": "0010"}
        assert _extract_all_franchise_ids(txn) == ["0001", "0010"]

    def test_empty_values_skipped(self):
        """Empty strings do not enter the result."""
        txn = {"franchise": "0001", "franchise2": "", "franchise3": "0007"}
        assert _extract_all_franchise_ids(txn) == ["0001", "0007"]

    def test_non_string_values_skipped(self):
        """Defensive: non-string values are not coerced."""
        txn = {"franchise": "0001", "franchise2": 12, "franchise3": None}
        assert _extract_all_franchise_ids(txn) == ["0001"]

    def test_empty_input(self):
        assert _extract_all_franchise_ids({}) == []


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


# ── _parse_trade_gave_up ─────────────────────────────────────────────

class TestParseTradeGaveUp:
    """Unit tests for the trade-specific gave-up parser.

    S10 pattern: the parser promotes ``franchise1_gave_up`` /
    ``franchise2_gave_up`` sibling keys from the raw MFL trade dict
    into canonical list-of-str form so consumer-layer code can read
    trade structure without reaching into ``raw_mfl_json``.
    """

    def test_both_populated(self):
        a, b = _parse_trade_gave_up({
            "franchise1_gave_up": "15648,15712,",
            "franchise2_gave_up": "14213,",
        })
        assert a == ["15648", "15712"]
        assert b == ["14213"]

    def test_missing_keys(self):
        """Non-trade dicts (or trades missing the keys) yield empty lists."""
        a, b = _parse_trade_gave_up({})
        assert a == []
        assert b == []

    def test_empty_strings(self):
        a, b = _parse_trade_gave_up({
            "franchise1_gave_up": "",
            "franchise2_gave_up": "",
        })
        assert a == []
        assert b == []

    def test_at_prefixed(self):
        """MFL sometimes emits @-prefixed variants; the parser accepts either."""
        a, b = _parse_trade_gave_up({
            "@franchise1_gave_up": "100,",
            "@franchise2_gave_up": "200,",
        })
        assert a == ["100"]
        assert b == ["200"]

    def test_non_string_values_skipped(self):
        a, b = _parse_trade_gave_up({
            "franchise1_gave_up": None,
            "franchise2_gave_up": 42,
        })
        assert a == []
        assert b == []

    def test_trailing_empty_tail_ignored(self):
        """MFL's canonical comma-with-trailing-empty format is handled."""
        a, b = _parse_trade_gave_up({
            "franchise1_gave_up": "A,B,C,",
            "franchise2_gave_up": "X,",
        })
        assert a == ["A", "B", "C"]
        assert b == ["X"]

    def test_one_side_empty(self):
        """Only one side populated is returned as-is — the caller decides validity."""
        a, b = _parse_trade_gave_up({
            "franchise1_gave_up": "P1,",
            "franchise2_gave_up": "",
        })
        assert a == ["P1"]
        assert b == []


# ── _extract_trade_comments (S10 promotion helper) ───────────────────

class TestExtractTradeComments:
    """Unit tests for the trade-comments promotion helper.

    S10 pattern: the helper surfaces ``comments`` from the raw MFL
    trade dict so consumer-layer code can read it from the canonical
    payload (``trade_comments``) without reaching into ``raw_mfl_json``.
    """

    def test_present(self):
        assert _extract_trade_comments({"comments": "Rental deadline deal"}) == \
            "Rental deadline deal"

    def test_at_prefixed(self):
        """MFL sometimes emits @comments; the helper accepts either shape."""
        assert _extract_trade_comments({"@comments": "via DM"}) == "via DM"

    def test_absent(self):
        """Trades without a comments key yield None (consumer treats as no-comment)."""
        assert _extract_trade_comments({}) is None


# ── _extract_trade_expires_timestamp (S10 promotion helper) ──────────

class TestExtractTradeExpiresTimestamp:
    """Unit tests for the trade-expires promotion helper.

    S10 pattern: surfaces the expiration Unix timestamp from the raw
    MFL trade dict as an int so consumers don't re-parse raw_mfl_json.
    """

    def test_int_string(self):
        assert _extract_trade_expires_timestamp({"expires": "1700100000"}) == 1700100000

    def test_absent(self):
        assert _extract_trade_expires_timestamp({}) is None

    def test_garbage(self):
        """Unparseable values yield None rather than raising."""
        assert _extract_trade_expires_timestamp({"expires": "not_a_number"}) is None


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

    def test_free_agent_franchise_ids_involved_contains_initiator_only(self):
        """S10: non-trade canonical list contains just the initiator."""
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
                 "transaction": "16207,|14108,"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["franchise_ids_involved"] == ["0001"]

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

    def test_trade_event_promotes_counterparties_to_canonical_payload(self):
        """S10: franchise_ids_involved is written at ingest, no downstream raw parsing needed."""
        txns = [{
            "type": "TRADE",
            "franchise": "0001",
            "franchise2": "0010",
            "timestamp": "1700000000",
        }]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        payload = result[0]["payload"]
        assert payload["franchise_id"] == "0001"
        assert payload["franchise_ids_involved"] == ["0001", "0010"]

    def test_trade_event_promotes_gave_up_lists_to_canonical_payload(self):
        """S10: trade-specific player IDs are written at ingest from franchise*_gave_up sibling keys.

        This is the ingest half of the trade-loader S10-pattern fix. The
        consumer half lives in ``_load_season_trades``, which reads these
        canonical fields first and only falls back to raw_mfl_json for
        pre-promotion events.
        """
        txns = [{
            "type": "TRADE",
            "franchise": "0001",
            "franchise2": "0010",
            "franchise1_gave_up": "15648,15712,",
            "franchise2_gave_up": "14213,",
            "timestamp": "1700000000",
        }]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        payload = result[0]["payload"]
        assert payload["trade_franchise_a_gave_up"] == ["15648", "15712"]
        assert payload["trade_franchise_b_gave_up"] == ["14213"]

    def test_trade_event_without_gave_up_keys_gets_empty_lists(self):
        """When MFL omits the gave-up keys, ingest still emits explicit empty lists.

        Shape stability matters: the consumer uses key-presence as a
        signal that the event is post-promotion (see
        ``_resolve_trade_structure`` in player_narrative_angles_v1). A
        trade event with neither gave-up side parseable is still a
        post-promotion event — it just happens to be non-viable as a
        trade, which the consumer's "must have players on both sides"
        guard will reject.
        """
        txns = [{
            "type": "TRADE",
            "franchise": "0001",
            "franchise2": "0010",
            "timestamp": "1700000000",
        }]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        payload = result[0]["payload"]
        assert payload["trade_franchise_a_gave_up"] == []
        assert payload["trade_franchise_b_gave_up"] == []

    def test_non_trade_events_get_empty_trade_fields(self):
        """Shape stability: the two trade-specific fields are always present, empty for non-trades."""
        txns = [{
            "type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
            "transaction": "16207,|14108,",
        }]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        payload = result[0]["payload"]
        assert payload["trade_franchise_a_gave_up"] == []
        assert payload["trade_franchise_b_gave_up"] == []

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

    # ── S10 promotion tests (this pass) ──────────────────────────────

    def test_mfl_timestamp_promoted_on_free_agent(self):
        """S10: Unix timestamp surfaces as canonical ``mfl_timestamp`` at ingest."""
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
                 "transaction": "16207,|14108,"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["mfl_timestamp"] == 1700000000

    def test_mfl_timestamp_promoted_on_trade(self):
        """S10: mfl_timestamp is promoted on every envelope type, including TRADE."""
        txns = [{"type": "TRADE", "franchise": "0001", "franchise2": "0010",
                 "timestamp": "1700000000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["mfl_timestamp"] == 1700000000

    def test_mfl_timestamp_none_when_timestamp_absent(self):
        """Missing timestamp is surfaced as None (shape stability)."""
        txns = [{"type": "FREE_AGENT", "franchise": "0001"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["mfl_timestamp"] is None

    def test_trade_comments_promoted_when_present(self):
        """S10: trade comments are promoted to canonical ``trade_comments`` at ingest."""
        txns = [{"type": "TRADE", "franchise": "0001", "franchise2": "0010",
                 "timestamp": "1700000000", "comments": "Big rental deadline deal"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["trade_comments"] == "Big rental deadline deal"

    def test_trade_comments_none_when_absent_on_trade(self):
        """TRADE events without a ``comments`` key get None (shape stability)."""
        txns = [{"type": "TRADE", "franchise": "0001", "franchise2": "0010",
                 "timestamp": "1700000000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["trade_comments"] is None

    def test_trade_comments_none_on_non_trade_envelope(self):
        """Non-TRADE envelopes always carry ``trade_comments`` = None (shape stability)."""
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
                 "transaction": "16207,|14108,"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["trade_comments"] is None

    def test_trade_expires_timestamp_promoted_when_present(self):
        """S10: trade expiration timestamp is promoted to canonical payload at ingest."""
        txns = [{"type": "TRADE", "franchise": "0001", "franchise2": "0010",
                 "timestamp": "1700000000", "expires": "1700100000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["trade_expires_timestamp"] == 1700100000

    def test_trade_expires_timestamp_none_when_absent_on_trade(self):
        """TRADE events without an ``expires`` key get None (shape stability)."""
        txns = [{"type": "TRADE", "franchise": "0001", "franchise2": "0010",
                 "timestamp": "1700000000"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["trade_expires_timestamp"] is None

    def test_trade_expires_timestamp_none_on_non_trade_envelope(self):
        """Non-TRADE envelopes always carry ``trade_expires_timestamp`` = None."""
        txns = [{"type": "FREE_AGENT", "franchise": "0001", "timestamp": "1700000000",
                 "transaction": "16207,|14108,"}]
        result = derive_transaction_event_envelopes(
            year=2024, league_id="L1", transactions=txns, source_url="http://test",
        )
        assert result[0]["payload"]["trade_expires_timestamp"] is None
