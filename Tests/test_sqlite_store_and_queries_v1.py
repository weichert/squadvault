"""Tests for SQLiteStore and core.queries.event_queries.

Covers: append_events, fetch_events, idempotency,
event_queries filter functions.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.queries.event_queries import (
    fetch_all_events,
    fetch_by_event_type,
    fetch_by_event_type_prefix,
    draft_picks,
    waiver_awards,
    trades,
    free_agent_transactions,
)

LEAGUE = "test_league"
SEASON = 2024
SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"


@pytest.fixture
def store(tmp_path):
    """Create a SQLiteStore backed by a fresh DB from schema.sql."""
    db = tmp_path / "test.sqlite"
    s = SQLiteStore(db_path=db)
    s.init_db(SCHEMA_PATH.read_text())
    return s


def _event(event_type: str, ext_id: str, payload: dict = None) -> dict:
    """Build a minimal event dict."""
    return {
        "league_id": LEAGUE,
        "season": SEASON,
        "external_source": "test",
        "external_id": ext_id,
        "event_type": event_type,
        "occurred_at": "2024-10-01T12:00:00Z",
        "payload": payload or {},
    }


# ── SQLiteStore ──────────────────────────────────────────────────────

class TestSQLiteStore:
    def test_append_and_fetch(self, store):
        """Events can be appended and fetched."""
        inserted, skipped = store.append_events([_event("DRAFT_PICK", "e1")])
        assert inserted == 1
        assert skipped == 0
        events = store.fetch_events(league_id=LEAGUE, season=SEASON, use_canonical=False)
        assert len(events) == 1
        assert events[0]["event_type"] == "DRAFT_PICK"

    def test_idempotent_append(self, store):
        """Duplicate external_id is skipped, not inserted twice."""
        store.append_events([_event("DRAFT_PICK", "e1")])
        inserted, skipped = store.append_events([_event("DRAFT_PICK", "e1")])
        assert inserted == 0
        assert skipped == 1
        events = store.fetch_events(league_id=LEAGUE, season=SEASON, use_canonical=False)
        assert len(events) == 1

    def test_multiple_events(self, store):
        """Multiple distinct events are all inserted."""
        events = [
            _event("DRAFT_PICK", "e1"),
            _event("TRANSACTION_TRADE", "e2"),
            _event("WAIVER_BID_AWARDED", "e3"),
        ]
        inserted, _ = store.append_events(events)
        assert inserted == 3

    def test_fetch_respects_league_season(self, store):
        """Fetch filters by league_id and season."""
        store.append_events([_event("DRAFT_PICK", "e1")])
        # Different league
        events = store.fetch_events(league_id="other_league", season=SEASON, use_canonical=False)
        assert events == []
        # Different season
        events = store.fetch_events(league_id=LEAGUE, season=2020, use_canonical=False)
        assert events == []

    def test_payload_round_trips(self, store):
        """Payload dict round-trips through JSON storage."""
        payload = {"player_id": "P100", "round": 1, "pick": 3}
        store.append_events([_event("DRAFT_PICK", "e1", payload)])
        events = store.fetch_events(league_id=LEAGUE, season=SEASON, use_canonical=False)
        assert events[0]["payload"] == payload


# ── Event query helpers ──────────────────────────────────────────────

class TestEventQueries:
    @pytest.fixture(autouse=True)
    def _setup(self, store):
        """Seed test events."""
        self.store = store
        store.append_events([
            _event("DRAFT_PICK", "e1"),
            _event("DRAFT_PICK", "e2"),
            _event("TRANSACTION_TRADE", "e3"),
            _event("WAIVER_BID_AWARDED", "e4"),
            _event("TRANSACTION_FREE_AGENT", "e5"),
        ])

    def test_fetch_all(self):
        """fetch_all_events returns all events."""
        result = fetch_all_events(self.store, league_id=LEAGUE, season=SEASON)
        assert len(result) == 5

    def test_fetch_by_type(self):
        """fetch_by_event_type filters exactly."""
        result = fetch_by_event_type(self.store, league_id=LEAGUE, season=SEASON, event_type="DRAFT_PICK")
        assert len(result) == 2
        assert all(e["event_type"] == "DRAFT_PICK" for e in result)

    def test_fetch_by_prefix(self):
        """fetch_by_event_type_prefix filters by prefix."""
        result = fetch_by_event_type_prefix(self.store, league_id=LEAGUE, season=SEASON, prefix="TRANSACTION_")
        assert len(result) == 2  # TRADE + FREE_AGENT

    def test_draft_picks(self):
        assert len(draft_picks(self.store, league_id=LEAGUE, season=SEASON)) == 2

    def test_waiver_awards(self):
        assert len(waiver_awards(self.store, league_id=LEAGUE, season=SEASON)) == 1

    def test_trades(self):
        assert len(trades(self.store, league_id=LEAGUE, season=SEASON)) == 1

    def test_free_agent_transactions(self):
        assert len(free_agent_transactions(self.store, league_id=LEAGUE, season=SEASON)) == 1

    def test_empty_league(self):
        """Querying a non-existent league returns empty."""
        assert fetch_all_events(self.store, league_id="NOBODY", season=SEASON) == []
