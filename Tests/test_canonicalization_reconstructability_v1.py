"""Phase 1A — Canonicalization Reconstructability Test.

Invariant: canonical_events is a deterministic, reproducible projection
over the immutable memory_events ledger. Dropping and rebuilding
canonical_events from the same ledger must produce identical results.

This test verifies the claim: "Canonical projections may change when the
ledger grows, but they are always fully reconstructable from the
immutable ledger."
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.canonicalize.run_canonicalize import canonicalize

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "recon_test_league"
SEASON = 2024


@pytest.fixture
def db(tmp_path):
    """Fresh DB from schema.sql."""
    db_path = str(tmp_path / "recon_test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


def _insert_memory_event(db_path, event_type, payload, id_suffix, occurred_at="2024-10-01T12:00:00Z"):
    """Insert a single memory event into the ledger."""
    con = sqlite3.connect(db_path)
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id,
            event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            LEAGUE, SEASON, "test", f"recon_{event_type}_{id_suffix}",
            event_type, occurred_at, "2024-10-01T13:00:00Z",
            json.dumps(payload),
        ),
    )
    con.commit()
    con.close()


def _snapshot_canonical(db_path):
    """Capture semantically meaningful canonical_events state.

    Returns a set of tuples: (action_fingerprint, best_memory_event_id, best_score, event_type)
    These are the fields that define canonical truth. We exclude id (autoincrement)
    and updated_at (wall-clock timestamp) because they are non-deterministic metadata.
    """
    con = sqlite3.connect(db_path)
    rows = con.execute(
        """SELECT action_fingerprint, best_memory_event_id, best_score, event_type
           FROM canonical_events
           WHERE league_id = ? AND season = ?
           ORDER BY action_fingerprint""",
        (LEAGUE, SEASON),
    ).fetchall()
    con.close()
    return set(rows)


def _seed_diverse_events(db_path):
    """Insert a realistic mix of event types for reconstruction testing."""
    # Waiver bid awards with deduplication potential
    _insert_memory_event(db_path, "WAIVER_BID_AWARDED", {
        "franchise_id": "F01", "player_id": "P100", "bid_amount": "25",
    }, id_suffix="wba1", occurred_at="2024-10-01T12:00:00Z")
    _insert_memory_event(db_path, "WAIVER_BID_AWARDED", {
        "franchise_id": "F01", "player_id": "P100", "bid_amount": "25",
        "raw_mfl_json": json.dumps({"type": "BBID_WAIVER", "amount": "25"}),
    }, id_suffix="wba1_dup", occurred_at="2024-10-01T12:00:00Z")

    # A different waiver bid
    _insert_memory_event(db_path, "WAIVER_BID_AWARDED", {
        "franchise_id": "F02", "player_id": "P200", "bid_amount": "10",
    }, id_suffix="wba2", occurred_at="2024-10-02T12:00:00Z")

    # Stub BBID that should be skipped
    _insert_memory_event(db_path, "WAIVER_BID_AWARDED", {
        "raw_mfl_json": json.dumps({"type": "BBID_WAIVER"}),
    }, id_suffix="stub1", occurred_at="2024-10-03T12:00:00Z")

    # Free agent transactions
    _insert_memory_event(db_path, "TRANSACTION_FREE_AGENT", {
        "franchise_id": "F01", "players_added_ids": ["P300"],
        "players_dropped_ids": ["P301"],
    }, id_suffix="fa1", occurred_at="2024-10-04T12:00:00Z")
    _insert_memory_event(db_path, "TRANSACTION_FREE_AGENT", {
        "franchise_id": "F03", "players_added_ids": ["P400"],
        "players_dropped_ids": [],
    }, id_suffix="fa2", occurred_at="2024-10-05T12:00:00Z")

    # Fallback-fingerprint events (generic event type, 1:1 mapping)
    _insert_memory_event(db_path, "DRAFT_PICK", {
        "franchise_id": "F01", "player_id": "P500", "round": 1, "pick": 3,
    }, id_suffix="dp1", occurred_at="2024-09-01T12:00:00Z")
    _insert_memory_event(db_path, "DRAFT_PICK", {
        "franchise_id": "F02", "player_id": "P501", "round": 1, "pick": 4,
    }, id_suffix="dp2", occurred_at="2024-09-01T12:01:00Z")


class TestCanonicalizationReconstructability:
    """Verify canonical_events can be dropped and rebuilt identically."""

    def test_drop_and_rebuild_produces_identical_output(self, db):
        """Core reconstructability invariant.

        Steps:
        1. Seed diverse memory events
        2. Canonicalize → snapshot A
        3. DROP canonical_events (and membership)
        4. Recreate tables from schema
        5. Re-canonicalize → snapshot B
        6. Assert A == B
        """
        _seed_diverse_events(db)

        # First canonicalization
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        snapshot_a = _snapshot_canonical(db)
        assert len(snapshot_a) > 0, "Sanity: should have canonical events"

        # Drop and recreate
        con = sqlite3.connect(db)
        con.execute("DELETE FROM canonical_membership")
        con.execute("DELETE FROM canonical_events")
        con.commit()
        remaining = con.execute("SELECT COUNT(*) FROM canonical_events").fetchone()[0]
        assert remaining == 0, "canonical_events should be empty after delete"
        con.close()

        # Verify memory_events are untouched
        con = sqlite3.connect(db)
        mem_count = con.execute(
            "SELECT COUNT(*) FROM memory_events WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchone()[0]
        con.close()
        assert mem_count > 0, "memory_events must survive canonical wipe"

        # Rebuild from ledger
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        snapshot_b = _snapshot_canonical(db)

        # The core invariant
        assert snapshot_a == snapshot_b, (
            "Canonical projection must be fully reconstructable from the immutable ledger. "
            f"Diff: A-B={snapshot_a - snapshot_b}, B-A={snapshot_b - snapshot_a}"
        )

    def test_memory_events_unchanged_after_canonicalize(self, db):
        """Canonicalization must never modify the immutable ledger."""
        _seed_diverse_events(db)

        # Snapshot memory_events before
        con = sqlite3.connect(db)
        before = con.execute(
            "SELECT id, league_id, season, event_type, occurred_at, ingested_at, payload_json "
            "FROM memory_events WHERE league_id=? AND season=? ORDER BY id",
            (LEAGUE, SEASON),
        ).fetchall()
        con.close()

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        # Snapshot after
        con = sqlite3.connect(db)
        after = con.execute(
            "SELECT id, league_id, season, event_type, occurred_at, ingested_at, payload_json "
            "FROM memory_events WHERE league_id=? AND season=? ORDER BY id",
            (LEAGUE, SEASON),
        ).fetchall()
        con.close()

        assert before == after, "memory_events must be immutable across canonicalization"

    def test_stub_bbid_excluded_consistently(self, db):
        """Stub BBID rows must be excluded in both initial and reconstructed runs."""
        _seed_diverse_events(db)

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        snap1 = _snapshot_canonical(db)

        # Wipe and rebuild
        con = sqlite3.connect(db)
        con.execute("DELETE FROM canonical_membership")
        con.execute("DELETE FROM canonical_events")
        con.commit()
        con.close()

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        snap2 = _snapshot_canonical(db)

        # Both runs should have the same count (stub excluded in both)
        assert len(snap1) == len(snap2)
        assert snap1 == snap2

    def test_best_selection_stable_across_rebuild(self, db):
        """When duplicates exist, the same best_memory_event_id is chosen each time."""
        # Insert two events that share a fingerprint but differ in score
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "franchise_id": "F10", "player_id": "P900", "bid_amount": "50",
        }, id_suffix="best_a", occurred_at="2024-10-10T12:00:00Z")
        _insert_memory_event(db, "WAIVER_BID_AWARDED", {
            "franchise_id": "F10", "player_id": "P900", "bid_amount": "50",
            "raw_mfl_json": json.dumps({"type": "BBID_WAIVER", "amount": "50", "extra": "data"}),
        }, id_suffix="best_b", occurred_at="2024-10-10T12:00:00Z")

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        snap1 = _snapshot_canonical(db)

        con = sqlite3.connect(db)
        con.execute("DELETE FROM canonical_membership")
        con.execute("DELETE FROM canonical_events")
        con.commit()
        con.close()

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        snap2 = _snapshot_canonical(db)

        assert snap1 == snap2, "Best-event selection must be deterministic across rebuilds"
