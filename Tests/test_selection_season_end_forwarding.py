"""Test that select_weekly_recap_events_v1 forwards season_end to window_for_week_index.

This validates the fix for the kwarg mismatch that caused
recap_week_gating_check.py and recap_week_selection_check.py to crash.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.selection.weekly_selection_v1 import (
    select_weekly_recap_events_v1,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


@pytest.fixture
def db_with_two_locks(tmp_path):
    """DB with exactly two lock events — week 1 has a window, week 2 needs season_end."""
    db = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text())

    locks = [
        ("2024-09-05T12:00:00Z", "lock_w1"),
        ("2024-09-12T12:00:00Z", "lock_w2"),
    ]
    for occurred_at, ext_id in locks:
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "test", ext_id, "TRANSACTION_LOCK_ALL_PLAYERS",
             occurred_at, "2024-09-01T00:00:00Z", "{}"),
        )

    for i, (occurred_at, ext_id) in enumerate(locks, 1):
        me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", (ext_id,)).fetchone()[0]
        con.execute(
            """INSERT INTO canonical_events
               (league_id, season, event_type, action_fingerprint, best_memory_event_id,
                best_score, selection_version, updated_at, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "TRANSACTION_LOCK_ALL_PLAYERS", ext_id, me_id,
             100, 1, "2024-09-01T00:00:00Z", occurred_at),
        )

    # Add a recap-eligible event between lock_w2 and the season_end cap
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (LEAGUE, SEASON, "test", "trade_after_lock2", "TRANSACTION_TRADE",
         "2024-09-15T08:00:00Z", "2024-09-01T00:00:00Z", "{}"),
    )
    me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", ("trade_after_lock2",)).fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint, best_memory_event_id,
            best_score, selection_version, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (LEAGUE, SEASON, "TRANSACTION_TRADE", "trade_after_lock2", me_id,
         100, 1, "2024-09-01T00:00:00Z", "2024-09-15T08:00:00Z"),
    )

    con.commit()
    con.close()
    return db


class TestSeasonEndForwarding:
    """select_weekly_recap_events_v1 must forward season_end to window_for_week_index."""

    def test_season_end_kwarg_accepted(self, db_with_two_locks):
        """Function accepts season_end without TypeError."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 1,
            season_end="2024-09-19T12:00:00Z",
        )
        assert result is not None

    def test_week2_without_season_end_uses_7d_cap(self, db_with_two_locks):
        """Week 2 has no third lock — without season_end, falls back to LOCK_PLUS_7D_CAP."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
        )
        # LOCK_PLUS_7D_CAP is a safe mode, so the trade is found
        assert result.window.mode == "LOCK_PLUS_7D_CAP"
        assert len(result.canonical_ids) == 1

    def test_week2_with_season_end_returns_events(self, db_with_two_locks):
        """Week 2 with season_end cap should produce a valid window and find the trade event."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
            season_end="2024-09-19T12:00:00Z",
        )
        assert len(result.canonical_ids) == 1
        assert "trade_after_lock2" in result.canonical_ids
        assert result.window.mode == "LOCK_TO_SEASON_END"

    def test_season_end_combined_with_allowlist(self, db_with_two_locks):
        """season_end + allowlist_event_types both work together."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
            season_end="2024-09-19T12:00:00Z",
            allowlist_event_types=["TRANSACTION_TRADE"],
        )
        assert len(result.canonical_ids) == 1

        # With an allowlist that excludes TRANSACTION_TRADE
        result2 = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
            season_end="2024-09-19T12:00:00Z",
            allowlist_event_types=["TRANSACTION_FREE_AGENT"],
        )
        assert result2.canonical_ids == []
