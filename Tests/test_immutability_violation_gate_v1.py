"""Phase 5D — Immutability Violation Gate.

Constitution claim: 'Facts are immutable; narratives are derived.'
Runs the FULL pipeline and verifies no operation modifies memory_events.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.storage.migrate import init_and_migrate
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_runs import upsert_recap_run, RecapRunRecord
from squadvault.core.recaps.recap_artifacts import (
    create_recap_artifact_draft_idempotent,
    approve_recap_artifact,
)
from squadvault.recaps.weekly_recap_lifecycle import (
    generate_weekly_recap_draft,
    approve_latest_weekly_recap,
)

LEAGUE = "immutability_gate_league"
SEASON = 2024


@pytest.fixture
def pipeline_db(tmp_path):
    db_path = str(tmp_path / "immutable.sqlite")
    init_and_migrate(db_path)
    store = SQLiteStore(db_path=Path(db_path))
    locks = [
        {"league_id": LEAGUE, "season": SEASON, "external_source": "test", "external_id": "lock_w1",
         "event_type": "TRANSACTION_LOCK_ALL_PLAYERS", "occurred_at": "2024-09-05T12:00:00Z",
         "payload": {"type": "LOCK_ALL_PLAYERS", "week": 1}},
        {"league_id": LEAGUE, "season": SEASON, "external_source": "test", "external_id": "lock_w2",
         "event_type": "TRANSACTION_LOCK_ALL_PLAYERS", "occurred_at": "2024-09-12T12:00:00Z",
         "payload": {"type": "LOCK_ALL_PLAYERS", "week": 2}},
        {"league_id": LEAGUE, "season": SEASON, "external_source": "test", "external_id": "lock_w3",
         "event_type": "TRANSACTION_LOCK_ALL_PLAYERS", "occurred_at": "2024-09-19T12:00:00Z",
         "payload": {"type": "LOCK_ALL_PLAYERS", "week": 3}},
    ]
    activity = [
        {"league_id": LEAGUE, "season": SEASON, "external_source": "test", "external_id": "waiver_1",
         "event_type": "WAIVER_BID_AWARDED", "occurred_at": "2024-09-06T10:00:00Z",
         "payload": {"franchise_id": "F1", "player_id": "P100", "bid_amount": "25"}},
        {"league_id": LEAGUE, "season": SEASON, "external_source": "test", "external_id": "waiver_2",
         "event_type": "WAIVER_BID_AWARDED", "occurred_at": "2024-09-07T10:00:00Z",
         "payload": {"franchise_id": "F2", "player_id": "P200", "bid_amount": "15"}},
        {"league_id": LEAGUE, "season": SEASON, "external_source": "test", "external_id": "fa_1",
         "event_type": "TRANSACTION_FREE_AGENT", "occurred_at": "2024-09-08T10:00:00Z",
         "payload": {"franchise_id": "F3", "players_added_ids": ["P300"], "players_dropped_ids": ["P400"]}},
    ]
    store.append_events(locks + activity)
    return db_path


def _snapshot_memory_events(db_path):
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT id, league_id, season, event_type, occurred_at, ingested_at, payload_json "
        "FROM memory_events ORDER BY id"
    ).fetchall()
    con.close()
    return rows


class TestImmutabilityViolationGate:
    def test_full_pipeline_preserves_memory_events(self, pipeline_db):
        before = _snapshot_memory_events(pipeline_db)
        assert len(before) >= 6

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=pipeline_db)
        assert before == _snapshot_memory_events(pipeline_db), "Canonicalization must not modify memory_events"

        sel = select_weekly_recap_events_v1(db_path=pipeline_db, league_id=LEAGUE, season=SEASON, week_index=1)
        assert before == _snapshot_memory_events(pipeline_db), "Selection must not modify memory_events"

        upsert_recap_run(pipeline_db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode, window_start=sel.window.window_start,
            window_end=sel.window.window_end, selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids], counts_by_type=sel.counts_by_type,
        ))
        assert before == _snapshot_memory_events(pipeline_db), "recap_runs upsert must not modify memory_events"

        generate_weekly_recap_draft(db_path=pipeline_db, league_id=LEAGUE, season=SEASON,
                                    week_index=1, reason="immutability_test")
        assert before == _snapshot_memory_events(pipeline_db), "Draft generation must not modify memory_events"

        approve_latest_weekly_recap(db_path=pipeline_db, league_id=LEAGUE, season=SEASON,
                                    week_index=1, approved_by="test_founder")
        assert before == _snapshot_memory_events(pipeline_db), "Approval must not modify memory_events"

    def test_re_canonicalize_preserves_memory_events(self, pipeline_db):
        before = _snapshot_memory_events(pipeline_db)
        for _ in range(3):
            canonicalize(league_id=LEAGUE, season=SEASON, db_path=pipeline_db)
        assert before == _snapshot_memory_events(pipeline_db)

    def test_draft_regeneration_preserves_memory_events(self, pipeline_db):
        before = _snapshot_memory_events(pipeline_db)
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=pipeline_db)
        sel = select_weekly_recap_events_v1(db_path=pipeline_db, league_id=LEAGUE, season=SEASON, week_index=1)
        upsert_recap_run(pipeline_db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode, window_start=sel.window.window_start,
            window_end=sel.window.window_end, selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids], counts_by_type=sel.counts_by_type,
        ))
        generate_weekly_recap_draft(db_path=pipeline_db, league_id=LEAGUE, season=SEASON,
                                    week_index=1, reason="first_draft")
        generate_weekly_recap_draft(db_path=pipeline_db, league_id=LEAGUE, season=SEASON,
                                    week_index=1, reason="regeneration", force=True)
        assert before == _snapshot_memory_events(pipeline_db)
