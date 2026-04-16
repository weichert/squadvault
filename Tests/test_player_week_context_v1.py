"""Tests for squadvault.core.recaps.context.player_week_context_v1.

Covers: data classes, _build_franchise_context, _build_faab_lookup,
_build_faab_performer_timelines, _render_faab_timeline,
derive_player_week_context_v1 (via DB fixture), render_player_highlights_for_prompt.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.context.player_week_context_v1 import (
    FaabPerformerTimeline,
    FaabPickup,
    FaabWeekAppearance,
    FranchiseWeekContext,
    PlayerScore,
    PlayerWeekContextV1,
    _build_faab_lookup,
    _build_faab_performer_timelines,
    _build_franchise_context,
    _empty_context,
    _load_season_player_history,
    _render_faab_timeline,
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

    def test_player_lines_carry_franchise_tag(self):
        """Every per-franchise player line must include [Franchise] tag.

        Prevents V7 PLAYER_FRANCHISE verifier failures caused by the model
        confusing franchise attribution when composing matchup prose across
        adjacent franchise sections. Regression lock for the data-layer fix.
        """
        ps_top = PlayerScore("11111", 30.00, True, True)
        ps_bust = PlayerScore("22222", 5.00, True, False)
        ps_bench = PlayerScore("33333", 20.00, False, True)
        ps_faab = PlayerScore("44444", 18.50, True, False)
        pickup = FaabPickup("44444", "0001", 25.0, 0)
        fc = FranchiseWeekContext(
            franchise_id="0001",
            starters=(ps_top, ps_bust),
            bench=(ps_bench,),
            top_starter=ps_top,
            bust_starter=ps_bust,
            starter_total=35.00,
            bench_total=20.00,
            bench_points_over_starters=15.00,
            best_bench_player=ps_bench,
            faab_performers=((ps_faab, pickup),),
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=4,
            total_starters=2,
        )

        def team_res(fid):
            return {"0001": "Miller's Genuine Draft"}.get(fid, fid)

        result = render_player_highlights_for_prompt(
            ctx, team_resolver=team_res,
        )
        tag = "[Miller's Genuine Draft]"
        # Top, Bust, Bench > starter (2 players), FAAB = 5 occurrences
        assert result.count(tag) >= 4, (
            f"Expected [franchise] tag on every player line; "
            f"found {result.count(tag)} occurrences in:\n{result}"
        )

    def test_matchup_grouped_rendering(self):
        """When matchup_pairings are provided, franchise blocks are grouped
        under matchup headers — prevents cross-franchise player misattribution.
        """
        fc_a = FranchiseWeekContext(
            franchise_id="0001",
            starters=(PlayerScore("11111", 30.00, True, True),),
            bench=(),
            top_starter=PlayerScore("11111", 30.00, True, True),
            bust_starter=PlayerScore("11111", 30.00, True, True),
            starter_total=30.00,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=(),
        )
        fc_b = FranchiseWeekContext(
            franchise_id="0002",
            starters=(PlayerScore("22222", 25.00, True, True),),
            bench=(),
            top_starter=PlayerScore("22222", 25.00, True, True),
            bust_starter=PlayerScore("22222", 25.00, True, True),
            starter_total=25.00,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=(),
        )
        ctx = self._make_context(
            franchises=(fc_a, fc_b),
            total_players=2,
            total_starters=2,
        )

        def team_res(fid):
            return {"0001": "Team Alpha", "0002": "Team Beta"}.get(fid, fid)

        result = render_player_highlights_for_prompt(
            ctx,
            team_resolver=team_res,
            matchup_pairings=[("0001", "0002")],
        )
        # Matchup header present
        assert "--- MATCHUP: Team Alpha vs Team Beta ---" in result
        # Both franchises rendered under the header
        header_pos = result.index("--- MATCHUP:")
        alpha_pos = result.index("Team Alpha (starters:")
        beta_pos = result.index("Team Beta (starters:")
        assert header_pos < alpha_pos < beta_pos

    def test_no_matchup_pairings_uses_flat_rendering(self):
        """Without matchup_pairings, rendering is flat (backward compat)."""
        fc = FranchiseWeekContext(
            franchise_id="0001",
            starters=(PlayerScore("11111", 30.00, True, True),),
            bench=(),
            top_starter=PlayerScore("11111", 30.00, True, True),
            bust_starter=PlayerScore("11111", 30.00, True, True),
            starter_total=30.00,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=(),
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=1,
            total_starters=1,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "--- MATCHUP:" not in result
        assert "0001 (starters:" in result


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


# ── _build_faab_performer_timelines ──────────────────────────────────


class TestBuildFaabPerformerTimelines:
    """Unit tests for FAAB performer timeline derivation (Finding 5 fix)."""

    def test_watson_case_three_weeks_first_start(self):
        """Finding 5 exact case: W12 bench, W13 bench, W14 starter → first start, week 3."""
        ps = PlayerScore("15789", 22.90, True, False)
        pickup = FaabPickup("15789", "0002", 20.0, 0)
        faab_performers = [(ps, pickup)]

        season_history = {
            ("0002", "15789"): [
                (12, 7.40, False),   # W12 bench
                (13, 16.30, False),  # W13 bench
                (14, 22.90, True),   # W14 starter (current week)
            ],
        }

        timelines = _build_faab_performer_timelines(
            faab_performers, "0002", current_week=14, season_history=season_history,
        )

        assert len(timelines) == 1
        t = timelines[0]
        assert t.player_id == "15789"
        assert t.franchise_id == "0002"
        assert t.weeks_on_roster == 3
        assert t.starts_on_roster == 1
        assert t.is_first_start is True
        assert t.is_first_week_on_roster is False
        assert len(t.prior_weeks) == 2
        assert t.prior_weeks[0] == FaabWeekAppearance(week=12, score=7.40, is_starter=False)
        assert t.prior_weeks[1] == FaabWeekAppearance(week=13, score=16.30, is_starter=False)

    def test_player_with_prior_starts_not_first_start(self):
        """Player who started in a prior week → is_first_start=False."""
        ps = PlayerScore("11111", 18.00, True, False)
        pickup = FaabPickup("11111", "0001", 15.0, 0)

        season_history = {
            ("0001", "11111"): [
                (8, 12.00, True),    # W8 starter (prior start)
                (9, 5.00, False),    # W9 bench
                (10, 18.00, True),   # W10 starter (current)
            ],
        }

        timelines = _build_faab_performer_timelines(
            [(ps, pickup)], "0001", current_week=10, season_history=season_history,
        )

        assert len(timelines) == 1
        t = timelines[0]
        assert t.is_first_start is False
        assert t.starts_on_roster == 2
        assert t.weeks_on_roster == 3

    def test_first_week_on_roster(self):
        """Player's first scoring week → is_first_week_on_roster=True, no prior weeks."""
        ps = PlayerScore("22222", 25.00, True, False)
        pickup = FaabPickup("22222", "0003", 40.0, 0)

        season_history = {
            ("0003", "22222"): [
                (14, 25.00, True),   # only week (current)
            ],
        }

        timelines = _build_faab_performer_timelines(
            [(ps, pickup)], "0003", current_week=14, season_history=season_history,
        )

        assert len(timelines) == 1
        t = timelines[0]
        assert t.is_first_week_on_roster is True
        assert t.weeks_on_roster == 1
        assert t.starts_on_roster == 1
        assert t.is_first_start is True
        assert t.prior_weeks == ()

    def test_bench_player_current_week_not_first_start(self):
        """Bench player this week → is_first_start=False even with no prior starts."""
        ps = PlayerScore("33333", 8.00, False, False)  # bench this week
        pickup = FaabPickup("33333", "0001", 10.0, 0)

        season_history = {
            ("0001", "33333"): [
                (12, 3.00, False),
                (13, 8.00, False),   # current week, bench
            ],
        }

        timelines = _build_faab_performer_timelines(
            [(ps, pickup)], "0001", current_week=13, season_history=season_history,
        )

        assert len(timelines) == 1
        t = timelines[0]
        assert t.is_first_start is False
        assert t.starts_on_roster == 0

    def test_empty_season_history_returns_empty(self):
        """No season history → empty timelines."""
        ps = PlayerScore("15789", 22.90, True, False)
        pickup = FaabPickup("15789", "0002", 20.0, 0)

        timelines = _build_faab_performer_timelines(
            [(ps, pickup)], "0002", current_week=14, season_history={},
        )
        assert timelines == ()

    def test_no_faab_performers_returns_empty(self):
        """No FAAB performers → empty timelines."""
        timelines = _build_faab_performer_timelines(
            [], "0001", current_week=14,
            season_history={("0001", "15789"): [(14, 22.90, True)]},
        )
        assert timelines == ()

    def test_player_missing_from_history_skipped(self):
        """FAAB performer not in season history → skipped (silence over fabrication)."""
        ps = PlayerScore("99999", 10.00, True, False)
        pickup = FaabPickup("99999", "0001", 5.0, 0)

        season_history = {
            ("0001", "11111"): [(14, 20.00, True)],  # different player
        }

        timelines = _build_faab_performer_timelines(
            [(ps, pickup)], "0001", current_week=14, season_history=season_history,
        )
        assert timelines == ()

    def test_deterministic_sorted_by_player_id(self):
        """Multiple FAAB performers → sorted by player_id."""
        ps_b = PlayerScore("22222", 15.00, True, False)
        ps_a = PlayerScore("11111", 20.00, True, False)
        pickup_b = FaabPickup("22222", "0001", 10.0, 0)
        pickup_a = FaabPickup("11111", "0001", 25.0, 0)

        season_history = {
            ("0001", "22222"): [(14, 15.00, True)],
            ("0001", "11111"): [(14, 20.00, True)],
        }

        # Feed in reverse order to verify sorting
        timelines = _build_faab_performer_timelines(
            [(ps_b, pickup_b), (ps_a, pickup_a)],
            "0001", current_week=14, season_history=season_history,
        )

        assert len(timelines) == 2
        assert timelines[0].player_id == "11111"
        assert timelines[1].player_id == "22222"


# ── _render_faab_timeline ────────────────────────────────────────────


class TestRenderFaabTimeline:
    """Unit tests for FAAB timeline prompt rendering."""

    def test_watson_case_rendering(self):
        """Finding 5 exact case renders correctly."""
        timeline = FaabPerformerTimeline(
            player_id="15789",
            franchise_id="0002",
            prior_weeks=(
                FaabWeekAppearance(week=12, score=7.40, is_starter=False),
                FaabWeekAppearance(week=13, score=16.30, is_starter=False),
            ),
            weeks_on_roster=3,
            starts_on_roster=1,
            is_first_start=True,
            is_first_week_on_roster=False,
        )

        result = _render_faab_timeline(timeline)
        assert "Week 3 on roster" in result
        assert "first start" in result
        assert "W12 7.40 (bench)" in result
        assert "W13 16.30 (bench)" in result

    def test_first_week_rendering(self):
        """First week on roster renders appropriately."""
        timeline = FaabPerformerTimeline(
            player_id="22222",
            franchise_id="0003",
            prior_weeks=(),
            weeks_on_roster=1,
            starts_on_roster=1,
            is_first_start=True,
            is_first_week_on_roster=True,
        )

        result = _render_faab_timeline(timeline)
        assert "First week on roster" in result
        assert "first start" in result
        assert "prior" not in result

    def test_veteran_starter_rendering(self):
        """Player with prior starts — no 'first start' claim."""
        timeline = FaabPerformerTimeline(
            player_id="11111",
            franchise_id="0001",
            prior_weeks=(
                FaabWeekAppearance(week=8, score=12.00, is_starter=True),
                FaabWeekAppearance(week=9, score=5.00, is_starter=False),
            ),
            weeks_on_roster=3,
            starts_on_roster=2,
            is_first_start=False,
            is_first_week_on_roster=False,
        )

        result = _render_faab_timeline(timeline)
        assert "Week 3 on roster" in result
        assert "first start" not in result
        assert "W8 12.00 (starter)" in result
        assert "W9 5.00 (bench)" in result

    def test_player_resolver_not_used(self):
        """Timeline rendering does not use player names (IDs only in timeline)."""
        timeline = FaabPerformerTimeline(
            player_id="15789",
            franchise_id="0002",
            prior_weeks=(
                FaabWeekAppearance(week=12, score=7.40, is_starter=False),
            ),
            weeks_on_roster=2,
            starts_on_roster=1,
            is_first_start=True,
            is_first_week_on_roster=False,
        )

        def resolver(pid: str) -> str:
            return "Watson"

        result = _render_faab_timeline(timeline, player_resolver=resolver)
        # Timeline content should not include player name — it's contextual
        assert "W12 7.40 (bench)" in result


# ── Render integration with timelines ────────────────────────────────


class TestRenderPlayerHighlightsWithTimeline:
    """Test that render_player_highlights_for_prompt includes timeline data."""

    def _make_context(self, **kwargs):
        defaults = dict(
            league_id="70985",
            season=2025,
            week=14,
            franchises=(),
            week_top_scorer=None,
            week_lowest_starter=None,
            total_players=0,
            total_starters=0,
        )
        defaults.update(kwargs)
        return PlayerWeekContextV1(**defaults)

    def test_faab_with_timeline_rendered(self):
        """FAAB performer line includes pre-derived temporal context."""
        ps = PlayerScore("15789", 22.90, True, False)
        pickup = FaabPickup("15789", "0002", 20.0, 0)
        timeline = FaabPerformerTimeline(
            player_id="15789",
            franchise_id="0002",
            prior_weeks=(
                FaabWeekAppearance(week=12, score=7.40, is_starter=False),
                FaabWeekAppearance(week=13, score=16.30, is_starter=False),
            ),
            weeks_on_roster=3,
            starts_on_roster=1,
            is_first_start=True,
            is_first_week_on_roster=False,
        )
        fc = FranchiseWeekContext(
            franchise_id="0002",
            starters=(ps,),
            bench=(),
            top_starter=ps,
            bust_starter=ps,
            starter_total=22.90,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=((ps, pickup),),
            faab_performer_timelines=(timeline,),
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=1,
            total_starters=1,
        )

        result = render_player_highlights_for_prompt(ctx)
        # Base FAAB line present
        assert "FAAB pickup $20" in result
        assert "22.90" in result
        # Timeline appended
        assert "Week 3 on roster" in result
        assert "first start" in result
        assert "W12 7.40 (bench)" in result

    def test_faab_without_timeline_still_renders(self):
        """FAAB performer without timeline renders the base line only (backward compat)."""
        ps = PlayerScore("15789", 22.90, True, False)
        pickup = FaabPickup("15789", "0002", 20.0, 0)
        fc = FranchiseWeekContext(
            franchise_id="0002",
            starters=(ps,),
            bench=(),
            top_starter=ps,
            bust_starter=ps,
            starter_total=22.90,
            bench_total=0.0,
            bench_points_over_starters=0.0,
            best_bench_player=None,
            faab_performers=((ps, pickup),),
            # No timelines (backward compat)
        )
        ctx = self._make_context(
            franchises=(fc,),
            total_players=1,
            total_starters=1,
        )

        result = render_player_highlights_for_prompt(ctx)
        assert "FAAB pickup $20" in result
        assert "22.90" in result
        # No timeline content
        assert "on roster" not in result


# ── DB-backed integration: FAAB timelines ────────────────────────────


@pytest.fixture
def db_with_faab(tmp_path):
    """Create a test database with multi-week player scores and FAAB data.

    Models the Finding 5 Watson case:
    - Player 15789 acquired via FAAB ($20) by franchise 0002
    - W12: 7.40 bench, W13: 16.30 bench, W14: 22.90 starter
    """
    db_path = str(tmp_path / "test_faab.sqlite")
    schema = SCHEMA_PATH.read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)

    events: list[tuple[str, dict]] = []

    # Franchise 0002 player 15789 — multi-week history (Watson case)
    for week, score, is_starter in [(12, 7.40, False), (13, 16.30, False), (14, 22.90, True)]:
        payload = _make_payload("0002", "15789", score, is_starter=is_starter, week=week)
        events.append(("WEEKLY_PLAYER_SCORE", payload))

    # Franchise 0002 another starter in W14 (so we have a valid matchup week)
    events.append(("WEEKLY_PLAYER_SCORE", _make_payload("0002", "44444", 15.00, week=14)))

    # Franchise 0001 starter in W14
    events.append(("WEEKLY_PLAYER_SCORE", _make_payload("0001", "55555", 30.00, week=14)))

    # FAAB award: franchise 0002 picked up player 15789 for $20
    faab_payload = {
        "player_id": "15789",
        "franchise_id": "0002",
        "bid_amount": "20",
    }
    events.append(("WAIVER_BID_AWARDED", faab_payload))

    for i, (event_type, payload) in enumerate(events):
        ext_id = f"test_faab_{i}"
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, event_type, external_source, external_id,
                payload_json, ingested_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
            ("70985", 2025, event_type, "MFL", ext_id, json.dumps(payload)),
        )

    con.commit()
    con.close()

    from squadvault.core.canonicalize.run_canonicalize import canonicalize
    canonicalize(league_id="70985", season=2025, db_path=db_path)

    return db_path


class TestFaabTimelineDbIntegration:
    """DB-backed integration tests for FAAB performer timelines."""

    def test_timeline_populated_from_db(self, db_with_faab):
        """derive_player_week_context_v1 populates FAAB timelines from DB."""
        ctx = derive_player_week_context_v1(
            db_path=db_with_faab, league_id="70985", season=2025, week=14,
        )
        assert ctx.has_data is True

        f0002 = [f for f in ctx.franchises if f.franchise_id == "0002"][0]

        # FAAB performer linked
        assert len(f0002.faab_performers) == 1
        ps, pickup = f0002.faab_performers[0]
        assert ps.player_id == "15789"
        assert pickup.bid_amount == 20.0

        # Timeline populated
        assert len(f0002.faab_performer_timelines) == 1
        t = f0002.faab_performer_timelines[0]
        assert t.player_id == "15789"
        assert t.weeks_on_roster == 3
        assert t.is_first_start is True
        assert t.is_first_week_on_roster is False
        assert len(t.prior_weeks) == 2
        assert t.prior_weeks[0].week == 12
        assert t.prior_weeks[0].is_starter is False
        assert t.prior_weeks[1].week == 13

    def test_timeline_renders_in_prompt(self, db_with_faab):
        """Full render pipeline includes timeline data."""
        ctx = derive_player_week_context_v1(
            db_path=db_with_faab, league_id="70985", season=2025, week=14,
        )
        result = render_player_highlights_for_prompt(ctx)
        assert "FAAB pickup $20" in result
        assert "Week 3 on roster" in result
        assert "first start" in result
        assert "W12 7.40 (bench)" in result

    def test_season_player_history_loads(self, db_with_faab):
        """_load_season_player_history returns all weeks for the season."""
        history = _load_season_player_history(db_with_faab, "70985", 2025)

        # Player 15789 on franchise 0002 should have 3 weeks
        key = ("0002", "15789")
        assert key in history
        assert len(history[key]) == 3
        assert history[key][0] == (12, 7.40, False)
        assert history[key][1] == (13, 16.30, False)
        assert history[key][2] == (14, 22.90, True)

    def test_franchise_without_faab_has_empty_timelines(self, db_with_faab):
        """Franchise with no FAAB performers has empty timelines tuple."""
        ctx = derive_player_week_context_v1(
            db_path=db_with_faab, league_id="70985", season=2025, week=14,
        )
        f0001 = [f for f in ctx.franchises if f.franchise_id == "0001"][0]
        assert f0001.faab_performer_timelines == ()

    def test_deterministic_with_faab(self, db_with_faab):
        """Same inputs produce identical outputs including timelines."""
        ctx1 = derive_player_week_context_v1(
            db_path=db_with_faab, league_id="70985", season=2025, week=14,
        )
        ctx2 = derive_player_week_context_v1(
            db_path=db_with_faab, league_id="70985", season=2025, week=14,
        )
        assert ctx1 == ctx2
