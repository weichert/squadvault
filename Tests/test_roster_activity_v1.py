"""Tests for verified roster activity stats.

Verifies that:
- derive_roster_activity correctly counts per-franchise moves
- render_writer_room_context_for_prompt includes roster activity
- System prompt references WRITER ROOM for stats verification
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_event(con, league_id, season, event_type, payload, occurred_at="2024-10-01T12:00:00Z"):
    """Insert a memory event and corresponding canonical event."""
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", f"e_{event_type}_{payload.get('franchise_id','x')}_{con.execute('SELECT COUNT(*) FROM memory_events').fetchone()[0]}",
         event_type, occurred_at, occurred_at, json.dumps(payload)),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    fp = f"{event_type}:{league_id}:{season}:{me_id}"
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, event_type, fp, me_id, 100, occurred_at, occurred_at),
    )


class TestDeriveRosterActivity:
    """derive_roster_activity should count moves correctly."""

    def test_counts_all_event_types(self, tmp_path):
        """Should count waiver wins, FA adds, and trades separately."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        # 3 waiver wins for franchise 0001
        for i in range(3):
            _insert_event(con, "L1", 2024, "WAIVER_BID_AWARDED",
                         {"franchise_id": "0001", "bid_amount": 10, "player_id": f"p{i}"})
        # 5 FA adds for franchise 0001
        for i in range(5):
            _insert_event(con, "L1", 2024, "TRANSACTION_FREE_AGENT",
                         {"franchise_id": "0001", "players_added_ids": f"p{i+10}"})
        # 1 trade for franchise 0001
        _insert_event(con, "L1", 2024, "TRANSACTION_TRADE",
                     {"franchise_id": "0001"})

        # 2 FA adds for franchise 0002
        for i in range(2):
            _insert_event(con, "L1", 2024, "TRANSACTION_FREE_AGENT",
                         {"franchise_id": "0002", "players_added_ids": f"p{i+20}"})

        con.commit()
        con.close()

        from squadvault.core.recaps.context.writer_room_context_v1 import derive_roster_activity
        activity = derive_roster_activity(db_path=db_path, league_id="L1", season=2024)

        # Should have 2 franchises
        by_fid = {r.franchise_id: r for r in activity}
        assert "0001" in by_fid
        assert "0002" in by_fid

        # Franchise 0001: 3 waivers + 5 FA + 1 trade = 9 total
        assert by_fid["0001"].waiver_wins == 3
        assert by_fid["0001"].free_agent_adds == 5
        assert by_fid["0001"].trades == 1
        assert by_fid["0001"].total_moves == 9

        # Franchise 0002: 2 FA = 2 total
        assert by_fid["0002"].free_agent_adds == 2
        assert by_fid["0002"].total_moves == 2

    def test_sorted_by_total_desc(self, tmp_path):
        """Results should be sorted by total_moves descending."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        for i in range(5):
            _insert_event(con, "L1", 2024, "TRANSACTION_FREE_AGENT",
                         {"franchise_id": "0001"})
        for i in range(10):
            _insert_event(con, "L1", 2024, "TRANSACTION_FREE_AGENT",
                         {"franchise_id": "0002"})

        con.commit()
        con.close()

        from squadvault.core.recaps.context.writer_room_context_v1 import derive_roster_activity
        activity = derive_roster_activity(db_path=db_path, league_id="L1", season=2024)

        assert activity[0].franchise_id == "0002"  # 10 moves
        assert activity[1].franchise_id == "0001"  # 5 moves


class TestRenderIncludesRosterActivity:
    """Prompt rendering should include roster activity counts."""

    def test_roster_section_in_output(self):
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            RosterActivity, render_writer_room_context_for_prompt,
        )
        activity = (
            RosterActivity("0001", waiver_wins=5, free_agent_adds=10, trades=2, total_moves=17),
            RosterActivity("0002", waiver_wins=3, free_agent_adds=4, trades=0, total_moves=7),
        )
        result = render_writer_room_context_for_prompt(
            deltas=(), faab=(), roster_activity=activity,
            name_map={"0001": "Team Alpha", "0002": "Team Beta"},
        )
        assert "Team Alpha: 17 total moves" in result
        assert "Team Beta: 7 total moves" in result
        assert "verified counts" in result.lower()


class TestStatsGuardrail:
    """System prompt should reference WRITER ROOM for stats."""

    def test_guardrail_present(self):
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "WRITER ROOM" in _SYSTEM_PROMPT
