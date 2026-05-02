"""Behavioral gate test: EAL included_count flows correctly end-to-end.

Proves that:
1. The gating check (upsert_recap_run) stores canonical_ids_json
2. generate_weekly_recap_draft reads canonical_ids_json → included_count
3. The EAL evaluator receives the actual count (not None)
4. The correct directive is persisted to recap_runs.editorial_attunement_v1

Density thresholds (from editorial_attunement_v1.py):
  - 0 events → AMBIGUITY_PREFER_SILENCE
  - 1-2 events → LOW_CONFIDENCE_RESTRAINT
  - 3-7 events → MODERATE_CONFIDENCE_ONLY
  - ≥8 events → HIGH_CONFIDENCE_ALLOWED
  - None (unknown) → LOW_CONFIDENCE_RESTRAINT
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.eal.editorial_attunement_v1 import (
    EAL_AMBIGUITY_PREFER_SILENCE,
    EAL_HIGH_CONFIDENCE_ALLOWED,
    EAL_LOW_CONFIDENCE_RESTRAINT,
    EAL_MODERATE_CONFIDENCE_ONLY,
)
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.storage.migrate import init_and_migrate
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft

LEAGUE = "eal_flow_test_league"
SEASON = 2024


@pytest.fixture
def fresh_db(tmp_path):
    """Create a fresh DB from schema.sql via init_and_migrate."""
    db_path = str(tmp_path / "eal_flow.sqlite")
    init_and_migrate(db_path)
    return db_path


def _lock(week: int, ts: str) -> dict:
    return {
        "league_id": LEAGUE,
        "season": SEASON,
        "external_source": "test",
        "external_id": f"lock_w{week}_{ts}",
        "event_type": "TRANSACTION_LOCK_ALL_PLAYERS",
        "occurred_at": ts,
        "payload": {"type": "LOCK_ALL_PLAYERS", "week": week},
    }


def _waiver(franchise_id: str, player_id: str, bid: str, ts: str, ext_id: str) -> dict:
    return {
        "league_id": LEAGUE,
        "season": SEASON,
        "external_source": "test",
        "external_id": ext_id,
        "event_type": "WAIVER_BID_AWARDED",
        "occurred_at": ts,
        "payload": {
            "franchise_id": franchise_id,
            "player_id": player_id,
            "bid_amount": bid,
        },
    }


def _free_agent(franchise_id: str, added: str, dropped: str, ts: str, ext_id: str) -> dict:
    return {
        "league_id": LEAGUE,
        "season": SEASON,
        "external_source": "test",
        "external_id": ext_id,
        "event_type": "TRANSACTION_FREE_AGENT",
        "occurred_at": ts,
        "payload": {
            "franchise_id": franchise_id,
            "players_added_ids": added,
            "players_dropped_ids": dropped,
        },
    }


def _matchup(week: int, winner: str, loser: str, w_score: str, l_score: str, ts: str, ext_id: str) -> dict:
    return {
        "league_id": LEAGUE,
        "season": SEASON,
        "external_source": "test",
        "external_id": ext_id,
        "event_type": "WEEKLY_MATCHUP_RESULT",
        "occurred_at": ts,
        "payload": {
            "week": str(week),
            "winner_franchise_id": winner,
            "loser_franchise_id": loser,
            "winner_score": w_score,
            "loser_score": l_score,
        },
    }


def _setup_week(fresh_db: str, week_index: int, events: list[dict]) -> None:
    """Ingest events, canonicalize, select, and upsert recap_run for a given week."""
    store = SQLiteStore(db_path=Path(fresh_db))
    store.append_events(events)
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=fresh_db)

    sel = select_weekly_recap_events_v1(
        db_path=fresh_db,
        league_id=LEAGUE,
        season=SEASON,
        week_index=week_index,
    )

    upsert_recap_run(
        fresh_db,
        RecapRunRecord(
            league_id=LEAGUE,
            season=SEASON,
            week_index=week_index,
            state="DRAFTED",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=sel.canonical_ids,
            counts_by_type=sel.counts_by_type,
            reason=None,
        ),
    )


def _read_persisted_eal(db_path: str, week_index: int) -> str | None:
    """Read the EAL directive persisted to recap_runs."""
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT editorial_attunement_v1 FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
        (LEAGUE, SEASON, week_index),
    ).fetchone()
    con.close()
    return row[0] if row else None


def _read_canonical_ids_json(db_path: str, week_index: int) -> str | None:
    """Read canonical_ids_json stored in recap_runs."""
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
        (LEAGUE, SEASON, week_index),
    ).fetchone()
    con.close()
    return row[0] if row else None


class TestEALIncludedCountFlow:
    """Verify included_count flows from gating check → EAL → persisted directive."""

    def test_dense_week_gets_high_confidence(self, fresh_db):
        """≥8 canonical events in window → HIGH_CONFIDENCE_ALLOWED."""
        locks = [
            _lock(1, "2024-09-05T12:00:00Z"),
            _lock(2, "2024-09-12T12:00:00Z"),
        ]
        # 5 matchups + 4 waivers = 9 distinct canonical events (≥8)
        activity = [
            _matchup(1, "F01", "F02", "120", "100", "2024-09-06T10:00:00Z", "m1"),
            _matchup(1, "F03", "F04", "110", "105", "2024-09-06T10:01:00Z", "m2"),
            _matchup(1, "F05", "F06", "130", "90", "2024-09-06T10:02:00Z", "m3"),
            _matchup(1, "F07", "F08", "115", "112", "2024-09-06T10:03:00Z", "m4"),
            _matchup(1, "F09", "F10", "125", "95", "2024-09-06T10:04:00Z", "m5"),
            _waiver("F01", "P101", "25", "2024-09-07T10:00:00Z", "w1"),
            _waiver("F02", "P102", "15", "2024-09-08T10:00:00Z", "w2"),
            _waiver("F03", "P103", "10", "2024-09-09T10:00:00Z", "w3"),
            _waiver("F04", "P104", "5", "2024-09-10T10:00:00Z", "w4"),
        ]
        _setup_week(fresh_db, 1, locks + activity)

        # Verify canonical_ids_json is populated with ≥8 IDs
        ids_json = _read_canonical_ids_json(fresh_db, 1)
        assert ids_json is not None
        ids = json.loads(ids_json)
        assert len(ids) >= 8, f"Expected ≥8 canonical events, got {len(ids)}"

        # Generate draft — this evaluates and persists EAL
        result = generate_weekly_recap_draft(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="test_dense",
        )
        assert result.created_new is True

        # Verify the persisted directive
        directive = _read_persisted_eal(fresh_db, 1)
        assert directive == EAL_HIGH_CONFIDENCE_ALLOWED, (
            f"Dense week (≥8 events) should get HIGH_CONFIDENCE_ALLOWED, got {directive}"
        )

    def test_sparse_week_gets_low_confidence(self, fresh_db):
        """1-2 canonical events in window → LOW_CONFIDENCE_RESTRAINT."""
        locks = [
            _lock(1, "2024-09-05T12:00:00Z"),
            _lock(2, "2024-09-12T12:00:00Z"),
        ]
        activity = [
            _waiver("F01", "P101", "25", "2024-09-07T10:00:00Z", "w1"),
        ]
        _setup_week(fresh_db, 1, locks + activity)

        ids_json = _read_canonical_ids_json(fresh_db, 1)
        ids = json.loads(ids_json)
        assert 1 <= len(ids) <= 2, f"Expected 1-2 canonical events, got {len(ids)}"

        result = generate_weekly_recap_draft(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="test_sparse",
        )
        assert result.created_new is True

        directive = _read_persisted_eal(fresh_db, 1)
        assert directive == EAL_LOW_CONFIDENCE_RESTRAINT, (
            f"Sparse week (1-2 events) should get LOW_CONFIDENCE_RESTRAINT, got {directive}"
        )

    def test_empty_week_gets_silence(self, fresh_db):
        """0 canonical events in window → AMBIGUITY_PREFER_SILENCE."""
        locks = [
            _lock(1, "2024-09-05T12:00:00Z"),
            _lock(2, "2024-09-12T12:00:00Z"),
        ]
        # No activity events — just lock boundaries
        _setup_week(fresh_db, 1, locks)

        ids_json = _read_canonical_ids_json(fresh_db, 1)
        ids = json.loads(ids_json)
        assert len(ids) == 0, f"Expected 0 canonical events, got {len(ids)}"

        result = generate_weekly_recap_draft(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="test_empty",
        )
        assert result.created_new is True

        directive = _read_persisted_eal(fresh_db, 1)
        assert directive == EAL_AMBIGUITY_PREFER_SILENCE, (
            f"Empty week (0 events) should get AMBIGUITY_PREFER_SILENCE, got {directive}"
        )

    def test_moderate_week_gets_moderate_confidence(self, fresh_db):
        """3-7 canonical events in window → MODERATE_CONFIDENCE_ONLY."""
        locks = [
            _lock(1, "2024-09-05T12:00:00Z"),
            _lock(2, "2024-09-12T12:00:00Z"),
        ]
        # 5 matchups = 5 distinct canonical events (3-7 range)
        activity = [
            _matchup(1, "F01", "F02", "120", "100", "2024-09-06T10:00:00Z", "m1"),
            _matchup(1, "F03", "F04", "110", "105", "2024-09-06T10:01:00Z", "m2"),
            _matchup(1, "F05", "F06", "130", "90", "2024-09-06T10:02:00Z", "m3"),
            _matchup(1, "F07", "F08", "115", "112", "2024-09-06T10:03:00Z", "m4"),
            _matchup(1, "F09", "F10", "125", "95", "2024-09-06T10:04:00Z", "m5"),
        ]
        _setup_week(fresh_db, 1, locks + activity)

        ids_json = _read_canonical_ids_json(fresh_db, 1)
        ids = json.loads(ids_json)
        assert 3 <= len(ids) <= 7, f"Expected 3-7 canonical events, got {len(ids)}"

        result = generate_weekly_recap_draft(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
            reason="test_moderate",
        )
        assert result.created_new is True

        directive = _read_persisted_eal(fresh_db, 1)
        assert directive == EAL_MODERATE_CONFIDENCE_ONLY, (
            f"Moderate week (3-7 events) should get MODERATE_CONFIDENCE_ONLY, got {directive}"
        )

    def test_canonical_ids_json_is_not_null(self, fresh_db):
        """Verify the canonical_ids_json column is populated (not NULL) after gating."""
        locks = [
            _lock(1, "2024-09-05T12:00:00Z"),
            _lock(2, "2024-09-12T12:00:00Z"),
        ]
        activity = [
            _waiver("F01", "P101", "25", "2024-09-07T10:00:00Z", "w1"),
            _waiver("F02", "P102", "15", "2024-09-08T10:00:00Z", "w2"),
            _waiver("F03", "P103", "10", "2024-09-09T10:00:00Z", "w3"),
        ]
        _setup_week(fresh_db, 1, locks + activity)

        ids_json = _read_canonical_ids_json(fresh_db, 1)
        assert ids_json is not None, "canonical_ids_json must not be NULL after gating"
        assert ids_json != "", "canonical_ids_json must not be empty string after gating"

        ids = json.loads(ids_json)
        assert isinstance(ids, list), "canonical_ids_json must be a JSON array"
        assert len(ids) >= 3, f"Expected ≥3 canonical IDs, got {len(ids)}"
