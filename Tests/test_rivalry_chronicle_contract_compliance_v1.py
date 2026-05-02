"""Rivalry Chronicle v1 — Contract Compliance Tests.

Verifies the contract card requirements:
- Team pair filtering
- Canonical facts block from WEEKLY_MATCHUP_RESULT events
- Name resolution via franchise_directory
- Contract-compliant output structure
- Deterministic facts block hash
- Edge cases (no matchups, missing weeks, teams never played)
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.chronicle.generate_rivalry_chronicle_v1 import generate_rivalry_chronicle_v1
from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy
from squadvault.chronicle.matchup_facts_v1 import (
    facts_block_hash_v1,
    query_head_to_head_matchups_v1,
)
from squadvault.chronicle.persist_rivalry_chronicle_v1 import persist_rivalry_chronicle_v1
from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.recaps.recap_artifacts import (
    ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
)
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.storage.migrate import init_and_migrate
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)

LEAGUE = "70985"
LEAGUE_INT = 70985
SEASON = 2024
TEAM_A = "0001"
TEAM_B = "0005"
TEAM_C = "0003"


def _lock_event(week, ts):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "contract_test", "external_id": f"ct_lock_w{week}",
        "event_type": "TRANSACTION_LOCK_ALL_PLAYERS",
        "occurred_at": ts,
        "payload": {"type": "LOCK_ALL_PLAYERS", "week": week},
    }


def _matchup_event(week, winner_fid, loser_fid, winner_score, loser_score, ts, is_tie=False):
    sorted_ids = sorted([winner_fid, loser_fid])
    eid = f"ct_matchup_w{week}_{sorted_ids[0]}_{sorted_ids[1]}"
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "contract_test", "external_id": eid,
        "event_type": "WEEKLY_MATCHUP_RESULT",
        "occurred_at": ts,
        "payload": {
            "week": week,
            "winner_franchise_id": winner_fid,
            "loser_franchise_id": loser_fid,
            "winner_score": winner_score,
            "loser_score": loser_score,
            "is_tie": is_tie,
        },
    }


def _waiver_event(franchise, player, bid, ts, uid):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "contract_test", "external_id": f"ct_{uid}",
        "event_type": "WAIVER_BID_AWARDED",
        "occurred_at": ts,
        "payload": {"franchise_id": franchise, "player_id": player, "bid_amount": bid},
    }


def _insert_franchise(conn, league_id, season, franchise_id, name):
    """Insert a franchise directory entry for name resolution."""
    conn.execute(
        "INSERT OR REPLACE INTO franchise_directory (league_id, season, franchise_id, name) "
        "VALUES (?, ?, ?, ?)",
        (str(league_id), int(season), str(franchise_id), str(name)),
    )


@pytest.fixture
def contract_db(tmp_path):
    """Fresh DB with matchup events and approved weekly recaps for 3 weeks."""
    db_path = str(tmp_path / "contract.sqlite")
    init_and_migrate(db_path)
    store = SQLiteStore(db_path=Path(db_path))

    # Insert franchise directory entries for name resolution
    con = sqlite3.connect(db_path)
    _insert_franchise(con, LEAGUE, SEASON, "0001", "Alpha Dogs")
    _insert_franchise(con, LEAGUE, SEASON, "0003", "Charlie's Angels")
    _insert_franchise(con, LEAGUE, SEASON, "0005", "Echo Force")
    con.commit()
    con.close()

    events = [
        # Lock events for weeks 1-4
        _lock_event(1, "2024-09-05T12:00:00Z"),
        _lock_event(2, "2024-09-12T12:00:00Z"),
        _lock_event(3, "2024-09-19T12:00:00Z"),
        _lock_event(4, "2024-09-26T12:00:00Z"),

        # Matchup results: A vs B in weeks 1 and 3, A vs C in week 2
        _matchup_event(1, TEAM_A, TEAM_B, "142.30", "121.50", "2024-09-06T10:00:00Z"),
        _matchup_event(2, TEAM_C, TEAM_A, "130.00", "125.00", "2024-09-13T10:00:00Z"),
        _matchup_event(3, TEAM_B, TEAM_A, "155.20", "148.70", "2024-09-20T10:00:00Z"),

        # Waiver noise (for weekly recaps to have content)
        _waiver_event("0001", "P100", "25", "2024-09-06T11:00:00Z", "w1_waiver"),
        _waiver_event("0005", "P200", "15", "2024-09-13T11:00:00Z", "w2_waiver"),
        _waiver_event("0001", "P300", "30", "2024-09-20T11:00:00Z", "w3_waiver"),
    ]
    store.append_events(events)
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)

    # Generate and approve weekly recaps for weeks 1-3
    for week in [1, 2, 3]:
        sel = select_weekly_recap_events_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=week,
        )
        upsert_recap_run(db_path, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=week, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))
        generate_weekly_recap_draft(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            week_index=week, reason="contract_test_prereq",
        )
        approve_latest_weekly_recap(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            week_index=week, approved_by="test_founder",
        )

    return db_path


class TestMatchupFactsQuery:
    """Test query_head_to_head_matchups_v1 — canonical matchup extraction."""

    def test_filters_by_team_pair(self, contract_db):
        """Only matchups between team A and team B are returned."""
        facts = query_head_to_head_matchups_v1(
            db_path=contract_db,
            league_id=LEAGUE,
            season=SEASON,
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        assert len(facts) == 2  # weeks 1 and 3 only
        weeks = [f.week for f in facts]
        assert weeks == [1, 3]

    def test_team_pair_order_independent(self, contract_db):
        """query(A, B) == query(B, A) — sorted pair ensures determinism."""
        facts_ab = query_head_to_head_matchups_v1(
            db_path=contract_db, league_id=LEAGUE, season=SEASON,
            team_a_id=TEAM_A, team_b_id=TEAM_B,
        )
        facts_ba = query_head_to_head_matchups_v1(
            db_path=contract_db, league_id=LEAGUE, season=SEASON,
            team_a_id=TEAM_B, team_b_id=TEAM_A,
        )
        assert len(facts_ab) == len(facts_ba)
        for a, b in zip(facts_ab, facts_ba):
            assert a.week == b.week
            assert a.winner_franchise_id == b.winner_franchise_id
            assert a.canonical_event_fingerprint == b.canonical_event_fingerprint

    def test_week_filter(self, contract_db):
        """Week indices filter limits results."""
        facts = query_head_to_head_matchups_v1(
            db_path=contract_db, league_id=LEAGUE, season=SEASON,
            team_a_id=TEAM_A, team_b_id=TEAM_B,
            week_indices=[1],
        )
        assert len(facts) == 1
        assert facts[0].week == 1

    def test_name_resolution(self, contract_db):
        """Franchise names are resolved via franchise_directory."""
        facts = query_head_to_head_matchups_v1(
            db_path=contract_db, league_id=LEAGUE, season=SEASON,
            team_a_id=TEAM_A, team_b_id=TEAM_B,
        )
        assert facts[0].winner_name == "Alpha Dogs"
        assert facts[0].loser_name == "Echo Force"

    def test_no_matchups_returns_empty(self, contract_db):
        """Teams that never played each other return empty list."""
        facts = query_head_to_head_matchups_v1(
            db_path=contract_db, league_id=LEAGUE, season=SEASON,
            team_a_id=TEAM_B, team_b_id=TEAM_C,
        )
        assert facts == []

    def test_facts_block_hash_deterministic(self, contract_db):
        """Same facts produce same hash."""
        facts = query_head_to_head_matchups_v1(
            db_path=contract_db, league_id=LEAGUE, season=SEASON,
            team_a_id=TEAM_A, team_b_id=TEAM_B,
        )
        h1 = facts_block_hash_v1(facts)
        h2 = facts_block_hash_v1(facts)
        assert h1 == h2
        assert len(h1) == 64


class TestContractCompliantGeneration:
    """Test generate_rivalry_chronicle_v1 with team pair (contract path)."""

    def test_generates_with_team_pair(self, contract_db):
        """Generation with team args produces contract-compliant output."""
        result = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        assert result.text
        assert "Rivalry Chronicle v1" in result.text
        assert "Alpha Dogs" in result.text
        assert "Echo Force" in result.text
        assert "Head-to-Head Results" in result.text
        assert "Trace" in result.text
        assert "Disclosures" in result.text

    def test_facts_block_contains_matchup_results(self, contract_db):
        """Facts block lists each matchup with scores."""
        result = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        text = result.text
        # Week 1: A beat B
        assert "Week 1" in text
        assert "142.30" in text
        # Week 3: B beat A
        assert "Week 3" in text
        assert "155.20" in text
        # Week 2 (A vs C) should NOT appear in facts block
        assert "Week 2:" not in text.split("Head-to-Head")[1].split("Trace")[0]

    def test_trace_block_has_fingerprints(self, contract_db):
        """Trace block includes canonical event fingerprints and facts hash."""
        result = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        assert "facts_block_hash:" in result.text
        assert "canonical_event_fingerprints:" in result.text

    def test_disclosures_notes_non_matchup_weeks(self, contract_db):
        """Disclosures note weeks where teams didn't face each other."""
        result = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        # Week 2 is in scope but teams didn't play each other
        assert "did not face each other" in result.text

    def test_fingerprint_includes_team_pair(self, contract_db):
        """Different team pairs produce different fingerprints."""
        r1 = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        r2 = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_C,
        )
        assert r1.fingerprint != r2.fingerprint

    def test_deterministic_output(self, contract_db, monkeypatch):
        """Same inputs produce identical fingerprint and identical rendered
        text — given that the (non-deterministic) creative narrative layer
        is held constant.

        Architectural note: the Rivalry Chronicle fingerprint is derived
        purely from canonical facts and is therefore deterministic by
        construction. The rendered ``text`` field includes optional
        narrative prose drafted by an LLM at non-zero temperature, which is
        inherently non-deterministic. To test the deterministic *rendering*
        layer without coupling to LLM stochasticity, we patch the creative
        layer to return a constant. This validates that:

          1. Facts → fingerprint is deterministic.
          2. (Facts, narrative) → rendered text is deterministic.

        It does NOT (and cannot) assert that two real LLM calls produce
        byte-identical prose; that would be a false claim about the system.
        """
        from squadvault.ai import creative_layer_rivalry_v1 as _cl_rivalry

        monkeypatch.setattr(
            _cl_rivalry,
            "draft_rivalry_narrative_v1",
            lambda **_kwargs: "FIXED NARRATIVE FOR DETERMINISM TEST",
        )

        kwargs = dict(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        r1 = generate_rivalry_chronicle_v1(**kwargs)
        r2 = generate_rivalry_chronicle_v1(**kwargs)
        assert r1.fingerprint == r2.fingerprint
        assert r1.text == r2.text


class TestContractCompliantPersistence:
    """Persist with team pair — DRAFT governance, idempotency."""

    def test_persist_with_team_pair_produces_draft(self, contract_db):
        """persist_rivalry_chronicle_v1 with team pair creates DRAFT."""
        result = persist_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        assert result.created_new is True

        con = sqlite3.connect(contract_db)
        row = con.execute(
            "SELECT state, rendered_text FROM recap_artifacts WHERE artifact_type=? AND version=?",
            (ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1, result.version),
        ).fetchone()
        con.close()

        assert row[0] == "DRAFT"
        assert "Alpha Dogs" in row[1]
        assert "Echo Force" in row[1]

    def test_persist_idempotent_with_team_pair(self, contract_db):
        """Same team pair + inputs = no duplicate artifact."""
        kwargs = dict(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_A,
            team_b_id=TEAM_B,
        )
        r1 = persist_rivalry_chronicle_v1(**kwargs)
        r2 = persist_rivalry_chronicle_v1(**kwargs)
        assert r1.created_new is True
        assert r2.created_new is False
        assert r1.version == r2.version

    def test_no_matchups_still_generates(self, contract_db):
        """Teams that never played produce a facts-only artifact with empty facts block."""
        result = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
            team_a_id=TEAM_B,
            team_b_id=TEAM_C,
        )
        assert "No head-to-head matchups found" in result.text


class TestLegacyPathPreserved:
    """Legacy path (no team args) still works for backward compatibility."""

    def test_legacy_format_without_team_args(self, contract_db):
        """Without team args, legacy upstream-quotes format is used."""
        result = generate_rivalry_chronicle_v1(
            db_path=contract_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1,),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert "BEGIN_PROVENANCE" in result.text
        assert "BEGIN_UPSTREAM_QUOTES" in result.text
