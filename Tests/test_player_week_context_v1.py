"""Tests for squadvault.core.recaps.context.player_week_context_v1.

Covers: data classes, _build_franchise_context, _build_faab_lookup,
derive_player_week_context_v1 (via DB fixture), render_player_highlights_for_prompt.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.context.player_week_context_v1 import (
    PlayerScore,
    FaabPickup,
    FranchiseWeekContext,
    PlayerWeekContextV1,
    _build_franchise_context,
    _build_faab_lookup,
    _empty_context,
    derive_player_week_context_v1,
    render_player_highlights_for_prompt,
)

SCHEMA_PATH = Path(__file__).resolve().parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
if not SCHEMA_PATH.exists():
    # Handle running from repo root
    SCHEMA_PATH = Path("src/squadvault/core/storage/schema.sql")


# ── Helpers ──────────────────────────────────────────────────────────

def _make_payload(franchise_id, player_id, score, is_starter=True, should_start=False, week=6):
    """Build a WEEKLY_PLAYER_SCORE payload dict."""
    return {
        "week": week,
        "franchise_id": franchise_id,
        "player_id": player_id,
        "score": score,
        "is_starter": is_starter,
        "should_start": should_start,
    }


# ── _empty_context ───────────────────────────────────────────────────

class TestEmptyContext:
    def test_returns_empty(self):
        ctx = _empty_context("70985", 2024, 6)
        assert ctx.league_id == "70985"
        assert ctx.season == 2024
        assert ctx.week == 6
        assert ctx.has_data is False
        assert ctx.franchises == ()
        assert ctx.week_top_scorer is None
        assert ctx.week_lowest_starter is None


# ── _build_franchise_context ─────────────────────────────────────────

class TestBuildFranchiseContext:
    def test_basic_starters(self):
        payloads = [
            _make_payload("0001", "15648", 40.20, is_starter=True),
            _make_payload("0001", "12345", 12.50, is_starter=True),
        ]
        ctx = _build_franchise_context("0001", payloads, {})
        assert ctx.franchise_id == "0001"
        assert len(ctx.starters) == 2
        assert len(ctx.bench) == 0
        assert ctx.top_starter.player_id == "15648"
        assert ctx.bust_starter.player_id == "12345"
        assert ctx.starter_total == 52.70

    def test_starters_and_bench(self):
        payloads = [
            _make_payload("0001", "15648", 40.20, is_starter=True),
            _make_payload("0001", "12345", 15.00, is_starter=False),
        ]
        ctx = _build_franchise_context("0001", payloads, {})
        assert len(ctx.starters) == 1
        assert len(ctx.bench) == 1
        assert ctx.bench_total == 15.00
        assert ctx.best_bench_player.player_id == "12345"

    def test_bench_should_start_points(self):
        payloads = [
            _make_payload("0001", "15648", 10.00, is_starter=True, should_start=False),
            _make_payload("0001", "12345", 25.00, is_starter=False, should_start=True),
        ]
        ctx = _build_franchise_context("0001", payloads, {})
        assert ctx.bench_points_over_starters == 25.00

    def test_starters_sorted_by_score_desc(self):
        payloads = [
            _make_payload("0001", "11111", 10.00),
            _make_payload("0001", "22222", 30.00),
            _make_payload("0001", "33333", 20.00),
        ]
        ctx = _build_franchise_context("0001", payloads, {})
        assert ctx.starters[0].player_id == "22222"
        assert ctx.starters[1].player_id == "33333"
        assert ctx.starters[2].player_id == "11111"

    def test_single_starter_is_both_top_and_bust(self):
        payloads = [
            _make_payload("0001", "15648", 40.20),
        ]
        ctx = _build_franchise_context("0001", payloads, {})
        assert ctx.top_starter.player_id == "15648"
        assert ctx.bust_starter.player_id == "15648"

    def test_no_players_returns_empty(self):
        ctx = _build_franchise_context("0001", [], {})
        assert ctx.starters == ()
        assert ctx.bench == ()
        assert ctx.top_starter is None
        assert ctx.bust_starter is None
        assert ctx.starter_total == 0.0

    def test_faab_linkage(self):
        payloads = [
            _make_payload("0001", "15648", 22.50, is_starter=True),
        ]
        faab_lookup = {
            "15648": [
                FaabPickup(
                    player_id="15648",
                    franchise_id="0001",
                    bid_amount=33.0,
                    acquisition_week=0,
                ),
            ],
        }
        ctx = _build_franchise_context("0001", payloads, faab_lookup)
        assert len(ctx.faab_performers) == 1
        ps, pickup = ctx.faab_performers[0]
        assert ps.player_id == "15648"
        assert pickup.bid_amount == 33.0

    def test_faab_wrong_franchise_not_linked(self):
        """FAAB pickup for a different franchise should not link."""
        payloads = [
            _make_payload("0001", "15648", 22.50),
        ]
        faab_lookup = {
            "15648": [
                FaabPickup(
                    player_id="15648",
                    franchise_id="0002",  # different franchise
                    bid_amount=33.0,
                    acquisition_week=0,
                ),
            ],
        }
        ctx = _build_franchise_context("0001", payloads, faab_lookup)
        assert len(ctx.faab_performers) == 0

    def test_score_tiebreak_by_player_id(self):
        """When two players have the same score, sort by player_id for determinism."""
        payloads = [
            _make_payload("0001", "22222", 20.00),
            _make_payload("0001", "11111", 20.00),
        ]
        ctx = _build_franchise_context("0001", payloads, {})
        assert ctx.starters[0].player_id == "11111"
        assert ctx.starters[1].player_id == "22222"


# ── _build_faab_lookup ───────────────────────────────────────────────

class TestBuildFaabLookup:
    def test_basic_lookup(self):
        faab_payloads = [
            {"player_id": "15648", "franchise_id": "0001", "bid_amount": "33"},
        ]
        lookup = _build_faab_lookup(faab_payloads)
        assert "15648" in lookup
        assert lookup["15648"][0].bid_amount == 33.0

    def test_players_added_ids_fallback(self):
        faab_payloads = [
            {"players_added_ids": "15648,99999", "franchise_id": "0001", "bid_amount": "25"},
        ]
        lookup = _build_faab_lookup(faab_payloads)
        assert "15648" in lookup

    def test_zero_bid_skipped(self):
        faab_payloads = [
            {"player_id": "15648", "franchise_id": "0001", "bid_amount": "0"},
        ]
        lookup = _build_faab_lookup(faab_payloads)
        assert "15648" not in lookup

    def test_missing_bid_skipped(self):
        faab_payloads = [
            {"player_id": "15648", "franchise_id": "0001"},
        ]
        lookup = _build_faab_lookup(faab_payloads)
        assert "15648" not in lookup

    def test_missing_player_id_skipped(self):
        faab_payloads = [
            {"franchise_id": "0001", "bid_amount": "33"},
        ]
        lookup = _build_faab_lookup(faab_payloads)
        assert lookup == {}

    def test_empty_input(self):
        lookup = _build_faab_lookup([])
        assert lookup == {}


# ── render_player_highlights_for_prompt ──────────────────────────────

class TestRenderPlayerHighlights:
    def _make_context(self, **kwargs):
        """Build a PlayerWeekContextV1 with sensible defaults."""
        defaults = dict(
            league_id="70985",
            season=2024,
            week=6,
            franchises=(),
            week_top_scorer=None,
            week_lowest_starter=None,
            total_players=0,
            total_starters=0,
        )
        defaults.update(kwargs)
        return PlayerWeekContextV1(**defaults)

    def test_empty_context_returns_empty_string(self):
        ctx = _empty_context("70985", 2024, 6)
        result = render_player_highlights_for_prompt(ctx)
        assert result == ""

    def test_week_top_scorer_rendered(self):
        ctx = self._make_context(
            week_top_scorer=("0001", "15648", 40.20),
            total_players=1,
            total_starters=1,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "top scorer" in result
        assert "15648" in result
        assert "40.20" in result

    def test_team_resolver_applied(self):
        fc = FranchiseWeekContext(
            franchise_id="0001",
            starters=(PlayerScore("15648", 40.20, True, False),),
            bench=(),
            top_starter=PlayerScore("15648", 40.20, True, False),
            bust_starter=PlayerScore("15648", 40.20, True, False),
            starter_total=40.20,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=(),
        )
        ctx = self._make_context(
            franchises=(fc,),
            week_top_scorer=("0001", "15648", 40.20),
            total_players=1,
            total_starters=1,
        )

        def team_res(fid):
            return {"0001": "Paradis' Playmakers"}.get(fid, fid)

        def player_res(pid):
            return {"15648": "Jahmyr Gibbs"}.get(pid, pid)

        result = render_player_highlights_for_prompt(
            ctx, team_resolver=team_res, player_resolver=player_res,
        )
        assert "Paradis' Playmakers" in result
        assert "Jahmyr Gibbs" in result

    def test_bench_outscored_starter_shown(self):
        fc = FranchiseWeekContext(
            franchise_id="0001",
            starters=(
                PlayerScore("11111", 30.00, True, True),
                PlayerScore("22222", 5.00, True, False),
            ),
            bench=(
                PlayerScore("33333", 20.00, False, True),
            ),
            top_starter=PlayerScore("11111", 30.00, True, True),
            bust_starter=PlayerScore("22222", 5.00, True, False),
            starter_total=35.00,
            bench_total=20.00,
            bench_points_over_starters=20.00,
            best_bench_player=PlayerScore("33333", 20.00, False, True),
            faab_performers=(),
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=3,
            total_starters=2,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "Bench > starter" in result
        assert "33333" in result
        assert "22222" in result

    def test_faab_performer_shown(self):
        ps = PlayerScore("15648", 22.50, True, False)
        pickup = FaabPickup("15648", "0001", 33.0, 0)
        fc = FranchiseWeekContext(
            franchise_id="0001",
            starters=(ps,),
            bench=(),
            top_starter=ps,
            bust_starter=ps,
            starter_total=22.50,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=((ps, pickup),),
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=1,
            total_starters=1,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "FAAB pickup $33" in result
        assert "22.50" in result

    def test_optimal_lineup_points_shown(self):
        fc = FranchiseWeekContext(
            franchise_id="0001",
            starters=(PlayerScore("11111", 10.00, True, False),),
            bench=(PlayerScore("22222", 25.00, False, True),),
            top_starter=PlayerScore("11111", 10.00, True, False),
            bust_starter=PlayerScore("11111", 10.00, True, False),
            starter_total=10.00,
            bench_total=25.00,
            bench_points_over_starters=25.00,
            best_bench_player=PlayerScore("22222", 25.00, False, True),
            faab_performers=(),
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=2,
            total_starters=1,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "Optimal lineup points left on bench: 25.00" in result


# ── DB-backed integration test ───────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    """Create a test database with schema and sample player score events."""
    db_path = str(tmp_path / "test.sqlite")
    schema = SCHEMA_PATH.read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)

    # Insert WEEKLY_PLAYER_SCORE events into memory_events
    events = [
        # Franchise 0001 starters
        _make_payload("0001", "15648", 40.20, is_starter=True, should_start=True, week=6),
        _make_payload("0001", "12345", 12.50, is_starter=True, should_start=True, week=6),
        _make_payload("0001", "99999", 8.00, is_starter=True, should_start=False, week=6),
        # Franchise 0001 bench
        _make_payload("0001", "88888", 15.00, is_starter=False, should_start=True, week=6),
        # Franchise 0002 starters
        _make_payload("0002", "55555", 22.50, is_starter=True, should_start=True, week=6),
        _make_payload("0002", "66666", 3.10, is_starter=True, should_start=True, week=6),
    ]

    for i, payload in enumerate(events):
        fid = payload["franchise_id"]
        pid = payload["player_id"]
        ext_id = f"test_ext_{fid}_{pid}_w6"
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, event_type, external_source, external_id,
                payload_json, ingested_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
            ("70985", 2024, "WEEKLY_PLAYER_SCORE", "MFL", ext_id,
             json.dumps(payload)),
        )

    # Run canonicalization
    con.commit()
    con.close()

    from squadvault.core.canonicalize.run_canonicalize import canonicalize
    canonicalize(league_id="70985", season=2024, db_path=db_path)

    return db_path


class TestDerivePlayerWeekContextIntegration:
    def test_derives_from_db(self, db):
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        assert ctx.has_data is True
        assert len(ctx.franchises) == 2
        assert ctx.total_players == 6
        assert ctx.total_starters == 5

    def test_week_top_scorer(self, db):
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        assert ctx.week_top_scorer is not None
        fid, pid, score = ctx.week_top_scorer
        assert pid == "15648"
        assert score == 40.20

    def test_week_lowest_starter(self, db):
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        assert ctx.week_lowest_starter is not None
        fid, pid, score = ctx.week_lowest_starter
        assert pid == "66666"
        assert score == 3.10

    def test_franchise_context_details(self, db):
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        f0001 = [f for f in ctx.franchises if f.franchise_id == "0001"][0]
        assert len(f0001.starters) == 3
        assert len(f0001.bench) == 1
        assert f0001.top_starter.player_id == "15648"
        assert f0001.bust_starter.player_id == "99999"
        assert f0001.bench_points_over_starters == 15.00

    def test_deterministic(self, db):
        """Same inputs produce identical outputs."""
        ctx1 = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        ctx2 = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        assert ctx1 == ctx2

    def test_missing_week_returns_empty(self, db):
        """Week with no data returns empty context."""
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=99,
        )
        assert ctx.has_data is False

    def test_missing_league_returns_empty(self, db):
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="99999", season=2024, week=6,
        )
        assert ctx.has_data is False

    def test_render_integration(self, db):
        """Verify rendered output is non-empty and contains expected data."""
        ctx = derive_player_week_context_v1(
            db_path=db, league_id="70985", season=2024, week=6,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "top scorer" in result
        assert "40.20" in result
        assert "0001" in result
        assert "0002" in result
