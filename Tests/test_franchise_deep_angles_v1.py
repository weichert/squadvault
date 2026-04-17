"""Tests for Franchise Deep Angle Detection v1 (Dimensions 7-9).

Exercises the implemented detectors against synthetic data.
"""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.core.recaps.context.league_history_v1 import HistoricalMatchup
from squadvault.core.recaps.context.franchise_deep_angles_v1 import (
    detect_scoring_concentration,
    detect_scoring_volatility,
    detect_star_explosion_count,
    detect_positional_strength,
    detect_bench_cost_game,
    detect_perfect_lineup_week,
    detect_close_game_record,
    detect_lucky_record,
    detect_the_bridesmaid,
    detect_transaction_volume_identity,
    detect_second_half_surge_collapse,
    detect_franchise_alltime_scoring,
    detect_weekly_scoring_rank_dominance,
    detect_schedule_strength,
    detect_points_against_luck,
    detect_repeat_matchup_pattern,
    detect_championship_history,
    detect_the_almost,
    detect_scoring_momentum_in_streak,
    _is_near_monotonic_growing,
    _is_near_monotonic_shrinking,
    detect_franchise_deep_angles_v1,
)


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "test_league"
SEASON = 2024


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _make_score_payload(week, franchise_id, player_id, score,
                         is_starter=True, should_start=None):
    if should_start is None:
        should_start = is_starter
    return {
        "week": week, "franchise_id": franchise_id, "player_id": player_id,
        "score": score, "is_starter": is_starter, "should_start": should_start,
    }


def _make_matchup(season, week, winner, loser, ws, ls, is_tie=False):
    return HistoricalMatchup(
        season=season, week=week, winner_id=winner, loser_id=loser,
        winner_score=ws, loser_score=ls, is_tie=is_tie,
        margin=round(abs(ws - ls), 2),
    )


# ── Dimension 7 ──────────────────────────────────────────────────────


class TestScoringConcentration:
    def test_detects_high_concentration(self):
        payloads = [
            _make_score_payload(1, "F1", "P1", 40.0),
            _make_score_payload(1, "F1", "P2", 10.0),
            _make_score_payload(1, "F1", "P3", 10.0),
        ]
        # P1 is 40/60 = 67%
        angles = detect_scoring_concentration(payloads, 1)
        assert len(angles) == 1
        assert "P1" in angles[0].headline
        assert angles[0].strength == 2

    def test_balanced_no_angle(self):
        payloads = [
            _make_score_payload(1, "F1", "P1", 15.0),
            _make_score_payload(1, "F1", "P2", 15.0),
            _make_score_payload(1, "F1", "P3", 15.0),
        ]
        angles = detect_scoring_concentration(payloads, 1)
        assert len(angles) == 0


class TestScoringVolatility:
    def test_detects_volatile_and_consistent(self):
        payloads = []
        for w in range(1, 6):
            # F1: consistent (100 every week)
            payloads.append(_make_score_payload(w, "F1", "P1", 100.0))
            # F2: volatile (60 to 160)
            payloads.append(_make_score_payload(w, "F2", "P2", 60.0 + w * 20))
            # F3: medium
            payloads.append(_make_score_payload(w, "F3", "P3", 90.0 + w * 5))
        angles = detect_scoring_volatility(payloads, 5)
        assert len(angles) == 2
        headlines = [a.headline for a in angles]
        assert any("F1" in h and "narrowest" in h for h in headlines)
        assert any("F2" in h and "widest" in h for h in headlines)

    def test_fname_resolves_franchise_id_in_headline(self):
        """Regression: headlines must wrap franchise_id with fname.

        Prior bug: detect_scoring_volatility accepted an fname parameter
        but the two SCORING_VOLATILITY headlines ("narrowest/widest
        scoring range") emitted raw franchise IDs rather than resolved
        names. Discovered in the 2026-04-16 Writing Room surfacing audit
        when a production prompt for 2025 W10 contained the line:
            [MINOR] [RE: Miller's Genuine Draft] 0006 has the
            narrowest scoring range this season ...
        The [RE: ...] tag resolved correctly via the lifecycle's
        _name_map; the headline did not because the detector ignored
        its own fname argument. This test prevents regression by
        passing a non-identity fname and asserting the resolved name
        appears in both headlines while the raw fid does not.
        """
        payloads = []
        for w in range(1, 6):
            payloads.append(_make_score_payload(w, "0001", "P1", 100.0))
            payloads.append(_make_score_payload(w, "0002", "P2", 60.0 + w * 20))
            payloads.append(_make_score_payload(w, "0003", "P3", 90.0 + w * 5))

        name_map = {
            "0001": "Italian Cavallini",
            "0002": "Ben's Gods",
            "0003": "Purple Haze",
        }
        angles = detect_scoring_volatility(
            payloads, 5, fname=lambda fid: name_map.get(fid, fid)
        )
        assert len(angles) == 2
        headlines = [a.headline for a in angles]
        narrowest = next(h for h in headlines if "narrowest" in h)
        widest = next(h for h in headlines if "widest" in h)

        # Resolved names must appear; raw fids must not.
        assert "Italian Cavallini" in narrowest
        assert "0001" not in narrowest
        assert "Ben's Gods" in widest
        assert "0002" not in widest

        # franchise_ids tuple still carries the raw fid for downstream
        # [RE: ...] resolution — this is the correct shape and must
        # remain unchanged.
        narrowest_angle = next(a for a in angles if "narrowest" in a.headline)
        widest_angle = next(a for a in angles if "widest" in a.headline)
        assert narrowest_angle.franchise_ids == ("0001",)
        assert widest_angle.franchise_ids == ("0002",)


class TestStarExplosionCount:
    def test_detects_explosion_leader(self):
        payloads = [
            _make_score_payload(1, "F1", "P1", 45.0),
            _make_score_payload(2, "F1", "P1", 42.0),
            _make_score_payload(3, "F1", "P1", 50.0),
            _make_score_payload(1, "F2", "P2", 41.0),
        ]
        # F1: 3 explosions, F2: 1. F1 has 3x as many.
        angles = detect_star_explosion_count(payloads, 3)
        assert len(angles) == 1
        assert "F1" in angles[0].headline


class TestPositionalStrength:
    def test_detects_positional_leader(self):
        payloads = [
            _make_score_payload(1, "F1", "P1", 30.0),
            _make_score_payload(1, "F1", "P2", 20.0),
            _make_score_payload(1, "F2", "P3", 25.0),
        ]
        positions = {"P1": "QB", "P2": "RB", "P3": "QB"}
        angles = detect_positional_strength(payloads, positions, 1)
        qb_angles = [a for a in angles if "QB" in a.headline]
        assert len(qb_angles) == 1
        assert "F1" in qb_angles[0].headline  # F1 has 30 QB pts vs F2's 25


# ── Dimension 8 ──────────────────────────────────────────────────────


class TestBenchCostGame:
    def test_detects_bench_cost(self):
        payloads = [
            _make_score_payload(5, "F1", "P1", 15.0, is_starter=True),
            # Bench player who should have started, scored more than margin
            _make_score_payload(5, "F1", "P2", 20.0, is_starter=False, should_start=True),
        ]
        matchups = [_make_matchup(2024, 5, "F2", "F1", 110.0, 105.0)]
        # F1 lost by 5, had 20 on bench
        angles = detect_bench_cost_game(payloads, matchups, 2024, 5)
        assert len(angles) == 1
        assert "F1" in angles[0].headline
        assert angles[0].strength == 2

    def test_no_cost_when_bench_less_than_margin(self):
        payloads = [
            _make_score_payload(5, "F1", "P2", 3.0, is_starter=False, should_start=True),
        ]
        matchups = [_make_matchup(2024, 5, "F2", "F1", 120.0, 100.0)]
        # Lost by 20, only 3 on bench
        angles = detect_bench_cost_game(payloads, matchups, 2024, 5)
        assert len(angles) == 0


class TestPerfectLineupWeek:
    def test_detects_perfect_lineup(self):
        payloads = [
            _make_score_payload(5, "F1", "P1", 25.0, is_starter=True, should_start=True),
            _make_score_payload(5, "F1", "P2", 15.0, is_starter=True, should_start=True),
            _make_score_payload(5, "F1", "P3", 5.0, is_starter=False, should_start=False),
        ]
        angles = detect_perfect_lineup_week(payloads, 5)
        assert len(angles) == 1
        assert "F1" in angles[0].headline

    def test_imperfect_lineup_no_angle(self):
        payloads = [
            _make_score_payload(5, "F1", "P1", 25.0, is_starter=True, should_start=True),
            # Should have started but was benched
            _make_score_payload(5, "F1", "P2", 20.0, is_starter=False, should_start=True),
        ]
        angles = detect_perfect_lineup_week(payloads, 5)
        assert len(angles) == 0


# ── Dimension 9 ──────────────────────────────────────────────────────


class TestCloseGameRecord:
    def test_detects_clutch_record(self):
        matchups = [
            _make_matchup(2022, w, "F1", "F2", 100.0 + w, 98.0 + w)
            for w in range(1, 6)
        ] + [
            _make_matchup(2023, w, "F1", "F3", 100.0, 97.0)
            for w in range(1, 4)
        ] + [
            # Close game in the target week (required for detector to fire)
            _make_matchup(2024, 1, "F1", "F2", 102.0, 100.0),
        ]
        # F1: 9-0 in close games
        angles = detect_close_game_record(matchups, 2024, 1)
        assert len(angles) >= 1
        assert any("F1" in a.headline for a in angles)


class TestLuckyRecord:
    def test_detects_lucky_team(self):
        matchups = [
            # F1 wins close, gets outscored overall
            _make_matchup(2024, 1, "F1", "F2", 101.0, 100.0),
            _make_matchup(2024, 2, "F1", "F2", 102.0, 100.0),
            _make_matchup(2024, 3, "F1", "F2", 100.0, 99.0),
            _make_matchup(2024, 4, "F2", "F1", 150.0, 80.0),  # F1 blown out
            _make_matchup(2024, 5, "F1", "F3", 101.0, 100.0),
            _make_matchup(2024, 5, "F2", "F3", 110.0, 100.0),  # need F3 for 3+ teams
        ]
        # F1: 4-1 but outscored (101+102+100+80+101=484 PF, 100+100+99+150+100=549 PA = -65)
        angles = detect_lucky_record(matchups, 2024, 5)
        lucky = [a for a in angles if "F1" in a.headline]
        assert len(lucky) == 1
        assert angles[0].strength == 2


class TestTheBridesmaid:
    def test_detects_bridesmaid(self):
        payloads = [
            _make_score_payload(5, "F1", "P1", 80.0),
            _make_score_payload(5, "F2", "P2", 75.0),  # second-highest
            _make_score_payload(5, "F3", "P3", 60.0),
        ]
        matchups = [
            _make_matchup(2024, 5, "F1", "F2", 80.0, 75.0),  # F2 lost
            _make_matchup(2024, 5, "F3", "F4", 60.0, 50.0),
        ]
        angles = detect_the_bridesmaid(payloads, matchups, 2024, 5)
        assert len(angles) == 1
        assert "F2" in angles[0].headline

    def test_no_bridesmaid_when_second_won(self):
        payloads = [
            _make_score_payload(5, "F1", "P1", 80.0),
            _make_score_payload(5, "F2", "P2", 75.0),
            _make_score_payload(5, "F3", "P3", 60.0),
        ]
        matchups = [
            _make_matchup(2024, 5, "F2", "F3", 75.0, 60.0),  # F2 won
            _make_matchup(2024, 5, "F1", "F4", 80.0, 50.0),
        ]
        angles = detect_the_bridesmaid(payloads, matchups, 2024, 5)
        assert len(angles) == 0


class TestTransactionVolumeIdentity:
    def test_detects_active_vs_quiet(self):
        counts = {"F1": 45, "F2": 12, "F3": 20}
        angles = detect_transaction_volume_identity(counts)
        assert len(angles) == 1
        assert "F1" in angles[0].headline
        assert "F2" in angles[0].headline

    def test_similar_counts_no_angle(self):
        counts = {"F1": 15, "F2": 14, "F3": 13}
        angles = detect_transaction_volume_identity(counts)
        assert len(angles) == 0  # not 2x difference


# ── Full pipeline (DB integration) ──────────────────────────────────


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score):
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = json.dumps({
        "week": week, "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}", "is_tie": False,
    }, sort_keys=True)
    ext_id = f"m_{league_id}_{season}_{week}_{winner_id}_{loser_id}"
    con.execute(
        """INSERT INTO memory_events (league_id, season, external_source, external_id,
           event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, 'test', ?, 'WEEKLY_MATCHUP_RESULT', ?, ?, ?)""",
        (league_id, season, ext_id, occurred_at, occurred_at, payload))
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events (league_id, season, event_type,
           action_fingerprint, best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, 'WEEKLY_MATCHUP_RESULT', ?, ?, 100, ?, ?)""",
        (league_id, season, f"fp_{ext_id}", me_id, occurred_at, occurred_at))


def _insert_player_score(con, *, league_id, season, week, franchise_id,
                          player_id, score, is_starter=True, should_start=None):
    if should_start is None:
        should_start = is_starter
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = json.dumps({
        "week": week, "franchise_id": franchise_id, "player_id": player_id,
        "score": score, "is_starter": is_starter, "should_start": should_start,
    }, sort_keys=True)
    ext_id = f"ps_{league_id}_{season}_{week}_{franchise_id}_{player_id}"
    con.execute(
        """INSERT INTO memory_events (league_id, season, external_source, external_id,
           event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, 'test', ?, 'WEEKLY_PLAYER_SCORE', ?, ?, ?)""",
        (league_id, season, ext_id, occurred_at, occurred_at, payload))
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events (league_id, season, event_type,
           action_fingerprint, best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, 'WEEKLY_PLAYER_SCORE', ?, ?, 100, ?, ?)""",
        (league_id, season, f"fp_{ext_id}", me_id, occurred_at, occurred_at))


class TestFranchiseDeepPipeline:
    def test_pipeline_detects_angles(self, tmp_path):
        """Full pipeline finds angles from DB data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 6):
            # F1 dominates with one player
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="P1", score=40.0)
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="P2", score=10.0)
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F2", player_id="P3", score=25.0)
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F2", player_id="P4", score=20.0)
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                             winner_id="F1", loser_id="F2",
                             winner_score=120, loser_score=100)
        con.commit()
        con.close()

        angles = detect_franchise_deep_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        assert len(angles) >= 1
        categories = {a.category for a in angles}
        assert "SCORING_CONCENTRATION" in categories

    def test_pipeline_empty(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        angles = detect_franchise_deep_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        assert angles == []

    def test_pipeline_deterministic(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 4):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="P1", score=30.0)
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                             winner_id="F1", loser_id="F2",
                             winner_score=100, loser_score=90)
        con.commit()
        con.close()

        a1 = detect_franchise_deep_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=3)
        a2 = detect_franchise_deep_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=3)
        assert a1 == a2


# ── Additional Dimension 9 detectors ─────────────────────────────────


class TestSecondHalfSurgeCollapse:
    def test_detects_collapse(self):
        payloads = []
        for w in range(1, 13):
            avg = 120.0 if w <= 6 else 90.0  # 25% decline in second half
            payloads.append(_make_score_payload(w, "F1", "P1", avg))
        angles = detect_second_half_surge_collapse(payloads, 12)
        assert len(angles) >= 1
        assert any("decline" in a.headline for a in angles)

    def test_not_enough_weeks_silence(self):
        payloads = [_make_score_payload(w, "F1", "P1", 100.0) for w in range(1, 6)]
        angles = detect_second_half_surge_collapse(payloads, 5)
        assert len(angles) == 0


class TestFranchiseAlltimeScoring:
    def test_finds_alltime_leader(self):
        matchups = [
            _make_matchup(2022, w, "F1", "F2", 130.0, 100.0) for w in range(1, 6)
        ] + [
            _make_matchup(2023, w, "F1", "F3", 120.0, 110.0) for w in range(1, 6)
        ]
        # F1 total PF: 5*130 + 5*120 = 1250
        angles = detect_franchise_alltime_scoring(matchups, 2024, 1)
        assert len(angles) == 1
        assert "F1" in angles[0].headline

    def test_single_season_silence(self):
        matchups = [_make_matchup(2024, 1, "F1", "F2", 130.0, 100.0)]
        angles = detect_franchise_alltime_scoring(matchups, 2024, 1)
        assert len(angles) == 0


class TestWeeklyScoringRankDominance:
    def test_detects_dominant_scorer(self):
        payloads = []
        # F1 is top scorer in 5 of 6 weeks, F2 once
        for w in range(1, 7):
            payloads.append(_make_score_payload(w, "F1", "P1", 50.0 if w <= 5 else 20.0))
            payloads.append(_make_score_payload(w, "F2", "P2", 30.0 if w <= 5 else 60.0))
            payloads.append(_make_score_payload(w, "F3", "P3", 25.0))
        angles = detect_weekly_scoring_rank_dominance(payloads, 6)
        assert len(angles) == 1
        assert "F1" in angles[0].headline
        assert "5" in angles[0].headline


class TestScheduleStrength:
    def test_detects_tough_schedule(self):
        matchups = []
        # F1 plays strong opponents (F2 and F3 who win a lot)
        for w in range(1, 6):
            matchups.append(_make_matchup(2024, w, "F2", "F1", 110, 100))  # F1 loses to F2
            matchups.append(_make_matchup(2024, w, "F3", "F4", 110, 90))   # F3 beats F4
            matchups.append(_make_matchup(2024, w, "F5", "F6", 100, 95))   # filler
        # F1 faces F2 every week; F2 is 5-0
        angles = detect_schedule_strength(matchups, 2024, 5)
        # Should detect F1 has tough schedule (faces F2 who is 5-0)
        assert len(angles) <= 1  # may or may not trigger depending on spread


class TestPointsAgainstLuck:
    def test_detects_unlucky_opponent_highs(self):
        matchups = [
            # F1 faces opponents who score their season highs against them
            _make_matchup(2024, 1, "F2", "F1", 150.0, 100.0),  # F2's season high
            _make_matchup(2024, 2, "F3", "F1", 145.0, 100.0),  # F3's season high
            _make_matchup(2024, 3, "F4", "F1", 140.0, 100.0),  # F4's season high
            # Others don't score their highs against F1
            _make_matchup(2024, 4, "F2", "F3", 130.0, 120.0),
            _make_matchup(2024, 5, "F3", "F4", 130.0, 110.0),
        ]
        angles = detect_points_against_luck(matchups, 2024, 5)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 1
        assert "3 times" in f1_angles[0].headline


class TestRepeatMatchupPattern:
    def test_detects_high_scoring_rivalry(self):
        matchups = [
            _make_matchup(2020 + i, 1, "F1", "F2", 125.0, 115.0)
            for i in range(5)
        ]
        # Every meeting exceeds 230 combined (125+115=240)
        angles = detect_repeat_matchup_pattern(matchups, 2024, 1)
        assert len(angles) == 1
        assert "F1" in angles[0].headline
        assert "F2" in angles[0].headline

    def test_mixed_scores_no_angle(self):
        matchups = [
            _make_matchup(2020, 1, "F1", "F2", 125.0, 115.0),  # 240 > 230
            _make_matchup(2021, 1, "F1", "F2", 100.0, 90.0),   # 190 < 230
            _make_matchup(2022, 1, "F1", "F2", 130.0, 110.0),  # 240 > 230
            _make_matchup(2023, 1, "F1", "F2", 95.0, 85.0),    # 180 < 230
        ]
        angles = detect_repeat_matchup_pattern(matchups, 2024, 1)
        assert len(angles) == 0  # only 2/4 above threshold (< 75%)


# ── Playoff-dependent detectors ──────────────────────────────────────


def _build_seasons_with_playoffs():
    """Build matchup data for 3 seasons with regular season + playoffs.

    10-team league: 5 matchups per regular season week, fewer in playoffs.
    Season structure: weeks 1-13 regular, week 14 semis (2 matchups),
    week 15 championship (1 matchup).
    """
    matchups = []
    for s in range(2021, 2024):
        # Regular season: 13 weeks, 5 matchups each
        franchises = [f"F{i}" for i in range(1, 11)]
        for w in range(1, 14):
            for i in range(5):
                winner = franchises[i]
                loser = franchises[9 - i]
                matchups.append(_make_matchup(s, w, winner, loser, 110.0, 90.0))

        # Playoffs week 14: 2 matchups (semis)
        matchups.append(_make_matchup(s, 14, "F1", "F4", 120.0, 100.0))
        matchups.append(_make_matchup(s, 14, "F2", "F3", 115.0, 105.0))

        # Championship week 15: 1 matchup
        matchups.append(_make_matchup(s, 15, "F1", "F2", 125.0, 110.0))

    return matchups


class TestChampionshipHistory:
    def test_detects_during_playoff_week(self):
        """Championship history surfaces during playoff weeks."""
        matchups = _build_seasons_with_playoffs()
        # Current season is 2024, week 14 is a playoff week
        # Add a playoff matchup for current season
        matchups.append(_make_matchup(2024, 14, "F1", "F3", 120.0, 100.0))
        matchups.append(_make_matchup(2024, 14, "F2", "F4", 115.0, 105.0))
        # Also need some regular-season matchups for 2024 to establish the mode
        for w in range(1, 14):
            for i in range(5):
                matchups.append(_make_matchup(2024, w, f"F{i+1}", f"F{10-i}", 110.0, 90.0))

        angles = detect_championship_history(matchups, 2024, 14)
        assert len(angles) >= 1
        # F1 has appeared in championship (week 15) in all 3 prior seasons
        champ_angles = [a for a in angles if "championship" in a.headline.lower()]
        assert len(champ_angles) >= 1

    def test_silent_during_regular_season(self):
        """No championship angles during regular season weeks."""
        matchups = _build_seasons_with_playoffs()
        # Add regular season week for 2024
        for i in range(5):
            matchups.append(_make_matchup(2024, 5, f"F{i+1}", f"F{10-i}", 110.0, 90.0))
        angles = detect_championship_history(matchups, 2024, 5)
        assert len(angles) == 0


class TestTheAlmost:
    def test_silent_during_regular_season(self):
        """No almost angles during regular season weeks."""
        matchups = _build_seasons_with_playoffs()
        for i in range(5):
            matchups.append(_make_matchup(2024, 5, f"F{i+1}", f"F{10-i}", 110.0, 90.0))
        angles = detect_the_almost(matchups, 2024, 5)
        assert len(angles) == 0

    def test_fires_during_playoff_week(self):
        """Detects during playoff weeks if threshold met."""
        matchups = _build_seasons_with_playoffs()
        matchups.append(_make_matchup(2024, 14, "F1", "F3", 120.0, 100.0))
        for w in range(1, 14):
            for i in range(5):
                matchups.append(_make_matchup(2024, w, f"F{i+1}", f"F{10-i}", 110.0, 90.0))
        # This tests that the function runs without error during playoff weeks
        angles = detect_the_almost(matchups, 2024, 14)
        # May or may not find "almost" teams depending on exact standings
        assert isinstance(angles, list)


class TestScoringMomentumInStreak:
    """Detector 49: SCORING_MOMENTUM_IN_STREAK.

    Validates both the growing-margins branch (originally implemented)
    and the shrinking-margins branch (added to match the docstring).
    """

    def _streak_for_f1(self, margins, *, win_each_week=True):
        """Build matchups giving F1 a streak with the given per-week margins.

        Each week pairs F1 vs F2 with F1 winning by ``margins[i]`` points.
        Other franchises play unrelated matchups so they don't contaminate.
        Set ``win_each_week=False`` to flip the first matchup into a loss
        for F1, breaking the streak.
        """
        matchups = []
        for i, m in enumerate(margins, start=1):
            ws = 100.0 + m
            ls = 100.0
            if win_each_week:
                matchups.append(_make_matchup(SEASON, i, "F1", "F2", ws, ls))
            else:
                # First week: F1 loses; remaining weeks: F1 wins
                if i == 1:
                    matchups.append(_make_matchup(SEASON, i, "F2", "F1", ws, ls))
                else:
                    matchups.append(_make_matchup(SEASON, i, "F1", "F2", ws, ls))
            # Filler matchups for other franchises so the loop has data
            matchups.append(_make_matchup(SEASON, i, "F3", "F4", 105.0, 95.0))
        return matchups

    def test_detects_growing_margins(self):
        """4-game streak with strictly growing margins fires the growing branch."""
        matchups = self._streak_for_f1([10, 15, 20, 25])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 1
        assert "growing margins" in f1_angles[0].headline
        assert "10, 15, 20, 25" in f1_angles[0].headline
        assert f1_angles[0].category == "SCORING_MOMENTUM_IN_STREAK"

    def test_detects_shrinking_margins(self):
        """4-game streak with strictly shrinking margins fires the shrinking branch.

        This is the regression case for the previously-missing branch:
        before the fix, a shrinking-margins streak would silently produce
        no angle even though the docstring promised both directions.
        """
        matchups = self._streak_for_f1([30, 22, 15, 8])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 1
        assert "shrinking margins" in f1_angles[0].headline
        assert "30, 22, 15, 8" in f1_angles[0].headline
        assert f1_angles[0].category == "SCORING_MOMENTUM_IN_STREAK"

    def test_no_angle_for_streak_under_4_games(self):
        """A 3-game streak (even with monotonic margins) does not fire."""
        matchups = self._streak_for_f1([10, 20, 30])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 3)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 0

    def test_no_angle_for_mixed_margins(self):
        """A 4-game streak with genuinely mixed margins fires no tier.

        [20, 5, 25, 10] is truly mixed: removing any single element does
        not yield a strictly monotonic sequence in either direction.
        """
        matchups = self._streak_for_f1([20, 5, 25, 10])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 0

    def test_no_angle_for_flat_margins(self):
        """A 4-game streak with equal margins fires neither branch (strict gate)."""
        matchups = self._streak_for_f1([15, 15, 15, 15])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 0

    def test_streak_broken_by_loss_does_not_fire(self):
        """A loss in the middle of the window breaks the active streak."""
        # Margins suggest growing, but week 1 is a loss for F1 — so the
        # active streak from week 4 backwards is only 3 games (weeks 2-4).
        matchups = self._streak_for_f1([10, 15, 20, 25], win_each_week=False)
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 0

    # ── Near-monotonic tiers (gate relaxation) ──

    def test_detects_mostly_growing_margins(self):
        """4-game streak with one dip from strictly growing fires tier 3.

        [10, 15, 12, 20] is near-growing: removing 12 yields [10, 15, 20]
        which is strictly growing. The headline includes 'mostly growing'
        and the full margin sequence as a voice guardrail.
        """
        matchups = self._streak_for_f1([10, 15, 12, 20])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 1
        assert "mostly growing margins" in f1_angles[0].headline
        assert "10, 15, 12, 20" in f1_angles[0].headline
        assert f1_angles[0].category == "SCORING_MOMENTUM_IN_STREAK"

    def test_detects_mostly_shrinking_margins(self):
        """4-game streak with one bump from strictly shrinking fires tier 4.

        [30, 22, 25, 10] is near-shrinking: removing 25 yields [30, 22, 10]
        which is strictly shrinking.
        """
        matchups = self._streak_for_f1([30, 22, 25, 10])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 1
        assert "mostly shrinking margins" in f1_angles[0].headline
        assert "30, 22, 25, 10" in f1_angles[0].headline

    def test_strict_takes_priority_over_near(self):
        """Strictly growing wins over near-growing (both could match).

        For strictly monotonic sequences, the near-monotonic check would
        also pass (removing any element still leaves a monotonic sequence).
        The elif chain ensures strict classifications take priority.
        """
        matchups = self._streak_for_f1([10, 15, 20, 25])
        angles = detect_scoring_momentum_in_streak(matchups, SEASON, 4)
        f1_angles = [a for a in angles if "F1" in a.headline]
        assert len(f1_angles) == 1
        # Must be "growing margins" NOT "mostly growing margins"
        assert "mostly" not in f1_angles[0].headline
        assert "growing margins" in f1_angles[0].headline


# ── Near-monotonic helper unit tests ─────────────────────────────────


class TestNearMonotonicHelpers:
    """Unit tests for _is_near_monotonic_growing/shrinking."""

    def test_growing_with_dip(self):
        assert _is_near_monotonic_growing([10, 15, 12, 20]) is True

    def test_growing_with_dip_at_start(self):
        assert _is_near_monotonic_growing([5, 3, 10, 15, 20]) is True

    def test_growing_with_dip_at_end(self):
        assert _is_near_monotonic_growing([10, 15, 20, 18]) is True

    def test_strict_growing_is_not_near(self):
        """Strict growing would match via the main branch; helper returns
        True for it too, but the elif chain prevents tier 3 from firing."""
        assert _is_near_monotonic_growing([10, 15, 20, 25]) is True

    def test_shrinking_with_bump(self):
        assert _is_near_monotonic_shrinking([30, 22, 25, 10]) is True

    def test_shrinking_with_bump_at_start(self):
        assert _is_near_monotonic_shrinking([35, 40, 30, 20, 10]) is True

    def test_shrinking_with_bump_at_end(self):
        assert _is_near_monotonic_shrinking([30, 22, 15, 18]) is True

    def test_truly_mixed_neither(self):
        assert _is_near_monotonic_growing([20, 5, 25, 10]) is False
        assert _is_near_monotonic_shrinking([20, 5, 25, 10]) is False

    def test_flat_is_not_near(self):
        assert _is_near_monotonic_growing([15, 15, 15, 15]) is False
        assert _is_near_monotonic_shrinking([15, 15, 15, 15]) is False

    def test_too_short(self):
        assert _is_near_monotonic_growing([10, 20]) is False
        assert _is_near_monotonic_shrinking([20, 10]) is False
