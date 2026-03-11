"""Tests for weekly window computation and event selection.

Covers: _parse_iso_z, _to_iso_z, window_for_week_index,
_fingerprint_from_ids, select_weekly_recap_events_v1, SelectionResult.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.selection.weekly_windows_v1 import (
    WeeklyWindow,
    _parse_iso_z,
    _to_iso_z,
    window_for_week_index,
    WINDOW_MISSING_LOCKS,
    WINDOW_UNSAFE_TO_COMPUTE,
)
from squadvault.core.recaps.selection.weekly_selection_v1 import (
    SelectionResult,
    _fingerprint_from_ids,
    select_weekly_recap_events_v1,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


@pytest.fixture
def db_path(tmp_path):
    """Create a fresh DB and seed with lock events and canonical events."""
    db = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text())

    # Insert memory events for 3 lock timestamps
    locks = [
        ("2024-09-05T12:00:00Z", "lock_w1"),
        ("2024-09-12T12:00:00Z", "lock_w2"),
        ("2024-09-19T12:00:00Z", "lock_w3"),
    ]
    for occurred_at, ext_id in locks:
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "test", ext_id, "TRANSACTION_LOCK_ALL_PLAYERS",
             occurred_at, "2024-09-01T00:00:00Z", "{}"),
        )

    # Insert canonical events for locks
    for i, (occurred_at, ext_id) in enumerate(locks, 1):
        me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", (ext_id,)).fetchone()[0]
        con.execute(
            """INSERT INTO canonical_events
               (league_id, season, event_type, action_fingerprint, best_memory_event_id, best_score,
                selection_version, updated_at, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "TRANSACTION_LOCK_ALL_PLAYERS", f"lock_fp_{i}",
             me_id, 100, 1, "2024-09-01T00:00:00Z", occurred_at),
        )

    # Insert some transaction events between week 1 and week 2 locks
    txn_events = [
        ("2024-09-06T10:00:00Z", "txn_trade_1", "TRANSACTION_TRADE"),
        ("2024-09-07T10:00:00Z", "txn_waiver_1", "WAIVER_BID_AWARDED"),
        ("2024-09-08T10:00:00Z", "txn_fa_1", "TRANSACTION_FREE_AGENT"),
    ]
    for occurred_at, ext_id, event_type in txn_events:
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "test", ext_id, event_type,
             occurred_at, "2024-09-01T00:00:00Z", '{"test": true}'),
        )
        me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", (ext_id,)).fetchone()[0]
        con.execute(
            """INSERT INTO canonical_events
               (league_id, season, event_type, action_fingerprint, best_memory_event_id, best_score,
                selection_version, updated_at, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, event_type, f"fp_{ext_id}",
             me_id, 100, 1, "2024-09-01T00:00:00Z", occurred_at),
        )

    con.commit()
    con.close()
    return db


# ── _parse_iso_z / _to_iso_z ────────────────────────────────────────

class TestIsoTimestampHelpers:
    def test_parse_z_suffix(self):
        dt = _parse_iso_z("2024-09-05T12:00:00Z")
        assert dt.year == 2024
        assert dt.month == 9
        assert dt.hour == 12

    def test_parse_offset_suffix(self):
        dt = _parse_iso_z("2024-09-05T12:00:00+00:00")
        assert dt.year == 2024

    def test_roundtrip(self):
        original = "2024-09-05T12:00:00Z"
        dt = _parse_iso_z(original)
        result = _to_iso_z(dt)
        assert result == original

    def test_to_iso_z_format(self):
        dt = _parse_iso_z("2024-01-01T00:00:00Z")
        assert _to_iso_z(dt).endswith("Z")
        assert "+00:00" not in _to_iso_z(dt)


# ── window_for_week_index ────────────────────────────────────────────

class TestWindowForWeekIndex:
    def test_lock_to_lock_week_1(self, db_path):
        """Week 1 window is lock_1 → lock_2."""
        w = window_for_week_index(db_path, LEAGUE, SEASON, 1)
        assert w.mode == "LOCK_TO_LOCK"
        assert w.window_start == "2024-09-05T12:00:00Z"
        assert w.window_end == "2024-09-12T12:00:00Z"

    def test_lock_to_lock_week_2(self, db_path):
        """Week 2 window is lock_2 → lock_3."""
        w = window_for_week_index(db_path, LEAGUE, SEASON, 2)
        assert w.mode == "LOCK_TO_LOCK"
        assert w.window_start == "2024-09-12T12:00:00Z"
        assert w.window_end == "2024-09-19T12:00:00Z"

    def test_last_week_with_season_end(self, db_path):
        """Last week falls back to LOCK_TO_SEASON_END when season_end provided."""
        w = window_for_week_index(
            db_path, LEAGUE, SEASON, 3,
            season_end="2024-12-31T23:59:59Z",
        )
        assert w.mode == "LOCK_TO_SEASON_END"
        assert w.window_start == "2024-09-19T12:00:00Z"
        assert w.window_end == "2024-12-31T23:59:59Z"

    def test_last_week_without_season_end(self, db_path):
        """Last week falls back to LOCK_PLUS_7D_CAP without season_end."""
        w = window_for_week_index(db_path, LEAGUE, SEASON, 3)
        assert w.mode == "LOCK_PLUS_7D_CAP"
        assert w.window_start == "2024-09-19T12:00:00Z"

    def test_week_beyond_locks_is_unsafe(self, db_path):
        """Week index beyond available locks returns UNSAFE."""
        w = window_for_week_index(db_path, LEAGUE, SEASON, 10)
        assert w.mode == "UNSAFE"
        assert w.reason == WINDOW_MISSING_LOCKS

    def test_zero_week_is_unsafe(self, db_path):
        """Week index 0 returns UNSAFE."""
        w = window_for_week_index(db_path, LEAGUE, SEASON, 0)
        assert w.mode == "UNSAFE"
        assert w.reason == WINDOW_UNSAFE_TO_COMPUTE

    def test_negative_week_is_unsafe(self, db_path):
        """Negative week index returns UNSAFE."""
        w = window_for_week_index(db_path, LEAGUE, SEASON, -1)
        assert w.mode == "UNSAFE"


# ── _fingerprint_from_ids ────────────────────────────────────────────

class TestFingerprintFromIds:
    def test_deterministic(self):
        ids = ["fp_1", "fp_2", "fp_3"]
        assert _fingerprint_from_ids(ids) == _fingerprint_from_ids(ids)

    def test_order_matters(self):
        assert _fingerprint_from_ids(["a", "b"]) != _fingerprint_from_ids(["b", "a"])

    def test_empty_ids(self):
        fp = _fingerprint_from_ids([])
        assert len(fp) == 64  # valid sha256

    def test_matches_sha256(self):
        ids = ["id_1", "id_2"]
        expected = hashlib.sha256(",".join(ids).encode("utf-8")).hexdigest()
        assert _fingerprint_from_ids(ids) == expected


# ── select_weekly_recap_events_v1 ────────────────────────────────────

class TestSelectWeeklyRecapEvents:
    def test_selects_events_in_window(self, db_path):
        """Events between lock_1 and lock_2 are selected for week 1."""
        result = select_weekly_recap_events_v1(
            db_path, LEAGUE, SEASON, 1,
            allowlist_event_types=[
                "TRANSACTION_TRADE", "WAIVER_BID_AWARDED", "TRANSACTION_FREE_AGENT",
            ],
        )
        assert isinstance(result, SelectionResult)
        assert result.week_index == 1
        assert len(result.canonical_ids) == 3
        assert result.counts_by_type["TRANSACTION_TRADE"] == 1
        assert result.counts_by_type["WAIVER_BID_AWARDED"] == 1
        assert result.counts_by_type["TRANSACTION_FREE_AGENT"] == 1
        assert len(result.fingerprint) == 64

    def test_empty_allowlist_returns_empty(self, db_path):
        """Empty allowlist returns empty selection."""
        result = select_weekly_recap_events_v1(
            db_path, LEAGUE, SEASON, 1,
            allowlist_event_types=[],
        )
        assert result.canonical_ids == []

    def test_unsafe_window_returns_empty(self, db_path):
        """Week beyond locks returns empty selection."""
        result = select_weekly_recap_events_v1(
            db_path, LEAGUE, SEASON, 10,
        )
        assert result.canonical_ids == []
        assert result.window.mode == "UNSAFE"

    def test_fingerprint_is_deterministic(self, db_path):
        """Same inputs produce same fingerprint."""
        r1 = select_weekly_recap_events_v1(
            db_path, LEAGUE, SEASON, 1,
            allowlist_event_types=["TRANSACTION_TRADE", "WAIVER_BID_AWARDED"],
        )
        r2 = select_weekly_recap_events_v1(
            db_path, LEAGUE, SEASON, 1,
            allowlist_event_types=["TRANSACTION_TRADE", "WAIVER_BID_AWARDED"],
        )
        assert r1.fingerprint == r2.fingerprint
        assert r1.canonical_ids == r2.canonical_ids

    def test_week_2_has_no_events(self, db_path):
        """Week 2 window (lock_2 → lock_3) has no seeded events."""
        result = select_weekly_recap_events_v1(
            db_path, LEAGUE, SEASON, 2,
            allowlist_event_types=["TRANSACTION_TRADE"],
        )
        assert result.canonical_ids == []

    def test_selection_result_frozen(self, db_path):
        """SelectionResult is frozen."""
        result = select_weekly_recap_events_v1(db_path, LEAGUE, SEASON, 1)
        with pytest.raises(AttributeError):
            result.week_index = 999
