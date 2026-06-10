"""Tests for D-W1 Option B: week-field matchup selection fallback.

Historical seasons have un-timestamped (occurred_at NULL) matchup events the
lock-derived window cannot reach; they are selected by payload_json.week. The
fallback is gated per season so any season with timestamped matchups (e.g.
2024-2025) keeps pure timestamp-window behavior and stays byte-identical.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.selection.weekly_selection_v1 import (
    select_weekly_recap_events_v1,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "wf_league"


def _conn(db: str) -> sqlite3.Connection:
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text())
    return con


def _add_matchup(con, season, week, fp, occurred_at):
    """Insert a WEEKLY_MATCHUP_RESULT carrying payload.week; occurred_at may be None."""
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
           VALUES (?,?,?,?,?,?,?,?)""",
        (LEAGUE, season, "test", f"me_{fp}", "WEEKLY_MATCHUP_RESULT", occurred_at,
         "2020-01-01T00:00:00Z", f'{{"week": {week}, "home_franchise_id": "0001"}}'),
    )
    me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", (f"me_{fp}",)).fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint, best_memory_event_id, best_score,
            selection_version, updated_at, occurred_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (LEAGUE, season, "WEEKLY_MATCHUP_RESULT", fp, me_id, 100, 1, "2020-01-01T00:00:00Z", occurred_at),
    )


def _add_lock(con, season, fp, occurred_at):
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
           VALUES (?,?,?,?,?,?,?,?)""",
        (LEAGUE, season, "test", f"me_{fp}", "TRANSACTION_LOCK_ALL_PLAYERS", occurred_at, "x", "{}"),
    )
    me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", (f"me_{fp}",)).fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint, best_memory_event_id, best_score,
            selection_version, updated_at, occurred_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (LEAGUE, season, "TRANSACTION_LOCK_ALL_PLAYERS", fp, me_id, 100, 1, "x", occurred_at),
    )


class TestHistoricalWeekFieldFallback:
    """Season with NO timestamped matchups: select by payload.week."""

    def test_untimestamped_matchups_selected_by_week(self, tmp_path):
        db = str(tmp_path / "hist.sqlite")
        con = _conn(db)
        # No locks at all (the 2010-2016 shape). Matchups carry week, occurred_at NULL.
        _add_matchup(con, 2015, 5, "m_w5_a", None)
        _add_matchup(con, 2015, 5, "m_w5_b", None)
        _add_matchup(con, 2015, 12, "m_w12_a", None)
        con.commit(); con.close()

        sel5 = select_weekly_recap_events_v1(db_path=db, league_id=LEAGUE, season=2015, week_index=5)
        assert sel5.counts_by_type.get("WEEKLY_MATCHUP_RESULT") == 2
        assert set(sel5.canonical_ids) == {"m_w5_a", "m_w5_b"}
        # Week isolation: week 12 not in week 5's selection.
        assert "m_w12_a" not in sel5.canonical_ids
        sel12 = select_weekly_recap_events_v1(db_path=db, league_id=LEAGUE, season=2015, week_index=12)
        assert set(sel12.canonical_ids) == {"m_w12_a"}

    def test_deterministic_ordering(self, tmp_path):
        db = str(tmp_path / "hist2.sqlite")
        con = _conn(db)
        _add_matchup(con, 2015, 5, "zzz", None)
        _add_matchup(con, 2015, 5, "aaa", None)
        con.commit(); con.close()
        sel = select_weekly_recap_events_v1(db_path=db, league_id=LEAGUE, season=2015, week_index=5)
        # NULL occurred_at -> "" -> ordered by action_fingerprint ascending.
        assert sel.canonical_ids == ["aaa", "zzz"]


class TestTimestampedSeasonUntouched:
    """Season WITH timestamped matchups: week-field gated off; byte-identical."""

    def test_stray_untimestamped_matchup_not_added(self, tmp_path):
        db = str(tmp_path / "work.sqlite")
        con = _conn(db)
        # Locks define windows for weeks 1 and 2.
        _add_lock(con, 2024, "lock1", "2024-09-05T17:00:00Z")
        _add_lock(con, 2024, "lock2", "2024-09-12T17:00:00Z")
        _add_lock(con, 2024, "lock3", "2024-09-19T17:00:00Z")
        # Week-1 matchup timestamped inside [lock1, lock2).
        _add_matchup(con, 2024, 1, "m_ts", "2024-09-05T17:00:00Z")
        # A stray un-timestamped matchup (the 2024-W18 quirk shape) for week 1.
        _add_matchup(con, 2024, 1, "m_null_stray", None)
        con.commit(); con.close()

        sel = select_weekly_recap_events_v1(db_path=db, league_id=LEAGUE, season=2024, week_index=1)
        # Season has a timestamped matchup -> week-field fallback is OFF.
        assert "m_ts" in sel.canonical_ids
        assert "m_null_stray" not in sel.canonical_ids
        assert sel.counts_by_type.get("WEEKLY_MATCHUP_RESULT") == 1
