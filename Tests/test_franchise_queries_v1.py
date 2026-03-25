"""Tests for squadvault.core.queries.franchise_queries.

Covers: _franchise_ids_from_payload, events_for_franchise,
draft_picks_for_franchise, trades_for_franchise.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.queries.franchise_queries import (
    _franchise_ids_from_payload,
    events_for_franchise,
    draft_picks_for_franchise,
    waiver_awards_for_franchise,
    trades_for_franchise,
    free_agent_moves_for_franchise,
)
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.canonicalize.run_canonicalize import canonicalize

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


# ── _franchise_ids_from_payload (pure) ───────────────────────────────

class TestFranchiseIdsFromPayload:
    def test_simple_franchise_id(self):
        event = {"payload": {"franchise_id": "F001"}}
        assert _franchise_ids_from_payload(event) == {"F001"}

    def test_trade_with_raw_mfl_json(self):
        raw = json.dumps({"franchise": "F001", "franchise2": "F002"})
        event = {"payload": {"raw_mfl_json": raw}}
        ids = _franchise_ids_from_payload(event)
        assert "F001" in ids
        assert "F002" in ids

    def test_franchise_id_plus_raw(self):
        raw = json.dumps({"franchise2": "F002"})
        event = {"payload": {"franchise_id": "F001", "raw_mfl_json": raw}}
        ids = _franchise_ids_from_payload(event)
        assert ids == {"F001", "F002"}

    def test_empty_payload(self):
        assert _franchise_ids_from_payload({"payload": {}}) == set()

    def test_no_payload(self):
        assert _franchise_ids_from_payload({}) == set()

    def test_invalid_raw_json(self):
        event = {"payload": {"raw_mfl_json": "not json"}}
        assert _franchise_ids_from_payload(event) == set()

    def test_franchise_id_as_list(self):
        event = {"payload": {"franchise_id": ["F001", "F002"]}}
        assert _franchise_ids_from_payload(event) == {"F001", "F002"}

    def test_ignores_non_franchise_keys_in_raw(self):
        raw = json.dumps({"player_id": "P001", "franchise": "F001"})
        event = {"payload": {"raw_mfl_json": raw}}
        ids = _franchise_ids_from_payload(event)
        assert ids == {"F001"}


# ── Store-backed queries ─────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    """Fresh DB with seeded events for franchise queries."""
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
            "payload": {"franchise_id": "F001", "raw_mfl_json": json.dumps({"franchise": "F001", "franchise2": "F002"})},
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
        """F002 should match trade (via raw_mfl_json) and free agent."""
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
