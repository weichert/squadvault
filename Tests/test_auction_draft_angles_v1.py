"""Tests for Auction Draft Angle Detection v1 (Dimension 6).

Exercises each of the 9 auction draft detectors (20-28) against
synthetic data. Also tests data loading and full pipeline.
"""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    _AuctionPick,
    _PlayerSeasonScoring,
    _load_all_auction_picks,
    _load_player_season_scoring,
    detect_auction_price_vs_production,
    detect_auction_dollar_per_point,
    detect_auction_bust,
    detect_auction_budget_allocation,
    detect_auction_positional_spending,
    detect_auction_strategy_consistency,
    detect_auction_league_inflation,
    detect_auction_most_expensive_history,
    detect_auction_draft_angles_v1,
)


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "test_league"
SEASON = 2024


# ── Helpers ──────────────────────────────────────────────────────────


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_draft_pick(con, *, league_id, season, franchise_id, player_id, bid_amount):
    occurred_at = f"{season}-09-01T12:00:00Z"
    payload = {"franchise_id": franchise_id, "player_id": player_id, "bid_amount": bid_amount}
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"dp_{league_id}_{season}_{franchise_id}_{player_id}"
    con.execute(
        """INSERT INTO memory_events (league_id, season, external_source, external_id,
           event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, 'test', ?, 'DRAFT_PICK', ?, ?, ?)""",
        (league_id, season, ext_id, occurred_at, occurred_at, payload_json))
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events (league_id, season, event_type,
           action_fingerprint, best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, 'DRAFT_PICK', ?, ?, 100, ?, ?)""",
        (league_id, season, f"fp_{ext_id}", me_id, occurred_at, occurred_at))


def _insert_player_score(con, *, league_id, season, week, franchise_id,
                          player_id, score, is_starter=True):
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {"week": week, "franchise_id": franchise_id, "player_id": player_id,
               "score": score, "is_starter": is_starter, "should_start": False}
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"ps_{league_id}_{season}_{week}_{franchise_id}_{player_id}"
    con.execute(
        """INSERT INTO memory_events (league_id, season, external_source, external_id,
           event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, 'test', ?, 'WEEKLY_PLAYER_SCORE', ?, ?, ?)""",
        (league_id, season, ext_id, occurred_at, occurred_at, payload_json))
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events (league_id, season, event_type,
           action_fingerprint, best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, 'WEEKLY_PLAYER_SCORE', ?, ?, 100, ?, ?)""",
        (league_id, season, f"fp_{ext_id}", me_id, occurred_at, occurred_at))


def _insert_player_directory(con, *, league_id, season, player_id, name, position):
    con.execute(
        """INSERT OR REPLACE INTO player_directory
           (league_id, season, player_id, name, position)
           VALUES (?, ?, ?, ?, ?)""",
        (league_id, season, player_id, name, position))


def _make_pick(season, franchise_id, player_id, bid, position=""):
    return _AuctionPick(season=season, franchise_id=franchise_id,
                         player_id=player_id, bid_amount=bid, position=position)


def _make_scoring(season, franchise_id, player_id, total, weeks, starters=None):
    return _PlayerSeasonScoring(season=season, franchise_id=franchise_id,
                                 player_id=player_id, total_points=total,
                                 weeks_played=weeks, starter_weeks=starters or weeks)


# ── Detector 20: AUCTION_PRICE_VS_PRODUCTION ─────────────────────────


class TestAuctionPriceVsProduction:
    def test_finds_alltime_best_investment(self):
        picks = [
            _make_pick(2020, "F1", "P1", 50.0),
            _make_pick(2021, "F2", "P2", 30.0),
        ]
        scoring = {
            (2020, "F1", "P1"): _make_scoring(2020, "F1", "P1", 300.0, 14),
            (2021, "F1", "P1"): _make_scoring(2021, "F1", "P1", 280.0, 14),
            (2021, "F2", "P2"): _make_scoring(2021, "F2", "P2", 200.0, 14),
        }
        # P1: 580 pts / $50 = 11.6 ppd. P2: 200 / $30 = 6.7 ppd.
        angles = detect_auction_price_vs_production(picks, scoring)
        assert len(angles) == 1
        assert "P1" in angles[0].headline
        assert angles[0].strength == 2

    def test_single_season_silence(self):
        picks = [_make_pick(2024, "F1", "P1", 50.0)]
        scoring = {(2024, "F1", "P1"): _make_scoring(2024, "F1", "P1", 200.0, 10)}
        angles = detect_auction_price_vs_production(picks, scoring)
        assert len(angles) == 0


# ── Detector 21: AUCTION_DOLLAR_PER_POINT ────────────────────────────


class TestAuctionDollarPerPoint:
    def test_finds_best_value(self):
        picks = [
            _make_pick(2024, "F1", "P1", 1.0),
            _make_pick(2024, "F2", "P2", 50.0),
            _make_pick(2024, "F3", "P3", 20.0),
        ]
        scoring = {
            (2024, "F1", "P1"): _make_scoring(2024, "F1", "P1", 60.0, 4),
            (2024, "F2", "P2"): _make_scoring(2024, "F2", "P2", 80.0, 4),
            (2024, "F3", "P3"): _make_scoring(2024, "F3", "P3", 50.0, 4),
        }
        angles = detect_auction_dollar_per_point(picks, scoring, 2024)
        assert len(angles) == 1
        assert "P1" in angles[0].headline  # 60/1 = 60 ppd, best

    def test_insufficient_data_silence(self):
        picks = [_make_pick(2024, "F1", "P1", 10.0)]
        scoring = {(2024, "F1", "P1"): _make_scoring(2024, "F1", "P1", 30.0, 2)}
        angles = detect_auction_dollar_per_point(picks, scoring, 2024)
        assert len(angles) == 0  # only 1 pick, need 3+


# ── Detector 22: AUCTION_BUST ────────────────────────────────────────


class TestAuctionBust:
    def test_detects_bust(self):
        picks = [
            _make_pick(2024, "F1", "P1", 60.0),  # top pick, underperforms
            _make_pick(2024, "F1", "P2", 20.0),
        ]
        scoring = {
            (2024, "F1", "P1"): _make_scoring(2024, "F1", "P1", 24.0, 6),  # avg 4.0
            (2024, "F1", "P2"): _make_scoring(2024, "F1", "P2", 90.0, 6),  # avg 15.0
        }
        # League avg: (4.0 + 15.0) / 2 = 9.5. P1 at 4.0 < 9.5 * 0.5 = 4.75
        angles = detect_auction_bust(picks, scoring, 2024)
        assert len(angles) == 1
        assert "P1" in angles[0].headline
        assert angles[0].strength == 2

    def test_no_bust_when_performing(self):
        picks = [_make_pick(2024, "F1", "P1", 60.0)]
        scoring = {(2024, "F1", "P1"): _make_scoring(2024, "F1", "P1", 120.0, 6)}
        angles = detect_auction_bust(picks, scoring, 2024)
        assert len(angles) == 0


# ── Detector 23: AUCTION_BUDGET_ALLOCATION ───────────────────────────


class TestAuctionBudgetAllocation:
    def test_detects_concentrated_vs_balanced(self):
        picks = [
            # F1: stars-and-scrubs (high variance)
            _make_pick(2024, "F1", "P1", 70.0),
            _make_pick(2024, "F1", "P2", 60.0),
            _make_pick(2024, "F1", "P3", 1.0),
            _make_pick(2024, "F1", "P4", 1.0),
            # F2: balanced
            _make_pick(2024, "F2", "P5", 15.0),
            _make_pick(2024, "F2", "P6", 12.0),
            _make_pick(2024, "F2", "P7", 10.0),
            _make_pick(2024, "F2", "P8", 8.0),
            # F3: medium
            _make_pick(2024, "F3", "P9", 30.0),
            _make_pick(2024, "F3", "PA", 20.0),
            _make_pick(2024, "F3", "PB", 10.0),
        ]
        angles = detect_auction_budget_allocation(picks, 2024)
        assert len(angles) == 2
        headlines = [a.headline for a in angles]
        assert any("F1" in h and "concentrated" in h for h in headlines)
        assert any("F2" in h and "balanced" in h for h in headlines)

    def test_fewer_than_3_franchises_silence(self):
        picks = [_make_pick(2024, "F1", "P1", 50.0)]
        angles = detect_auction_budget_allocation(picks, 2024)
        assert len(angles) == 0


# ── Detector 24: AUCTION_POSITIONAL_SPENDING ─────────────────────────


class TestAuctionPositionalSpending:
    def test_detects_heavy_positional_spending(self):
        picks = [
            _make_pick(2024, "F1", "P1", 60.0, "QB"),
            _make_pick(2024, "F1", "P2", 40.0, "QB"),
            _make_pick(2024, "F1", "P3", 30.0, "RB"),
            _make_pick(2024, "F1", "P4", 20.0, "WR"),
        ]
        # QB: 100/150 = 67%
        angles = detect_auction_positional_spending(picks, 2024)
        assert len(angles) >= 1
        assert any("QB" in a.headline for a in angles)

    def test_no_position_data_silence(self):
        picks = [_make_pick(2024, "F1", "P1", 50.0, "")]  # no position
        angles = detect_auction_positional_spending(picks, 2024)
        assert len(angles) == 0


# ── Detector 25: AUCTION_STRATEGY_CONSISTENCY ────────────────────────


class TestAuctionStrategyConsistency:
    def test_detects_consistent_spending(self):
        picks = []
        for yr in range(2020, 2025):
            picks.append(_make_pick(yr, "F1", f"QB_{yr}", 60.0, "QB"))
            picks.append(_make_pick(yr, "F1", f"RB_{yr}", 30.0, "RB"))
            picks.append(_make_pick(yr, "F1", f"WR_{yr}", 10.0, "WR"))
        # F1 spends 60% on QB consistently across 5 seasons
        angles = detect_auction_strategy_consistency(picks, 2024)
        assert len(angles) >= 1
        assert any("QB" in a.headline and "F1" in a.headline for a in angles)

    def test_insufficient_seasons_silence(self):
        picks = [_make_pick(2024, "F1", "P1", 50.0, "QB")]
        angles = detect_auction_strategy_consistency(picks, 2024)
        assert len(angles) == 0


# ── Detector 26: AUCTION_LEAGUE_INFLATION ────────────────────────────


class TestAuctionLeagueInflation:
    def test_detects_price_increase(self):
        picks = []
        for yr in range(2020, 2025):
            base = 20 + (yr - 2020) * 10  # 20, 30, 40, 50, 60
            picks.append(_make_pick(yr, "F1", f"QB_{yr}", float(base), "QB"))
            picks.append(_make_pick(yr, "F2", f"QB2_{yr}", float(base + 5), "QB"))
        # QB avg goes from ~22.5 in 2020 to ~62.5 in 2024 = ~178% increase
        angles = detect_auction_league_inflation(picks, 2024)
        assert len(angles) >= 1
        assert any("QB" in a.headline and "risen" in a.headline for a in angles)

    def test_stable_prices_no_angle(self):
        picks = []
        for yr in range(2020, 2024):
            picks.append(_make_pick(yr, "F1", f"P_{yr}", 30.0, "QB"))
        angles = detect_auction_league_inflation(picks, 2024)
        assert len(angles) == 0  # no change


# ── Detector 28: AUCTION_MOST_EXPENSIVE_HISTORY ──────────────────────


class TestAuctionMostExpensiveHistory:
    def test_finds_alltime_max(self):
        picks = [
            _make_pick(2020, "F1", "P1", 50.0, "QB"),
            _make_pick(2022, "F2", "P2", 70.0, "QB"),
            _make_pick(2024, "F3", "P3", 45.0, "RB"),
        ]
        angles = detect_auction_most_expensive_history(picks)
        assert len(angles) == 1
        assert "F2" in angles[0].headline
        assert "$70" in angles[0].headline

    def test_single_season_silence(self):
        picks = [_make_pick(2024, "F1", "P1", 70.0, "QB")]
        angles = detect_auction_most_expensive_history(picks)
        assert len(angles) == 0


# ── Data loading (DB integration) ────────────────────────────────────


class TestAuctionDataLoading:
    def test_loads_picks_with_positions(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_draft_pick(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F1", player_id="P1", bid_amount=50.0)
        _insert_player_directory(con, league_id=LEAGUE, season=SEASON,
                                  player_id="P1", name="Josh Allen", position="QB")
        con.commit()
        con.close()

        picks = _load_all_auction_picks(db_path, LEAGUE)
        assert len(picks) == 1
        assert picks[0].position == "QB"
        assert picks[0].bid_amount == 50.0

    def test_loads_scoring_aggregates(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=20.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F1", player_id="P1", score=25.0)
        con.commit()
        con.close()

        scoring = _load_player_season_scoring(db_path, LEAGUE)
        key = (SEASON, "F1", "P1")
        assert key in scoring
        assert scoring[key].total_points == 45.0
        assert scoring[key].weeks_played == 2

    def test_empty_data(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        assert _load_all_auction_picks(db_path, LEAGUE) == []
        assert _load_player_season_scoring(db_path, LEAGUE) == {}


# ── Full pipeline (DB integration) ──────────────────────────────────


class TestAuctionFullPipeline:
    def test_pipeline_detects_angles(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Two seasons of draft picks
        for yr in [2023, SEASON]:
            _insert_draft_pick(con, league_id=LEAGUE, season=yr,
                                franchise_id="F1", player_id=f"P1_{yr}", bid_amount=50.0)
            _insert_draft_pick(con, league_id=LEAGUE, season=yr,
                                franchise_id="F2", player_id=f"P2_{yr}", bid_amount=10.0)
            _insert_draft_pick(con, league_id=LEAGUE, season=yr,
                                franchise_id="F3", player_id=f"P3_{yr}", bid_amount=30.0)
        # Scoring for current season
        for w in range(1, 6):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id=f"P1_{SEASON}", score=25.0)
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F2", player_id=f"P2_{SEASON}", score=15.0)
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F3", player_id=f"P3_{SEASON}", score=20.0)
        con.commit()
        con.close()

        angles = detect_auction_draft_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        assert len(angles) >= 1
        categories = {a.category for a in angles}
        # Should have at least dollar-per-point (best value)
        assert "AUCTION_DOLLAR_PER_POINT" in categories

    def test_pipeline_empty_data(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        angles = detect_auction_draft_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        assert angles == []

    def test_pipeline_deterministic(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for yr in [2023, SEASON]:
            _insert_draft_pick(con, league_id=LEAGUE, season=yr,
                                franchise_id="F1", player_id=f"P_{yr}", bid_amount=40.0)
        for w in range(1, 5):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id=f"P_{SEASON}", score=20.0)
        con.commit()
        con.close()

        a1 = detect_auction_draft_angles_v1(db_path=db_path, league_id=LEAGUE,
                                             season=SEASON, week=4)
        a2 = detect_auction_draft_angles_v1(db_path=db_path, league_id=LEAGUE,
                                             season=SEASON, week=4)
        assert a1 == a2
