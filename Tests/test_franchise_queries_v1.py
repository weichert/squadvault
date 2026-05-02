"""Tests for squadvault.core.queries.franchise_queries.

Covers: _franchise_ids_from_payload, events_for_franchise,
draft_picks_for_franchise, trades_for_franchise.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.queries.franchise_queries import (
    _franchise_ids_from_payload,
    draft_picks_for_franchise,
    events_for_franchise,
    free_agent_moves_for_franchise,
    trades_for_franchise,
    waiver_awards_for_franchise,
)
from squadvault.core.storage.sqlite_store import SQLiteStore

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


# ── _franchise_ids_from_payload (pure) ───────────────────────────────

class TestFranchiseIdsFromPayload:
    """Covers the canonical-only read path. No raw_mfl_json parsing here —
    the helper deliberately ignores it; counterparty data must reach the
    helper via the canonical ``franchise_ids_involved`` field promoted
    at ingest time.
    """

    def test_simple_franchise_id(self):
        event = {"payload": {"franchise_id": "F001"}}
        assert _franchise_ids_from_payload(event) == {"F001"}

    def test_trade_with_franchise_ids_involved(self):
        """Canonical path: trade event carries all parties in the list field."""
        event = {"payload": {
            "franchise_id": "F001",
            "franchise_ids_involved": ["F001", "F002"],
        }}
        assert _franchise_ids_from_payload(event) == {"F001", "F002"}

    def test_franchise_ids_involved_plus_scalar_deduped(self):
        """Scalar initiator is merged into the set; duplicates collapse."""
        event = {"payload": {
            "franchise_id": "F001",
            "franchise_ids_involved": ["F001", "F002", "F003"],
        }}
        assert _franchise_ids_from_payload(event) == {"F001", "F002", "F003"}

    def test_empty_payload(self):
        assert _franchise_ids_from_payload({"payload": {}}) == set()

    def test_no_payload(self):
        assert _franchise_ids_from_payload({}) == set()

    def test_franchise_id_as_list(self):
        """Older payloads sometimes stored franchise_id as a list; still supported."""
        event = {"payload": {"franchise_id": ["F001", "F002"]}}
        assert _franchise_ids_from_payload(event) == {"F001", "F002"}

    # ── Backward-compat: events predating franchise_ids_involved ───────

    def test_old_event_shape_falls_back_to_scalar_franchise_id(self):
        """An event without the new list still resolves to its scalar initiator.

        This covers the memory-ledger append-only case: events written
        before franchise_ids_involved was promoted will only have
        franchise_id (plus raw_mfl_json, which the helper ignores).
        """
        event = {"payload": {
            "franchise_id": "F001",
            "raw_mfl_json": json.dumps({"franchise": "F001", "franchise2": "F002"}),
        }}
        # Only the scalar initiator surfaces. Counterparty F002 is present
        # in raw_mfl_json but the helper deliberately does not read it —
        # this is the documented under-representation of historical
        # trades noted in the helper's docstring.
        assert _franchise_ids_from_payload(event) == {"F001"}

    def test_old_event_shape_ignores_raw_even_when_no_scalar(self):
        """raw_mfl_json alone is not enough — returns empty set."""
        raw = json.dumps({"franchise": "F001", "franchise2": "F002"})
        event = {"payload": {"raw_mfl_json": raw}}
        assert _franchise_ids_from_payload(event) == set()

    def test_malformed_franchise_ids_involved_is_ignored_not_raised(self):
        """Non-list values in the field are skipped; scalar fallback still works."""
        event = {"payload": {
            "franchise_id": "F001",
            "franchise_ids_involved": "not-a-list",
        }}
        assert _franchise_ids_from_payload(event) == {"F001"}


# ── Store-backed queries ─────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    """Fresh DB with seeded events for franchise queries.

    The trade event uses the canonical ``franchise_ids_involved`` field
    (post-S10-fix shape). raw_mfl_json is left on the envelope as it
    would be in real ingest, but queries do not depend on it.
    """
    db = tmp_path / "test.sqlite"
    s = SQLiteStore(db_path=db)
    s.init_db(SCHEMA_PATH.read_text())
    s.append_events([
        {
            "league_id": LEAGUE, "season": SEASON,
            "external_source": "test", "external_id": "draft_1",
            "event_type": "DRAFT_PICK",
            "occurred_at": "2024-09-01T12:00:00Z",
            "payload": {"franchise_id": "F001", "player_id": "P001"},
        },
        {
            "league_id": LEAGUE, "season": SEASON,
            "external_source": "test", "external_id": "waiver_1",
            "event_type": "WAIVER_BID_AWARDED",
            "occurred_at": "2024-09-02T12:00:00Z",
            "payload": {"franchise_id": "F001", "player_id": "P002"},
        },
        {
            "league_id": LEAGUE, "season": SEASON,
            "external_source": "test", "external_id": "trade_1",
            "event_type": "TRANSACTION_TRADE",
            "occurred_at": "2024-09-03T12:00:00Z",
            "payload": {
                "franchise_id": "F001",
                "franchise_ids_involved": ["F001", "F002"],
                "raw_mfl_json": json.dumps({"franchise": "F001", "franchise2": "F002"}),
            },
        },
        {
            "league_id": LEAGUE, "season": SEASON,
            "external_source": "test", "external_id": "fa_1",
            "event_type": "TRANSACTION_FREE_AGENT",
            "occurred_at": "2024-09-04T12:00:00Z",
            "payload": {"franchise_id": "F002"},
        },
    ])
    # Canonicalize so the canonical view has data (franchise_queries reads canonical by default)
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=str(db))
    return s


class TestEventsForFranchise:
    def test_f001_events(self, store):
        """F001 should match draft, waiver, and trade."""
        events = events_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F001")
        types = {e["event_type"] for e in events}
        assert "DRAFT_PICK" in types
        assert "WAIVER_BID_AWARDED" in types
        assert "TRANSACTION_TRADE" in types

    def test_f002_events(self, store):
        """F002 matches trade (via franchise_ids_involved) and free agent."""
        events = events_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F002")
        types = {e["event_type"] for e in events}
        assert "TRANSACTION_TRADE" in types
        assert "TRANSACTION_FREE_AGENT" in types

    def test_unknown_franchise_empty(self, store):
        events = events_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F999")
        assert events == []


class TestTypedFranchiseQueries:
    def test_draft_picks(self, store):
        result = draft_picks_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F001")
        assert len(result) == 1
        assert result[0]["event_type"] == "DRAFT_PICK"

    def test_waiver_awards(self, store):
        result = waiver_awards_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F001")
        assert len(result) == 1

    def test_trades(self, store):
        result = trades_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F001")
        assert len(result) == 1

    def test_free_agent_moves(self, store):
        result = free_agent_moves_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F002")
        assert len(result) == 1

    def test_no_matches(self, store):
        assert draft_picks_for_franchise(store, league_id=LEAGUE, season=SEASON, franchise_id="F002") == []
