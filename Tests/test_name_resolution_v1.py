"""Phase 9 — Name Resolution in Rendered Recaps.

Verifies that _render_text_from_recap_runs produces human-readable
event bullets with franchise names and player names resolved from
franchise_directory and player_directory.
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
from squadvault.recaps.weekly_recap_lifecycle import (
    _render_text_from_recap_runs,
    _load_canonical_event_rows,
    _collect_ids_from_payloads,
    generate_weekly_recap_draft,
)

LEAGUE = "name_resolution_test"
SEASON = 2024


def _lock(week, ts):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "nr_test", "external_id": f"nr_lock_w{week}",
        "event_type": "TRANSACTION_LOCK_ALL_PLAYERS",
        "occurred_at": ts,
        "payload": {"type": "LOCK_ALL_PLAYERS", "week": week},
    }


def _waiver(franchise, player, bid, ts, uid):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "nr_test", "external_id": f"nr_{uid}",
        "event_type": "WAIVER_BID_AWARDED",
        "occurred_at": ts,
        "payload": {"franchise_id": franchise, "player_id": player, "bid_amount": bid},
    }


def _trade(from_f, to_f, player, ts, uid):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "nr_test", "external_id": f"nr_{uid}",
        "event_type": "TRANSACTION_TRADE",
        "occurred_at": ts,
        "payload": {
            "from_franchise_id": from_f, "to_franchise_id": to_f,
            "player_id": player,
        },
    }


def _fa(franchise, added, dropped, ts, uid):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "nr_test", "external_id": f"nr_{uid}",
        "event_type": "TRANSACTION_FREE_AGENT",
        "occurred_at": ts,
        "payload": {
            "franchise_id": franchise,
            "players_added_ids": [added],
            "players_dropped_ids": [dropped],
        },
    }


@pytest.fixture
def nr_db(tmp_path):
    """Fresh DB with events AND populated directory tables."""
    db_path = str(tmp_path / "name_res.sqlite")
    init_and_migrate(db_path)
    store = SQLiteStore(db_path=Path(db_path))

    events = [
        _lock(1, "2024-09-05T12:00:00Z"),
        _lock(2, "2024-09-12T12:00:00Z"),
        _waiver("F01", "P100", "25", "2024-09-06T10:00:00Z", "waiver1"),
        _waiver("F02", "P200", "15", "2024-09-07T10:00:00Z", "waiver2"),
        _trade("F01", "F03", "P300", "2024-09-08T10:00:00Z", "trade1"),
        _fa("F02", "P400", "P500", "2024-09-09T10:00:00Z", "fa1"),
    ]
    store.append_events(events)

    con = sqlite3.connect(db_path)
    for fid, name in [("F01", "Touchdown Terrors"), ("F02", "Blitz Brigade"), ("F03", "End Zone Elite")]:
        con.execute(
            "INSERT OR REPLACE INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
            (LEAGUE, SEASON, fid, name),
        )
    for pid, name, pos, team in [
        ("P100", "Joe Burrow", "QB", "CIN"),
        ("P200", "Ja'Marr Chase", "WR", "CIN"),
        ("P300", "Derrick Henry", "RB", "BAL"),
        ("P400", "Puka Nacua", "WR", "LAR"),
        ("P500", "Geno Smith", "QB", "SEA"),
    ]:
        con.execute(
            "INSERT OR REPLACE INTO player_directory (league_id, season, player_id, name, position, team) VALUES (?,?,?,?,?,?)",
            (LEAGUE, SEASON, pid, name, pos, team),
        )
    con.commit()
    con.close()

    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)

    sel = select_weekly_recap_events_v1(
        db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1,
    )
    upsert_recap_run(db_path, RecapRunRecord(
        league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
        window_mode=sel.window.mode,
        window_start=sel.window.window_start,
        window_end=sel.window.window_end,
        selection_fingerprint=sel.fingerprint,
        canonical_ids=[str(c) for c in sel.canonical_ids],
        counts_by_type=sel.counts_by_type,
    ))

    return db_path


class TestNameResolution:
    def test_rendered_text_contains_team_names(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert text is not None
        assert "Touchdown Terrors" in text
        assert "Blitz Brigade" in text
        assert "End Zone Elite" in text

    def test_rendered_text_contains_player_names(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert text is not None
        assert "Joe Burrow" in text
        assert "Derrick Henry" in text

    def test_bullets_section_present(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert text is not None
        assert "What happened this week" in text

    def test_waiver_bullet_format(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert "won" in text
        assert "on waivers" in text

    def test_trade_bullet_format(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert "acquired" in text

    def test_free_agent_bullet_format(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert "free agent" in text

    def test_draft_still_contains_summary(self, nr_db):
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert "SquadVault Weekly Recap" in text
        assert "Events selected:" in text
        assert "Selection fingerprint:" in text

    def test_unresolved_ids_pass_through(self, nr_db):
        """IDs not in directory tables pass through as raw IDs."""
        con = sqlite3.connect(nr_db)
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id,
                event_type, occurred_at, ingested_at, payload_json)
               VALUES (?,?,?,?,?,?,?,?)""",
            (LEAGUE, SEASON, "nr_test", "nr_unknown_player",
             "WAIVER_BID_AWARDED", "2024-09-10T10:00:00Z",
             "2024-09-10T10:00:00Z",
             json.dumps({"franchise_id": "F01", "player_id": "P999", "bid_amount": "5"})),
        )
        con.commit()
        con.close()

        canonicalize(league_id=LEAGUE, season=SEASON, db_path=nr_db)
        sel = select_weekly_recap_events_v1(
            db_path=nr_db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(nr_db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode, window_start=sel.window.window_start,
            window_end=sel.window.window_end, selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids], counts_by_type=sel.counts_by_type,
        ))
        text = _render_text_from_recap_runs(nr_db, LEAGUE, SEASON, 1)
        assert "P999" in text
        assert "Joe Burrow" in text

    def test_generate_draft_includes_names(self, nr_db):
        result = generate_weekly_recap_draft(
            db_path=nr_db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="name_resolution_test",
        )
        con = sqlite3.connect(nr_db)
        row = con.execute(
            "SELECT rendered_text FROM recap_artifacts WHERE version=?",
            (result.version,),
        ).fetchone()
        con.close()
        text = row[0]
        assert "Touchdown Terrors" in text
        assert "Joe Burrow" in text
        assert "What happened this week" in text


class TestNameResolutionHelpers:
    def test_load_canonical_event_rows(self, nr_db):
        con = sqlite3.connect(nr_db)
        fps = [str(r[0]) for r in con.execute(
            "SELECT action_fingerprint FROM canonical_events WHERE league_id=? AND season=? LIMIT 5",
            (LEAGUE, SEASON),
        ).fetchall()]
        con.close()
        rows = _load_canonical_event_rows(nr_db, fps)
        assert len(rows) > 0
        assert all(isinstance(r.payload, dict) for r in rows)

    def test_load_empty_ids(self, nr_db):
        assert _load_canonical_event_rows(nr_db, []) == []

    def test_collect_ids_from_payloads(self, nr_db):
        con = sqlite3.connect(nr_db)
        fps = [str(r[0]) for r in con.execute(
            "SELECT action_fingerprint FROM canonical_events WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchall()]
        con.close()
        rows = _load_canonical_event_rows(nr_db, fps)
        player_ids, franchise_ids = _collect_ids_from_payloads(rows)
        assert len(player_ids) > 0
        assert len(franchise_ids) > 0
        assert "P100" in player_ids
        assert "F01" in franchise_ids
