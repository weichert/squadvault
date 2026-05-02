"""Integration test: fresh DB → ingest → canonicalize → select → draft → approve → export.

Exercises the full deterministic pipeline end-to-end without LLM calls.
Verifies that the chain of immutable operations produces correct, traceable results.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.exports.approved_weekly_recap_export_v1 import (
    fetch_latest_approved_weekly_recap,
    write_approved_weekly_recap_export_bundle,
)
from squadvault.core.recaps.recap_artifacts import (
    approve_recap_artifact,
    create_recap_artifact_draft_idempotent,
    latest_approved_version,
)
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.storage.migrate import init_and_migrate
from squadvault.core.storage.sqlite_store import SQLiteStore

LEAGUE = "integration_test_league"
SEASON = 2024


@pytest.fixture
def fresh_db(tmp_path):
    """Create a fresh DB from schema.sql via init_and_migrate."""
    db_path = str(tmp_path / "integration.sqlite")
    init_and_migrate(db_path)

    # Verify core tables exist
    con = sqlite3.connect(db_path)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    con.close()
    assert "memory_events" in tables
    assert "canonical_events" in tables
    assert "recap_artifacts" in tables
    assert "recap_runs" in tables
    return db_path


def _make_lock_event(week: int, ts: str) -> dict:
    """Build a LOCK_ALL_PLAYERS event."""
    return {
        "league_id": LEAGUE,
        "season": SEASON,
        "external_source": "test",
        "external_id": f"lock_w{week}_{ts}",
        "event_type": "TRANSACTION_LOCK_ALL_PLAYERS",
        "occurred_at": ts,
        "payload": {"type": "LOCK_ALL_PLAYERS", "week": week},
    }


def _make_waiver_event(franchise_id: str, player_id: str, bid: str, ts: str, ext_id: str) -> dict:
    """Build a WAIVER_BID_AWARDED event."""
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


def _make_free_agent_event(franchise_id: str, added: str, dropped: str, ts: str, ext_id: str) -> dict:
    """Build a TRANSACTION_FREE_AGENT event."""
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


class TestFullPipeline:
    """End-to-end: ingest → canonicalize → select → draft → approve → export."""

    def test_full_pipeline(self, fresh_db, tmp_path):
        store = SQLiteStore(db_path=Path(fresh_db))

        # ── Step 1: Ingest lock events (week boundaries) ────────────
        locks = [
            _make_lock_event(1, "2024-09-05T12:00:00Z"),
            _make_lock_event(2, "2024-09-12T12:00:00Z"),
            _make_lock_event(3, "2024-09-19T12:00:00Z"),
        ]
        inserted, skipped = store.append_events(locks)
        assert inserted == 3

        # ── Step 2: Ingest week 1 activity ──────────────────────────
        activity = [
            _make_waiver_event("F1", "P100", "25", "2024-09-06T10:00:00Z", "waiver_1"),
            _make_waiver_event("F2", "P200", "15", "2024-09-07T10:00:00Z", "waiver_2"),
            _make_free_agent_event("F3", "P300", "P400", "2024-09-08T10:00:00Z", "fa_1"),
        ]
        inserted, skipped = store.append_events(activity)
        assert inserted == 3

        # ── Step 3: Canonicalize ────────────────────────────────────
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=fresh_db)

        con = sqlite3.connect(fresh_db)
        canon_count = con.execute(
            "SELECT COUNT(*) FROM canonical_events WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchone()[0]
        con.close()
        assert canon_count >= 3  # 3 locks + 3 activity (some may dedupe)

        # ── Step 4: Select week 1 events ────────────────────────────
        sel = select_weekly_recap_events_v1(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
        )
        assert sel.window.mode == "LOCK_TO_LOCK"
        assert sel.window.window_start == "2024-09-05T12:00:00Z"
        assert sel.window.window_end == "2024-09-12T12:00:00Z"
        assert len(sel.canonical_ids) >= 2  # waiver + FA events in window
        assert len(sel.fingerprint) == 64  # SHA-256 hex

        # ── Step 5: Create DRAFT artifact ───────────────────────────
        rendered = f"# Week 1 Recap\n\nEvents: {len(sel.canonical_ids)}"
        version, created = create_recap_artifact_draft_idempotent(
            fresh_db, LEAGUE, SEASON, 1, sel.fingerprint,
            sel.window.window_start, sel.window.window_end,
            rendered,
        )
        assert version == 1
        assert created is True

        # Idempotency: same fingerprint → no new version
        v2, c2 = create_recap_artifact_draft_idempotent(
            fresh_db, LEAGUE, SEASON, 1, sel.fingerprint,
            sel.window.window_start, sel.window.window_end,
            rendered,
        )
        assert v2 == 1
        assert c2 is False

        # ── Step 6: Approve artifact ────────────────────────────────
        approve_recap_artifact(fresh_db, LEAGUE, SEASON, 1, version, "test_founder")
        assert latest_approved_version(fresh_db, LEAGUE, SEASON, 1) == version

        # ── Step 7: Fetch and export ────────────────────────────────
        artifact = fetch_latest_approved_weekly_recap(fresh_db, LEAGUE, SEASON, 1)
        assert artifact.state == "APPROVED"
        assert artifact.approved_by == "test_founder"
        assert artifact.selection_fingerprint == sel.fingerprint

        out_dir = tmp_path / "export"
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir)
        assert Path(manifest.recap_md).exists()
        assert Path(manifest.recap_json).exists()
        assert Path(manifest.metadata_json).exists()

        meta = json.loads(Path(manifest.metadata_json).read_text())
        assert meta["league_id"] == LEAGUE
        assert meta["state"] == "APPROVED"
        assert meta["selection_fingerprint"] == sel.fingerprint

    def test_empty_week_produces_empty_selection(self, fresh_db):
        """Week with no activity → empty selection, not a crash."""
        store = SQLiteStore(db_path=Path(fresh_db))
        locks = [
            _make_lock_event(1, "2024-09-05T12:00:00Z"),
            _make_lock_event(2, "2024-09-12T12:00:00Z"),
        ]
        store.append_events(locks)
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=fresh_db)

        sel = select_weekly_recap_events_v1(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
        )
        assert sel.window.mode == "LOCK_TO_LOCK"
        assert sel.canonical_ids == []
        assert len(sel.fingerprint) == 64

    def test_no_locks_produces_unsafe_window(self, fresh_db):
        """No lock events → UNSAFE window, empty selection."""
        sel = select_weekly_recap_events_v1(
            db_path=fresh_db,
            league_id=LEAGUE,
            season=SEASON,
            week_index=1,
        )
        assert sel.window.mode == "UNSAFE"
        assert sel.canonical_ids == []

    def test_selection_determinism(self, fresh_db):
        """Same inputs produce identical fingerprints."""
        store = SQLiteStore(db_path=Path(fresh_db))
        events = [
            _make_lock_event(1, "2024-09-05T12:00:00Z"),
            _make_lock_event(2, "2024-09-12T12:00:00Z"),
            _make_waiver_event("F1", "P100", "25", "2024-09-06T10:00:00Z", "w1"),
        ]
        store.append_events(events)
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=fresh_db)

        sel1 = select_weekly_recap_events_v1(
            db_path=fresh_db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        sel2 = select_weekly_recap_events_v1(
            db_path=fresh_db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        assert sel1.fingerprint == sel2.fingerprint
        assert sel1.canonical_ids == sel2.canonical_ids

    def test_canonicalize_idempotent(self, fresh_db):
        """Running canonicalize twice produces same canonical count."""
        store = SQLiteStore(db_path=Path(fresh_db))
        events = [
            _make_lock_event(1, "2024-09-05T12:00:00Z"),
            _make_waiver_event("F1", "P100", "25", "2024-09-06T10:00:00Z", "w1"),
        ]
        store.append_events(events)

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=fresh_db)
        con = sqlite3.connect(fresh_db)
        count1 = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=fresh_db)
        con = sqlite3.connect(fresh_db)
        count2 = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        con.close()

        assert count1 == count2

    def test_append_idempotent(self, fresh_db):
        """Duplicate events are skipped on re-ingest."""
        store = SQLiteStore(db_path=Path(fresh_db))
        event = [_make_waiver_event("F1", "P100", "25", "2024-09-06T10:00:00Z", "dup_1")]
        ins1, skip1 = store.append_events(event)
        ins2, skip2 = store.append_events(event)
        assert ins1 == 1 and skip1 == 0
        assert ins2 == 0 and skip2 == 1
