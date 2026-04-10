"""Tests for Player Narrative Angle Detection v1 (Dimensions 1-2).

Exercises each of the 11 player angle detectors against
synthetic player scoring data:

Dimension 1 (short-horizon):
1. PLAYER_HOT_STREAK
2. PLAYER_COLD_STREAK
3. PLAYER_SEASON_HIGH
4. PLAYER_BOOM_BUST
5. PLAYER_BREAKOUT
6. ZERO_POINT_STARTER

Dimension 2 (long-horizon / cross-season):
7. PLAYER_ALLTIME_HIGH
8. PLAYER_FRANCHISE_RECORD
9. CAREER_MILESTONE
10. PLAYER_FRANCHISE_TENURE
11. PLAYER_JOURNEY

Also tests the full detection pipeline and prompt rendering.
"""
from __future__ import annotations

import json
import os
import sqlite3


from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    _PlayerWeekRecord,
    _CrossSeasonRecord,
    _Trade,
    _PlayerDrop,
    _FaabAcquisition,
    _load_season_player_scores,
    _load_all_seasons_player_scores,
    _load_all_seasons_starter_zeros,
    _load_all_matchup_opponents,
    _load_season_trades,
    _load_season_drops,
    _load_season_faab_acquisitions,
    _load_season_drafted_players,
    _build_player_franchise_weeks,
    _ordinal,
    detect_player_hot_streak,
    detect_player_cold_streak,
    detect_player_season_high,
    detect_player_boom_bust,
    detect_player_breakout,
    detect_zero_point_starter,
    detect_player_alltime_high,
    detect_player_franchise_record,
    detect_career_milestone,
    detect_player_franchise_tenure,
    detect_player_journey,
    detect_player_vs_opponent,
    detect_revenge_game,
    detect_player_duel,
    detect_trade_outcome,
    detect_the_one_that_got_away,
    detect_faab_roi,
    detect_faab_franchise_efficiency,
    detect_waiver_dependency,
    detect_player_narrative_angles_v1,
)


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "test_league"
SEASON = 2024


# ── Helpers ──────────────────────────────────────────────────────────


def _fresh_db(tmp_path, name="test.sqlite"):
    """Create a fresh DB from schema.sql."""
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_player_score(con, *, league_id, season, week, franchise_id,
                          player_id, score, is_starter=True, should_start=False):
    """Insert a WEEKLY_PLAYER_SCORE into memory + canonical events."""
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {
        "week": week,
        "franchise_id": franchise_id,
        "player_id": player_id,
        "score": score,
        "is_starter": is_starter,
        "should_start": should_start,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"ps_{league_id}_{season}_{week}_{franchise_id}_{player_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_PLAYER_SCORE",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_PLAYER_SCORE",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


def _make_record(week, franchise_id, player_id, score, is_starter=True):
    """Convenience factory for _PlayerWeekRecord."""
    return _PlayerWeekRecord(
        week=week,
        franchise_id=franchise_id,
        player_id=player_id,
        score=score,
        is_starter=is_starter,
    )


# ── Unit: ordinal helper ────────────────────────────────────────────


class TestOrdinal:
    def test_basic_ordinals(self):
        assert _ordinal(1) == "1st"
        assert _ordinal(2) == "2nd"
        assert _ordinal(3) == "3rd"
        assert _ordinal(4) == "4th"
        assert _ordinal(11) == "11th"
        assert _ordinal(12) == "12th"
        assert _ordinal(13) == "13th"
        assert _ordinal(21) == "21st"
        assert _ordinal(22) == "22nd"
        assert _ordinal(101) == "101st"
        assert _ordinal(111) == "111th"


# ── Unit: index builder ─────────────────────────────────────────────


class TestIndexBuilder:
    def test_groups_by_franchise_player(self):
        records = [
            _make_record(1, "F1", "P1", 20.0),
            _make_record(2, "F1", "P1", 25.0),
            _make_record(1, "F1", "P2", 10.0),
            _make_record(3, "F1", "P1", 30.0),  # week 3 — should be excluded if through_week=2
        ]
        index = _build_player_franchise_weeks(records, through_week=2)
        assert ("F1", "P1") in index
        assert len(index[("F1", "P1")]) == 2  # week 3 excluded
        assert ("F1", "P2") in index
        assert len(index[("F1", "P2")]) == 1

    def test_empty_records(self):
        index = _build_player_franchise_weeks([], through_week=5)
        assert index == {}


# ── Detector 1: PLAYER_HOT_STREAK ───────────────────────────────────


class TestPlayerHotStreak:
    def test_detects_3_week_streak(self):
        """3 consecutive weeks above 25 pts = MINOR."""
        records = [
            _make_record(1, "F1", "P1", 26.0),
            _make_record(2, "F1", "P1", 28.0),
            _make_record(3, "F1", "P1", 30.0),
        ]
        angles = detect_player_hot_streak(records, target_week=3)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_HOT_STREAK"
        assert angles[0].strength == 1  # MINOR
        assert "3 consecutive" in angles[0].headline

    def test_detects_4_week_streak_notable(self):
        """4 consecutive weeks = NOTABLE."""
        records = [_make_record(w, "F1", "P1", 25.0 + w) for w in range(1, 5)]
        angles = detect_player_hot_streak(records, target_week=4)
        assert len(angles) == 1
        assert angles[0].strength == 2  # NOTABLE

    def test_detects_5_week_streak_headline(self):
        """5+ consecutive weeks = HEADLINE."""
        records = [_make_record(w, "F1", "P1", 30.0) for w in range(1, 6)]
        angles = detect_player_hot_streak(records, target_week=5)
        assert len(angles) == 1
        assert angles[0].strength == 3  # HEADLINE

    def test_broken_streak_not_detected(self):
        """A gap below threshold breaks the streak."""
        records = [
            _make_record(1, "F1", "P1", 30.0),
            _make_record(2, "F1", "P1", 10.0),  # breaks streak
            _make_record(3, "F1", "P1", 30.0),
            _make_record(4, "F1", "P1", 30.0),
        ]
        angles = detect_player_hot_streak(records, target_week=4)
        # Streak is only 2 (weeks 3-4), not enough
        assert len(angles) == 0

    def test_non_starters_excluded(self):
        """Bench players don't count toward hot streaks."""
        records = [_make_record(w, "F1", "P1", 30.0, is_starter=False) for w in range(1, 4)]
        angles = detect_player_hot_streak(records, target_week=3)
        assert len(angles) == 0

    def test_below_threshold_no_streak(self):
        """Scores just below threshold produce no angles."""
        records = [_make_record(w, "F1", "P1", 24.9) for w in range(1, 4)]
        angles = detect_player_hot_streak(records, target_week=3)
        assert len(angles) == 0

    def test_missing_week_breaks_streak(self):
        """A week with no data breaks the streak."""
        records = [
            _make_record(1, "F1", "P1", 30.0),
            _make_record(2, "F1", "P1", 30.0),
            # week 3 missing
            _make_record(4, "F1", "P1", 30.0),
        ]
        angles = detect_player_hot_streak(records, target_week=4)
        # Streak is only 1 (week 4 only since week 3 missing)
        assert len(angles) == 0


# ── Detector 2: PLAYER_COLD_STREAK ──────────────────────────────────


class TestPlayerColdStreak:
    def test_detects_3_week_cold_streak(self):
        """3 consecutive weeks under 8 pts = NOTABLE."""
        records = [_make_record(w, "F1", "P1", 5.0) for w in range(1, 4)]
        angles = detect_player_cold_streak(records, target_week=3)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_COLD_STREAK"
        assert angles[0].strength == 2  # NOTABLE

    def test_detects_4_week_cold_streak_headline(self):
        """4+ consecutive weeks under 8 pts = HEADLINE."""
        records = [_make_record(w, "F1", "P1", 3.0) for w in range(1, 5)]
        angles = detect_player_cold_streak(records, target_week=4)
        assert len(angles) == 1
        assert angles[0].strength == 3  # HEADLINE

    def test_good_week_breaks_cold_streak(self):
        """A good score breaks the cold streak."""
        records = [
            _make_record(1, "F1", "P1", 5.0),
            _make_record(2, "F1", "P1", 15.0),  # breaks streak
            _make_record(3, "F1", "P1", 4.0),
            _make_record(4, "F1", "P1", 3.0),
        ]
        angles = detect_player_cold_streak(records, target_week=4)
        assert len(angles) == 0  # only 2 consecutive, not enough

    def test_non_starters_excluded(self):
        """Bench players don't trigger cold streaks."""
        records = [_make_record(w, "F1", "P1", 2.0, is_starter=False) for w in range(1, 4)]
        angles = detect_player_cold_streak(records, target_week=3)
        assert len(angles) == 0


# ── Detector 3: PLAYER_SEASON_HIGH ──────────────────────────────────


class TestPlayerSeasonHigh:
    def test_detects_new_season_high(self):
        """A score higher than all prior weeks = HEADLINE."""
        records = [
            _make_record(1, "F1", "P1", 20.0),
            _make_record(2, "F2", "P2", 25.0),
            _make_record(3, "F1", "P1", 22.0),
            _make_record(4, "F1", "P3", 40.0),  # new season high
        ]
        angles = detect_player_season_high(records, target_week=4)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_SEASON_HIGH"
        assert angles[0].strength == 3
        assert "40.00" in angles[0].headline
        assert "P3" in angles[0].headline

    def test_no_angle_when_not_new_high(self):
        """A score below the existing high produces no angle."""
        records = [
            _make_record(1, "F1", "P1", 50.0),
            _make_record(2, "F2", "P2", 30.0),
        ]
        angles = detect_player_season_high(records, target_week=2)
        assert len(angles) == 0

    def test_week_1_no_angle(self):
        """Week 1 produces no angle — no prior data to compare against."""
        records = [_make_record(1, "F1", "P1", 50.0)]
        angles = detect_player_season_high(records, target_week=1)
        assert len(angles) == 0

    def test_only_starters_considered(self):
        """Bench players should not count for season high."""
        records = [
            _make_record(1, "F1", "P1", 20.0),
            _make_record(2, "F1", "P2", 50.0, is_starter=False),  # bench
        ]
        angles = detect_player_season_high(records, target_week=2)
        assert len(angles) == 0

    def test_tie_for_season_high_no_angle(self):
        """Tying the existing high (not beating it) produces no angle."""
        records = [
            _make_record(1, "F1", "P1", 35.0),
            _make_record(2, "F2", "P2", 35.0),
        ]
        angles = detect_player_season_high(records, target_week=2)
        assert len(angles) == 0


# ── Detector 4: PLAYER_BOOM_BUST ────────────────────────────────────


class TestPlayerBoomBust:
    def test_detects_boom(self):
        """Score >= 2x recent average = boom."""
        records = [
            _make_record(1, "F1", "P1", 15.0),
            _make_record(2, "F1", "P1", 15.0),
            _make_record(3, "F1", "P1", 15.0),
            _make_record(4, "F1", "P1", 15.0),
            _make_record(5, "F1", "P1", 40.0),  # 40/15 = 2.67x
        ]
        angles = detect_player_boom_bust(records, target_week=5)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_BOOM_BUST"
        assert "Boom" in angles[0].detail
        assert angles[0].strength == 1  # MINOR

    def test_detects_bust(self):
        """Score <= 0.3x recent average = bust."""
        records = [
            _make_record(1, "F1", "P1", 20.0),
            _make_record(2, "F1", "P1", 20.0),
            _make_record(3, "F1", "P1", 20.0),
            _make_record(4, "F1", "P1", 20.0),
            _make_record(5, "F1", "P1", 5.0),  # 5/20 = 0.25x
        ]
        angles = detect_player_boom_bust(records, target_week=5)
        assert len(angles) == 1
        assert "Bust" in angles[0].detail

    def test_no_angle_with_insufficient_history(self):
        """Fewer than 4 prior weeks = silence."""
        records = [
            _make_record(1, "F1", "P1", 15.0),
            _make_record(2, "F1", "P1", 15.0),
            _make_record(3, "F1", "P1", 15.0),
            _make_record(4, "F1", "P1", 40.0),  # only 3 prior weeks
        ]
        angles = detect_player_boom_bust(records, target_week=4)
        assert len(angles) == 0

    def test_normal_performance_no_angle(self):
        """Score within normal range produces no angle."""
        records = [
            _make_record(1, "F1", "P1", 15.0),
            _make_record(2, "F1", "P1", 15.0),
            _make_record(3, "F1", "P1", 15.0),
            _make_record(4, "F1", "P1", 15.0),
            _make_record(5, "F1", "P1", 18.0),  # 18/15 = 1.2x — normal
        ]
        angles = detect_player_boom_bust(records, target_week=5)
        assert len(angles) == 0

    def test_bench_players_excluded(self):
        """Bench players on target week don't trigger boom/bust."""
        records = [
            _make_record(1, "F1", "P1", 15.0),
            _make_record(2, "F1", "P1", 15.0),
            _make_record(3, "F1", "P1", 15.0),
            _make_record(4, "F1", "P1", 15.0),
            _make_record(5, "F1", "P1", 40.0, is_starter=False),  # bench
        ]
        angles = detect_player_boom_bust(records, target_week=5)
        assert len(angles) == 0

    def test_low_average_ignored(self):
        """Very low averages (< 1.0) are ignored to avoid division noise."""
        records = [
            _make_record(1, "F1", "P1", 0.5),
            _make_record(2, "F1", "P1", 0.3),
            _make_record(3, "F1", "P1", 0.2),
            _make_record(4, "F1", "P1", 0.1),
            _make_record(5, "F1", "P1", 5.0),
        ]
        angles = detect_player_boom_bust(records, target_week=5)
        assert len(angles) == 0


# ── Detector 5: PLAYER_BREAKOUT ─────────────────────────────────────


class TestPlayerBreakout:
    def test_detects_first_20_plus_game(self):
        """First time a player scores 20+ on a franchise = MINOR breakout."""
        records = [
            _make_record(1, "F1", "P1", 10.0),
            _make_record(2, "F1", "P1", 12.0),
            _make_record(3, "F1", "P1", 25.0),  # first 20+ game
        ]
        angles = detect_player_breakout(records, target_week=3)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_BREAKOUT"
        assert angles[0].strength == 1
        assert "first" in angles[0].headline.lower()

    def test_no_breakout_if_already_done_it(self):
        """If player already scored 20+ before, no breakout angle."""
        records = [
            _make_record(1, "F1", "P1", 22.0),
            _make_record(2, "F1", "P1", 10.0),
            _make_record(3, "F1", "P1", 25.0),
        ]
        angles = detect_player_breakout(records, target_week=3)
        assert len(angles) == 0

    def test_no_breakout_on_first_week(self):
        """First week on a franchise — not a breakout, just a debut."""
        records = [_make_record(1, "F1", "P1", 25.0)]
        angles = detect_player_breakout(records, target_week=1)
        assert len(angles) == 0

    def test_below_threshold_no_breakout(self):
        """Score below 20 doesn't trigger breakout."""
        records = [
            _make_record(1, "F1", "P1", 10.0),
            _make_record(2, "F1", "P1", 18.0),
        ]
        angles = detect_player_breakout(records, target_week=2)
        assert len(angles) == 0

    def test_bench_player_no_breakout(self):
        """Bench players don't trigger breakouts."""
        records = [
            _make_record(1, "F1", "P1", 10.0),
            _make_record(2, "F1", "P1", 25.0, is_starter=False),
        ]
        angles = detect_player_breakout(records, target_week=2)
        assert len(angles) == 0


# ── Detector 6: ZERO_POINT_STARTER ──────────────────────────────────


class TestZeroPointStarter:
    def test_detects_zero_point_starter(self):
        """A starter with 0.00 points = NOTABLE."""
        records = [
            _make_record(1, "F1", "P1", 20.0),
            _make_record(1, "F1", "P2", 0.0),  # zero-point starter
        ]
        angles = detect_zero_point_starter(records, target_week=1)
        assert len(angles) == 1
        assert angles[0].category == "ZERO_POINT_STARTER"
        assert angles[0].strength == 2
        assert "0.00" in angles[0].headline

    def test_bench_zero_not_detected(self):
        """A bench player with 0.00 points is not detected."""
        records = [_make_record(1, "F1", "P1", 0.0, is_starter=False)]
        angles = detect_zero_point_starter(records, target_week=1)
        assert len(angles) == 0

    def test_nonzero_not_detected(self):
        """A starter with > 0 points is not detected."""
        records = [_make_record(1, "F1", "P1", 0.01)]
        angles = detect_zero_point_starter(records, target_week=1)
        assert len(angles) == 0

    def test_historical_context_in_detail(self):
        """All-time zero count appears in detail when provided."""
        records = [_make_record(1, "F1", "P1", 0.0)]
        angles = detect_zero_point_starter(records, target_week=1, alltime_zero_count=4)
        assert len(angles) == 1
        assert "4th" in angles[0].detail

    def test_multiple_zeros_same_week(self):
        """Multiple zero-point starters in the same week are each detected."""
        records = [
            _make_record(1, "F1", "P1", 0.0),
            _make_record(1, "F2", "P2", 0.0),
        ]
        angles = detect_zero_point_starter(records, target_week=1)
        assert len(angles) == 2


# ── Data loading (DB integration) ───────────────────────────────────


class TestDataLoading:
    def test_loads_season_player_scores(self, tmp_path):
        """Load player scores from DB for a season."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=20.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P2", score=15.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F1", player_id="P1", score=25.0)
        con.commit()
        con.close()

        records = _load_season_player_scores(db_path, LEAGUE, SEASON)
        assert len(records) == 3
        # Should be sorted by (week, franchise_id, player_id)
        assert records[0].week == 1
        assert records[0].player_id == "P1"
        assert records[1].player_id == "P2"
        assert records[2].week == 2

    def test_empty_season(self, tmp_path):
        """No data returns empty list."""
        db_path = _fresh_db(tmp_path)
        records = _load_season_player_scores(db_path, LEAGUE, SEASON)
        assert records == []

    def test_loads_alltime_zeros(self, tmp_path):
        """Count all-time zero-point starters across seasons."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Season 2023: 1 zero
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F1", player_id="P1", score=0.0)
        # Season 2024: 2 zeros
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P2", score=0.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F2", player_id="P3", score=0.0)
        # Non-starter zero should not count
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=3,
                              franchise_id="F1", player_id="P4", score=0.0,
                              is_starter=False)
        # Non-zero starter should not count
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=3,
                              franchise_id="F1", player_id="P5", score=5.0)
        con.commit()
        con.close()

        count = _load_all_seasons_starter_zeros(db_path, LEAGUE)
        assert count == 3  # 2023 P1 + 2024 P2 + 2024 P3


# ── Full pipeline (DB integration) ──────────────────────────────────


class TestFullPipeline:
    def _build_hot_streak_scenario(self, tmp_path):
        """Player P1 on franchise F1 scores 30+ for weeks 3-6."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # P1: weeks 1-2 normal, weeks 3-6 hot
        scores = [15.0, 18.0, 30.0, 32.0, 28.0, 35.0]
        for w, s in enumerate(scores, start=1):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="P1", score=s)
        # P2: consistent 20s
        for w in range(1, 7):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="P2", score=20.0)
        con.commit()
        con.close()
        return db_path

    def test_pipeline_detects_angles(self, tmp_path):
        """Full pipeline finds angles from DB data."""
        db_path = self._build_hot_streak_scenario(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        assert len(angles) >= 1
        categories = {a.category for a in angles}
        # Should detect at least a hot streak for P1 (weeks 3-6: 30, 32, 28, 35)
        # Week 5 is 28 (above 25) so 4 consecutive weeks
        assert "PLAYER_HOT_STREAK" in categories

    def test_pipeline_empty_data(self, tmp_path):
        """No data produces no angles."""
        db_path = _fresh_db(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        assert angles == []

    def test_pipeline_deterministic(self, tmp_path):
        """Same inputs produce identical angles."""
        db_path = self._build_hot_streak_scenario(tmp_path)
        a1 = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        a2 = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        assert a1 == a2

    def test_pipeline_sorted_by_strength(self, tmp_path):
        """Result is sorted by strength descending."""
        db_path = self._build_hot_streak_scenario(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        if len(angles) > 1:
            strengths = [a.strength for a in angles]
            assert strengths == sorted(strengths, reverse=True)

    def test_pipeline_zero_point_with_history(self, tmp_path):
        """Zero-point starter includes all-time count in detail."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Prior season zeros
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F1", player_id="P99", score=0.0)
        # Current season: normal scores + one zero
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=20.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F1", player_id="P1", score=0.0)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=2,
        )
        zero_angles = [a for a in angles if a.category == "ZERO_POINT_STARTER"]
        assert len(zero_angles) == 1
        # Should mention the all-time count (2 total: P99 in 2023 + P1 in 2024)
        assert "2nd" in zero_angles[0].detail


# ── Prompt rendering ─────────────────────────────────────────────────



# ══════════════════════════════════════════════════════════════════════
# Phase 2 — Dimension 2: Player Long-Horizon Angles (Detectors 7-11)
# ══════════════════════════════════════════════════════════════════════


def _make_xseason(season, week, franchise_id, player_id, score, is_starter=True):
    """Convenience factory for _CrossSeasonRecord."""
    return _CrossSeasonRecord(
        season=season,
        week=week,
        franchise_id=franchise_id,
        player_id=player_id,
        score=score,
        is_starter=is_starter,
    )


# ── Detector 7: PLAYER_ALLTIME_HIGH ─────────────────────────────────


class TestPlayerAlltimeHigh:
    def test_detects_new_alltime_high(self):
        """A score higher than all prior seasons = HEADLINE."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 45.0),
            _make_xseason(2023, 5, "F2", "P2", 50.0),
            _make_xseason(2024, 3, "F1", "P3", 55.0),  # new all-time high
        ]
        angles = detect_player_alltime_high(records, current_season=2024, target_week=3)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_ALLTIME_HIGH"
        assert angles[0].strength == 3
        assert "55.00" in angles[0].headline
        assert "P3" in angles[0].headline

    def test_no_angle_when_not_new_high(self):
        """Score below prior all-time high produces no angle."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 60.0),
            _make_xseason(2024, 3, "F1", "P2", 50.0),
        ]
        angles = detect_player_alltime_high(records, current_season=2024, target_week=3)
        assert len(angles) == 0

    def test_single_season_no_angle(self):
        """Only 1 season of data = silence (per spec)."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 30.0),
            _make_xseason(2024, 2, "F1", "P1", 50.0),
        ]
        angles = detect_player_alltime_high(records, current_season=2024, target_week=2)
        assert len(angles) == 0

    def test_only_starters_considered(self):
        """Bench scores don't count for all-time high."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 40.0),
            _make_xseason(2024, 3, "F1", "P2", 50.0, is_starter=False),
        ]
        angles = detect_player_alltime_high(records, current_season=2024, target_week=3)
        assert len(angles) == 0

    def test_tie_no_angle(self):
        """Tying the all-time high (not beating it) produces no angle."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 50.0),
            _make_xseason(2024, 3, "F1", "P2", 50.0),
        ]
        angles = detect_player_alltime_high(records, current_season=2024, target_week=3)
        assert len(angles) == 0

    def test_future_weeks_excluded(self):
        """Records from weeks after target_week in current season are excluded."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 40.0),
            _make_xseason(2024, 3, "F1", "P2", 45.0),
            _make_xseason(2024, 5, "F1", "P3", 60.0),  # future week — excluded
        ]
        angles = detect_player_alltime_high(records, current_season=2024, target_week=3)
        assert len(angles) == 1
        assert "45.00" in angles[0].headline


# ── Detector 8: PLAYER_FRANCHISE_RECORD ──────────────────────────────


class TestPlayerFranchiseRecord:
    def test_detects_new_franchise_record(self):
        """A score higher than any prior week on the franchise = NOTABLE."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 35.0),
            _make_xseason(2023, 5, "F1", "P2", 40.0),
            _make_xseason(2024, 3, "F1", "P3", 45.0),  # new franchise record
        ]
        angles = detect_player_franchise_record(
            records, current_season=2024, target_week=3,
        )
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_FRANCHISE_RECORD"
        assert angles[0].strength == 2
        assert "45.00" in angles[0].headline
        assert "F1" in angles[0].headline

    def test_tenure_scoped(self):
        """Tenure scoping limits history to current owner's period."""
        records = [
            _make_xseason(2018, 1, "F1", "P1", 60.0),  # before tenure
            _make_xseason(2022, 1, "F1", "P2", 35.0),   # within tenure
            _make_xseason(2024, 3, "F1", "P3", 40.0),    # new record within tenure
        ]
        angles = detect_player_franchise_record(
            records, current_season=2024, target_week=3,
            tenure_map={"F1": 2021},
        )
        assert len(angles) == 1
        assert "under current ownership" in angles[0].headline
        # The 60.0 from 2018 should be excluded by tenure scoping

    def test_no_angle_when_not_new_record(self):
        """Score below prior franchise high produces no angle."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 50.0),
            _make_xseason(2024, 3, "F1", "P2", 40.0),
        ]
        angles = detect_player_franchise_record(
            records, current_season=2024, target_week=3,
        )
        assert len(angles) == 0

    def test_no_prior_history_no_angle(self):
        """No prior data for the franchise means no record to break."""
        records = [
            _make_xseason(2024, 3, "F1", "P1", 50.0),
        ]
        angles = detect_player_franchise_record(
            records, current_season=2024, target_week=3,
        )
        assert len(angles) == 0

    def test_bench_excluded(self):
        """Bench players don't set franchise records."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 35.0),
            _make_xseason(2024, 3, "F1", "P2", 45.0, is_starter=False),
        ]
        angles = detect_player_franchise_record(
            records, current_season=2024, target_week=3,
        )
        assert len(angles) == 0

    def test_multiple_franchises_independent(self):
        """Each franchise's record is independent."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 35.0),
            _make_xseason(2022, 1, "F2", "P2", 40.0),
            _make_xseason(2024, 3, "F1", "P3", 40.0),  # new F1 record
            _make_xseason(2024, 3, "F2", "P4", 38.0),  # NOT new F2 record
        ]
        angles = detect_player_franchise_record(
            records, current_season=2024, target_week=3,
        )
        assert len(angles) == 1
        assert "F1" in angles[0].franchise_ids


# ── Detector 9: CAREER_MILESTONE ────────────────────────────────────


class TestCareerMilestone:
    def test_crosses_1000_point_milestone_basic(self):
        """Crossing 1000 career points this week = NOTABLE."""
        records = [
            # Prior: 980 total points on F1
            _make_xseason(2021, 1, "F1", "P1", 300.0),
            _make_xseason(2022, 1, "F1", "P1", 350.0),
            _make_xseason(2023, 1, "F1", "P1", 330.0),
            # This week: pushes past 1000
            _make_xseason(2024, 3, "F1", "P1", 25.0),
        ]
        angles = detect_career_milestone(records, current_season=2024, target_week=3)
        assert len(angles) == 1
        assert angles[0].category == "CAREER_MILESTONE"
        assert "1,000" in angles[0].headline
        assert angles[0].strength == 2

    def test_crosses_1000_point_milestone(self):
        """Crossing 1000 career points = NOTABLE, reports 1000 not 500."""
        records = [
            _make_xseason(2020, 1, "F1", "P1", 300.0),
            _make_xseason(2021, 1, "F1", "P1", 350.0),
            _make_xseason(2022, 1, "F1", "P1", 340.0),
            # Prior total: 990. This week: crosses 1000
            _make_xseason(2024, 3, "F1", "P1", 15.0),
        ]
        angles = detect_career_milestone(records, current_season=2024, target_week=3)
        assert len(angles) == 1
        assert "1,000" in angles[0].headline

    def test_no_milestone_below_1000(self):
        """Career total below 1000 = no angle."""
        records = [
            _make_xseason(2023, 1, "F1", "P1", 200.0),
            _make_xseason(2024, 3, "F1", "P1", 20.0),
        ]
        angles = detect_career_milestone(records, current_season=2024, target_week=3)
        assert len(angles) == 0

    def test_already_past_milestone_no_angle(self):
        """Milestone crossed in prior weeks = no angle this week."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 300.0),
            _make_xseason(2023, 1, "F1", "P1", 220.0),  # total 520, below 1000
            _make_xseason(2024, 3, "F1", "P1", 15.0),
        ]
        angles = detect_career_milestone(records, current_season=2024, target_week=3)
        assert len(angles) == 0

    def test_different_franchises_independent(self):
        """Career points are per-franchise, not global."""
        records = [
            _make_xseason(2021, 1, "F1", "P1", 300.0),
            _make_xseason(2022, 1, "F1", "P1", 400.0),
            _make_xseason(2023, 1, "F2", "P1", 300.0),  # different franchise
            _make_xseason(2024, 3, "F1", "P1", 310.0),   # crosses 1000 on F1
        ]
        angles = detect_career_milestone(records, current_season=2024, target_week=3)
        assert len(angles) == 1
        assert "F1" in angles[0].headline


# ── Detector 10: PLAYER_FRANCHISE_TENURE ─────────────────────────────


class TestPlayerFranchiseTenure:
    def test_detects_3_year_tenure(self):
        """Player on same franchise for 3 consecutive seasons = MINOR."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 20.0),
            _make_xseason(2023, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 1, "F1", "P1", 20.0),
        ]
        angles = detect_player_franchise_tenure(records, current_season=2024, target_week=1)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_FRANCHISE_TENURE"
        assert angles[0].strength == 1
        assert "3 consecutive" in angles[0].headline

    def test_only_fires_on_week_1(self):
        """Tenure angles only surface on week 1 to avoid repetition."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 20.0),
            _make_xseason(2023, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 5, "F1", "P1", 20.0),
        ]
        angles = detect_player_franchise_tenure(records, current_season=2024, target_week=5)
        assert len(angles) == 0

    def test_non_consecutive_no_tenure(self):
        """Gap in seasons breaks the consecutive streak."""
        records = [
            _make_xseason(2020, 1, "F1", "P1", 20.0),
            # gap: 2021 missing
            _make_xseason(2022, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 1, "F1", "P1", 20.0),
        ]
        angles = detect_player_franchise_tenure(records, current_season=2024, target_week=1)
        # Streak is only 1 (2024 only, since 2023 missing breaks it from 2022)
        assert len(angles) == 0

    def test_two_year_tenure_no_angle(self):
        """2 consecutive seasons is below the threshold."""
        records = [
            _make_xseason(2023, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 1, "F1", "P1", 20.0),
        ]
        angles = detect_player_franchise_tenure(records, current_season=2024, target_week=1)
        assert len(angles) == 0

    def test_longest_tenure_noted(self):
        """When multiple players qualify, the longest gets extra detail."""
        records = [
            # P1: 3 consecutive seasons
            _make_xseason(2022, 1, "F1", "P1", 20.0),
            _make_xseason(2023, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 1, "F1", "P1", 20.0),
            # P2: 5 consecutive seasons
            _make_xseason(2020, 1, "F2", "P2", 20.0),
            _make_xseason(2021, 1, "F2", "P2", 20.0),
            _make_xseason(2022, 1, "F2", "P2", 20.0),
            _make_xseason(2023, 1, "F2", "P2", 20.0),
            _make_xseason(2024, 1, "F2", "P2", 20.0),
        ]
        angles = detect_player_franchise_tenure(records, current_season=2024, target_week=1)
        assert len(angles) == 2
        p2_angle = [a for a in angles if "P2" in a.headline][0]
        assert "Longest active" in p2_angle.detail

    def test_not_active_current_season_excluded(self):
        """Player not on roster this season doesn't get a tenure angle."""
        records = [
            _make_xseason(2021, 1, "F1", "P1", 20.0),
            _make_xseason(2022, 1, "F1", "P1", 20.0),
            _make_xseason(2023, 1, "F1", "P1", 20.0),
            # P1 not on F1 in 2024
        ]
        angles = detect_player_franchise_tenure(records, current_season=2024, target_week=1)
        assert len(angles) == 0


# ── Detector 11: PLAYER_JOURNEY ──────────────────────────────────────


class TestPlayerJourney:
    def test_detects_3_franchise_journey(self):
        """Player on 3+ different franchises = MINOR."""
        records = [
            _make_xseason(2020, 1, "F1", "P1", 20.0),
            _make_xseason(2021, 1, "F2", "P1", 20.0),
            _make_xseason(2022, 1, "F3", "P1", 20.0),
            _make_xseason(2024, 1, "F3", "P1", 20.0),  # active this week
        ]
        angles = detect_player_journey(records, current_season=2024, target_week=1)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_JOURNEY"
        assert angles[0].strength == 1
        assert "3 different" in angles[0].headline

    def test_only_fires_on_week_1(self):
        """Journey angles only surface on week 1."""
        records = [
            _make_xseason(2020, 1, "F1", "P1", 20.0),
            _make_xseason(2021, 1, "F2", "P1", 20.0),
            _make_xseason(2022, 1, "F3", "P1", 20.0),
            _make_xseason(2024, 5, "F3", "P1", 20.0),
        ]
        angles = detect_player_journey(records, current_season=2024, target_week=5)
        assert len(angles) == 0

    def test_two_franchises_no_journey(self):
        """Only 2 franchises is below the threshold."""
        records = [
            _make_xseason(2020, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 1, "F2", "P1", 20.0),
        ]
        angles = detect_player_journey(records, current_season=2024, target_week=1)
        assert len(angles) == 0

    def test_inactive_player_excluded(self):
        """Player not active this week doesn't get a journey angle."""
        records = [
            _make_xseason(2020, 1, "F1", "P1", 20.0),
            _make_xseason(2021, 1, "F2", "P1", 20.0),
            _make_xseason(2022, 1, "F3", "P1", 20.0),
            # P1 not active in 2024 week 1
        ]
        angles = detect_player_journey(records, current_season=2024, target_week=1)
        assert len(angles) == 0

    def test_franchise_ids_sorted_in_output(self):
        """The franchise_ids tuple should be deterministically sorted."""
        records = [
            _make_xseason(2020, 1, "F3", "P1", 20.0),
            _make_xseason(2021, 1, "F1", "P1", 20.0),
            _make_xseason(2022, 1, "F2", "P1", 20.0),
            _make_xseason(2024, 1, "F2", "P1", 20.0),
        ]
        angles = detect_player_journey(records, current_season=2024, target_week=1)
        assert len(angles) == 1
        assert angles[0].franchise_ids == ("F1", "F2", "F3")


# ── Cross-season data loading (DB integration) ──────────────────────


class TestCrossSeasonDataLoading:
    def test_loads_all_seasons(self, tmp_path):
        """Load player scores across multiple seasons from DB."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_player_score(con, league_id=LEAGUE, season=2022, week=1,
                              franchise_id="F1", player_id="P1", score=20.0)
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F1", player_id="P1", score=25.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=30.0)
        con.commit()
        con.close()

        records = _load_all_seasons_player_scores(db_path, LEAGUE)
        assert len(records) == 3
        assert records[0].season == 2022
        assert records[1].season == 2023
        assert records[2].season == SEASON

    def test_empty_returns_empty(self, tmp_path):
        """No data returns empty list."""
        db_path = _fresh_db(tmp_path)
        records = _load_all_seasons_player_scores(db_path, LEAGUE)
        assert records == []


# ── Full pipeline with Dimension 2 (DB integration) ─────────────────


class TestFullPipelineDimension2:
    def _build_cross_season_scenario(self, tmp_path):
        """Multi-season scenario with known angles:
        - P1 on F1: 2022 (500 pts), 2023 (490 pts), 2024 week 1 (15 pts) = 1005 career
        - P2 on F2: 2023 (best=40), 2024 week 1 (50) = new franchise record
        - P3: F1 in 2020, F2 in 2021, F3 in 2022, F3 in 2024 week 1 = journey
        """
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        # P1: career milestone candidate (crosses 1000 pts on F1 this week)
        # Prior: 500 + 490 = 990. This week: 15 + 990 = 1005. Crosses 1000.
        _insert_player_score(con, league_id=LEAGUE, season=2022, week=1,
                              franchise_id="F1", player_id="P1", score=500.0)
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F1", player_id="P1", score=490.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=15.0)

        # P2: franchise record candidate
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F2", player_id="P2", score=40.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F2", player_id="P2", score=50.0)

        # P3: journey candidate (3 different franchises)
        _insert_player_score(con, league_id=LEAGUE, season=2020, week=1,
                              franchise_id="F1", player_id="P3", score=15.0)
        _insert_player_score(con, league_id=LEAGUE, season=2021, week=1,
                              franchise_id="F2", player_id="P3", score=15.0)
        _insert_player_score(con, league_id=LEAGUE, season=2022, week=1,
                              franchise_id="F3", player_id="P3", score=15.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F3", player_id="P3", score=15.0)

        con.commit()
        con.close()
        return db_path

    def test_detects_career_milestone_via_pipeline(self, tmp_path):
        """Full pipeline detects career milestone from DB data."""
        db_path = self._build_cross_season_scenario(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        milestone_angles = [a for a in angles if a.category == "CAREER_MILESTONE"]
        assert len(milestone_angles) == 1
        assert "P1" in milestone_angles[0].headline
        assert "1,000" in milestone_angles[0].headline

    def test_detects_franchise_record_via_pipeline(self, tmp_path):
        """Full pipeline detects franchise record from DB data."""
        db_path = self._build_cross_season_scenario(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        record_angles = [a for a in angles if a.category == "PLAYER_FRANCHISE_RECORD"]
        assert len(record_angles) == 1
        assert "F2" in record_angles[0].headline

    def test_detects_journey_via_pipeline(self, tmp_path):
        """Full pipeline detects player journey from DB data."""
        db_path = self._build_cross_season_scenario(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        journey_angles = [a for a in angles if a.category == "PLAYER_JOURNEY"]
        assert len(journey_angles) == 1
        assert "P3" in journey_angles[0].headline

    def test_pipeline_deterministic_with_dim2(self, tmp_path):
        """Same inputs produce identical angles across both dimensions."""
        db_path = self._build_cross_season_scenario(tmp_path)
        a1 = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        a2 = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        assert a1 == a2

    def test_pipeline_tenure_map_passed_through(self, tmp_path):
        """Tenure map is respected in the full pipeline."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Old era: high score on F1 before tenure start
        _insert_player_score(con, league_id=LEAGUE, season=2018, week=1,
                              franchise_id="F1", player_id="P1", score=60.0)
        # New era: lower ceiling
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F1", player_id="P2", score=35.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P3", score=40.0)
        con.commit()
        con.close()

        # Without tenure: 40 < 60, no record
        angles_no_tenure = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        records_no_tenure = [a for a in angles_no_tenure if a.category == "PLAYER_FRANCHISE_RECORD"]
        assert len(records_no_tenure) == 0

        # With tenure starting 2022: 40 > 35, new record
        angles_with_tenure = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
            tenure_map={"F1": 2022},
        )
        records_with_tenure = [a for a in angles_with_tenure if a.category == "PLAYER_FRANCHISE_RECORD"]
        assert len(records_with_tenure) == 1
        assert "under current ownership" in records_with_tenure[0].headline

    def test_alltime_high_via_pipeline(self, tmp_path):
        """Full pipeline detects all-time high from multi-season data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_player_score(con, league_id=LEAGUE, season=2022, week=1,
                              franchise_id="F1", player_id="P1", score=45.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F2", player_id="P2", score=50.0)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1,
        )
        alltime_angles = [a for a in angles if a.category == "PLAYER_ALLTIME_HIGH"]
        assert len(alltime_angles) == 1
        assert "50.00" in alltime_angles[0].headline


# ══════════════════════════════════════════════════════════════════════
# Phase 3 — Dimension 3: Player vs. Opponent (Detectors 12-14)
# ══════════════════════════════════════════════════════════════════════


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score):
    """Insert a WEEKLY_MATCHUP_RESULT into memory + canonical events."""
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": False,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"m_{league_id}_{season}_{week}_{winner_id}_{loser_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_MATCHUP_RESULT",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_MATCHUP_RESULT",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


def _make_opponent_index(matchups):
    """Build an opponent index from a list of (season, week, winner, loser) tuples."""
    index = {}
    for season, week, winner, loser in matchups:
        index[(season, week, winner)] = loser
        index[(season, week, loser)] = winner
    return index


# ── Detector 12: PLAYER_VS_OPPONENT ──────────────────────────────────


class TestPlayerVsOpponent:
    def test_detects_dominance(self):
        """Player scoring 30+ in all 3 prior meetings = MINOR."""
        records = [
            # P1 on F1, scoring 35+ in all 3 prior games vs F2
            _make_xseason(2022, 1, "F1", "P1", 35.0),
            _make_xseason(2023, 3, "F1", "P1", 38.0),
            _make_xseason(2023, 10, "F1", "P1", 32.0),
            # This week
            _make_xseason(2024, 5, "F1", "P1", 40.0),
        ]
        opp_index = _make_opponent_index([
            (2022, 1, "F1", "F2"),
            (2023, 3, "F1", "F2"),
            (2023, 10, "F2", "F1"),  # F1 lost this one — still a meeting
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_vs_opponent(records, 2024, 5, opp_index)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_VS_OPPONENT"
        assert "3" in angles[0].headline
        assert "P1" in angles[0].headline

    def test_4_meetings_notable(self):
        """4+ meetings with dominance = NOTABLE."""
        records = [_make_xseason(2020 + i, 1, "F1", "P1", 33.0) for i in range(4)]
        records.append(_make_xseason(2024, 5, "F1", "P1", 35.0))
        opp_index = _make_opponent_index(
            [(2020 + i, 1, "F1", "F2") for i in range(4)] + [(2024, 5, "F1", "F2")]
        )
        angles = detect_player_vs_opponent(records, 2024, 5, opp_index)
        assert len(angles) == 1
        assert angles[0].strength == 2  # NOTABLE

    def test_broken_dominance_no_angle(self):
        """One bad game in the set breaks the dominance pattern."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 35.0),
            _make_xseason(2023, 3, "F1", "P1", 10.0),  # broke pattern
            _make_xseason(2023, 10, "F1", "P1", 35.0),
            _make_xseason(2024, 5, "F1", "P1", 40.0),
        ]
        opp_index = _make_opponent_index([
            (2022, 1, "F1", "F2"),
            (2023, 3, "F1", "F2"),
            (2023, 10, "F1", "F2"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_vs_opponent(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_fewer_than_3_meetings_silence(self):
        """Fewer than 3 prior meetings = silence."""
        records = [
            _make_xseason(2023, 1, "F1", "P1", 35.0),
            _make_xseason(2024, 5, "F1", "P1", 40.0),
        ]
        opp_index = _make_opponent_index([
            (2023, 1, "F1", "F2"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_vs_opponent(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_bench_excluded(self):
        """Bench players don't trigger dominance angles."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 35.0, is_starter=False),
            _make_xseason(2023, 3, "F1", "P1", 38.0, is_starter=False),
            _make_xseason(2023, 10, "F1", "P1", 32.0, is_starter=False),
            _make_xseason(2024, 5, "F1", "P1", 40.0, is_starter=False),
        ]
        opp_index = _make_opponent_index([
            (2022, 1, "F1", "F2"), (2023, 3, "F1", "F2"),
            (2023, 10, "F1", "F2"), (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_vs_opponent(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_different_opponents_independent(self):
        """Dominance is per-opponent, not aggregate."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 35.0),  # vs F2
            _make_xseason(2023, 3, "F1", "P1", 38.0),   # vs F3
            _make_xseason(2023, 10, "F1", "P1", 32.0),  # vs F2
            _make_xseason(2024, 5, "F1", "P1", 40.0),   # vs F2 this week
        ]
        opp_index = _make_opponent_index([
            (2022, 1, "F1", "F2"),
            (2023, 3, "F1", "F3"),  # different opponent
            (2023, 10, "F1", "F2"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_vs_opponent(records, 2024, 5, opp_index)
        # Only 2 prior meetings vs F2 (weeks 2022/1 and 2023/10), not enough
        assert len(angles) == 0


# ── Detector 13: REVENGE_GAME ────────────────────────────────────────


class TestRevengeGame:
    def test_detects_revenge(self):
        """Player scoring against former franchise = MINOR."""
        records = [
            # P1 was on F2 in 2022
            _make_xseason(2022, 1, "F2", "P1", 20.0),
            # P1 now on F1, scoring against F2
            _make_xseason(2024, 5, "F1", "P1", 25.0),
        ]
        opp_index = _make_opponent_index([(2024, 5, "F1", "F2")])
        angles = detect_revenge_game(records, 2024, 5, opp_index)
        assert len(angles) == 1
        assert angles[0].category == "REVENGE_GAME"
        assert "formerly on F2" in angles[0].headline
        assert "25.00" in angles[0].headline

    def test_low_score_no_revenge(self):
        """Score below min_score doesn't trigger revenge angle."""
        records = [
            _make_xseason(2022, 1, "F2", "P1", 20.0),
            _make_xseason(2024, 5, "F1", "P1", 5.0),  # below 15 threshold
        ]
        opp_index = _make_opponent_index([(2024, 5, "F1", "F2")])
        angles = detect_revenge_game(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_never_on_opponent_no_revenge(self):
        """Player never on the opponent's franchise = no revenge."""
        records = [
            _make_xseason(2022, 1, "F3", "P1", 20.0),  # was on F3, not F2
            _make_xseason(2024, 5, "F1", "P1", 25.0),
        ]
        opp_index = _make_opponent_index([(2024, 5, "F1", "F2")])
        angles = detect_revenge_game(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_bench_excluded(self):
        """Bench players don't get revenge angles."""
        records = [
            _make_xseason(2022, 1, "F2", "P1", 20.0),
            _make_xseason(2024, 5, "F1", "P1", 25.0, is_starter=False),
        ]
        opp_index = _make_opponent_index([(2024, 5, "F1", "F2")])
        angles = detect_revenge_game(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_same_franchise_no_revenge(self):
        """Player still on the same franchise is not a revenge game."""
        records = [
            _make_xseason(2022, 1, "F1", "P1", 20.0),
            _make_xseason(2024, 5, "F1", "P1", 25.0),
        ]
        opp_index = _make_opponent_index([(2024, 5, "F1", "F2")])
        # P1 was on F1 before and is still on F1 — not revenge against F2
        angles = detect_revenge_game(records, 2024, 5, opp_index)
        assert len(angles) == 0


# ── Detector 14: PLAYER_DUEL ────────────────────────────────────────


class TestPlayerDuel:
    def test_detects_duel(self):
        """Two players meeting 3+ times head-to-head = MINOR."""
        records = [
            # 3 prior meetings: P1 on F1, P2 on F2
            _make_xseason(2021, 1, "F1", "P1", 30.0),
            _make_xseason(2021, 1, "F2", "P2", 25.0),
            _make_xseason(2022, 5, "F1", "P1", 20.0),
            _make_xseason(2022, 5, "F2", "P2", 28.0),
            _make_xseason(2023, 3, "F1", "P1", 35.0),
            _make_xseason(2023, 3, "F2", "P2", 22.0),
            # This week
            _make_xseason(2024, 5, "F1", "P1", 33.0),
            _make_xseason(2024, 5, "F2", "P2", 27.0),
        ]
        opp_index = _make_opponent_index([
            (2021, 1, "F1", "F2"),
            (2022, 5, "F1", "F2"),
            (2023, 3, "F2", "F1"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_duel(records, 2024, 5, opp_index)
        assert len(angles) == 1
        assert angles[0].category == "PLAYER_DUEL"
        assert "P1" in angles[0].headline
        assert "P2" in angles[0].headline
        # P1 outscored P2 in 2 of 3 meetings (30>25, 35>22, but 20<28)
        assert "2 of 3" in angles[0].headline

    def test_fewer_than_3_meetings_silence(self):
        """Fewer than 3 prior meetings = silence."""
        records = [
            _make_xseason(2023, 3, "F1", "P1", 35.0),
            _make_xseason(2023, 3, "F2", "P2", 22.0),
            _make_xseason(2024, 5, "F1", "P1", 33.0),
            _make_xseason(2024, 5, "F2", "P2", 27.0),
        ]
        opp_index = _make_opponent_index([
            (2023, 3, "F1", "F2"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_duel(records, 2024, 5, opp_index)
        assert len(angles) == 0

    def test_no_duplicate_duels(self):
        """Same duel pair produces only one angle, not two."""
        records = [
            _make_xseason(2021, 1, "F1", "P1", 30.0),
            _make_xseason(2021, 1, "F2", "P2", 25.0),
            _make_xseason(2022, 5, "F1", "P1", 20.0),
            _make_xseason(2022, 5, "F2", "P2", 28.0),
            _make_xseason(2023, 3, "F1", "P1", 35.0),
            _make_xseason(2023, 3, "F2", "P2", 22.0),
            _make_xseason(2024, 5, "F1", "P1", 33.0),
            _make_xseason(2024, 5, "F2", "P2", 27.0),
        ]
        opp_index = _make_opponent_index([
            (2021, 1, "F1", "F2"),
            (2022, 5, "F1", "F2"),
            (2023, 3, "F2", "F1"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_duel(records, 2024, 5, opp_index)
        # Should be exactly 1, not 2 (one from F1's perspective + one from F2's)
        assert len(angles) == 1

    def test_bench_excluded_from_duel(self):
        """Bench players on target week don't participate in duels."""
        records = [
            _make_xseason(2021, 1, "F1", "P1", 30.0),
            _make_xseason(2021, 1, "F2", "P2", 25.0),
            _make_xseason(2022, 5, "F1", "P1", 20.0),
            _make_xseason(2022, 5, "F2", "P2", 28.0),
            _make_xseason(2023, 3, "F1", "P1", 35.0),
            _make_xseason(2023, 3, "F2", "P2", 22.0),
            # P2 benched this week
            _make_xseason(2024, 5, "F1", "P1", 33.0),
            _make_xseason(2024, 5, "F2", "P2", 27.0, is_starter=False),
        ]
        opp_index = _make_opponent_index([
            (2021, 1, "F1", "F2"),
            (2022, 5, "F1", "F2"),
            (2023, 3, "F2", "F1"),
            (2024, 5, "F1", "F2"),
        ])
        angles = detect_player_duel(records, 2024, 5, opp_index)
        assert len(angles) == 0


# ── Matchup opponent loading (DB integration) ───────────────────────


class TestMatchupOpponentLoading:
    def test_loads_opponent_index(self, tmp_path):
        """Build opponent index from DB matchup data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=2024, week=1,
                         winner_id="F1", loser_id="F2",
                         winner_score=120, loser_score=100)
        _insert_matchup(con, league_id=LEAGUE, season=2024, week=1,
                         winner_id="F3", loser_id="F4",
                         winner_score=110, loser_score=95)
        con.commit()
        con.close()

        opp = _load_all_matchup_opponents(db_path, LEAGUE)
        assert opp[(2024, 1, "F1")] == "F2"
        assert opp[(2024, 1, "F2")] == "F1"
        assert opp[(2024, 1, "F3")] == "F4"

    def test_empty_returns_empty(self, tmp_path):
        """No matchup data returns empty dict."""
        db_path = _fresh_db(tmp_path)
        opp = _load_all_matchup_opponents(db_path, LEAGUE)
        assert opp == {}


# ── Full pipeline with Dimension 3 (DB integration) ─────────────────


class TestFullPipelineDimension3:
    def _build_revenge_scenario(self, tmp_path):
        """Scenario: P1 was on F2 in 2023, now on F1 playing against F2."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # P1 was on F2 in 2023
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                              franchise_id="F2", player_id="P1", score=20.0)
        # P1 now on F1 in 2024
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=5,
                              franchise_id="F1", player_id="P1", score=30.0)
        # Also need a player on F2 this week for the matchup to exist
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=5,
                              franchise_id="F2", player_id="P2", score=18.0)
        # Matchup: F1 vs F2
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=5,
                         winner_id="F1", loser_id="F2",
                         winner_score=130, loser_score=100)
        con.commit()
        con.close()
        return db_path

    def test_revenge_via_pipeline(self, tmp_path):
        """Full pipeline detects revenge game from DB data."""
        db_path = self._build_revenge_scenario(tmp_path)
        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        revenge_angles = [a for a in angles if a.category == "REVENGE_GAME"]
        assert len(revenge_angles) == 1
        assert "P1" in revenge_angles[0].headline
        assert "F2" in revenge_angles[0].headline

    def test_duel_via_pipeline(self, tmp_path):
        """Full pipeline detects player duel from DB data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # 3 prior meetings with P1 on F1 and P2 on F2 each time
        for yr in [2021, 2022, 2023]:
            _insert_player_score(con, league_id=LEAGUE, season=yr, week=1,
                                  franchise_id="F1", player_id="P1", score=30.0)
            _insert_player_score(con, league_id=LEAGUE, season=yr, week=1,
                                  franchise_id="F2", player_id="P2", score=25.0)
            _insert_matchup(con, league_id=LEAGUE, season=yr, week=1,
                             winner_id="F1", loser_id="F2",
                             winner_score=130, loser_score=100)
        # This week
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=5,
                              franchise_id="F1", player_id="P1", score=33.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=5,
                              franchise_id="F2", player_id="P2", score=28.0)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=5,
                         winner_id="F1", loser_id="F2",
                         winner_score=130, loser_score=100)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        duel_angles = [a for a in angles if a.category == "PLAYER_DUEL"]
        assert len(duel_angles) == 1
        assert "P1" in duel_angles[0].headline
        assert "P2" in duel_angles[0].headline

    def test_pipeline_deterministic_with_dim3(self, tmp_path):
        """Same inputs produce identical angles across all dimensions."""
        db_path = self._build_revenge_scenario(tmp_path)
        a1 = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        a2 = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        assert a1 == a2


# ══════════════════════════════════════════════════════════════════════
# Phase 4 — Dimension 4: Trade & Transaction Outcomes (Detectors 15-16)
# ══════════════════════════════════════════════════════════════════════


def _insert_transaction(con, *, league_id, season, event_type, franchise_id,
                         players_added_ids="", players_dropped_ids="",
                         occurred_at=None, bid_amount=None):
    """Insert a TRANSACTION_* into memory + canonical events."""
    if occurred_at is None:
        occurred_at = f"{season}-10-01T12:00:00Z"
    payload = {
        "mfl_type": event_type.replace("TRANSACTION_", ""),
        "franchise_id": franchise_id,
        "player_id": "",
        "players_added_ids": players_added_ids,
        "players_dropped_ids": players_dropped_ids,
        "player_ids_involved": "",
        "bid_amount": bid_amount,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"tx_{league_id}_{season}_{franchise_id}_{occurred_at}_{event_type}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, event_type,
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, event_type,
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


def _make_trade(season, franchise_a, franchise_b, gave_a, gave_b,
                occurred_at="2024-10-01T12:00:00Z"):
    """Convenience factory for _Trade.

    ``gave_a`` is the list of player IDs that ``franchise_a`` sent to
    ``franchise_b``; ``gave_b`` is the reverse direction.
    """
    return _Trade(
        season=season,
        franchise_a_id=franchise_a,
        franchise_b_id=franchise_b,
        franchise_a_gave_up=tuple(gave_a),
        franchise_b_gave_up=tuple(gave_b),
        occurred_at=occurred_at,
    )


# ── Detector 15: TRADE_OUTCOME ───────────────────────────────────────


class TestTradeOutcome:
    def test_detects_trade_gap(self):
        """Trade with 20+ point gap = angle produced."""
        records = [
            _make_xseason(2024, w, "F1", "PA", 25.0 + w) for w in range(1, 4)
        ] + [
            _make_xseason(2024, w, "F2", "PB", 8.0 + w) for w in range(1, 4)
        ]
        # F1 gave PB to F2, F2 gave PA to F1 → F1 acquired PA, F2 acquired PB
        trades = [_make_trade(2024, "F1", "F2", ["PB"], ["PA"])]
        angles = detect_trade_outcome(records, trades, 2024, 3)
        assert len(angles) == 1
        assert angles[0].category == "TRADE_OUTCOME"
        assert "PA" in angles[0].headline
        assert "PB" in angles[0].headline

    def test_large_gap_notable(self):
        """Gap >= 40 points = NOTABLE."""
        records = [
            _make_xseason(2024, w, "F1", "PA", 30.0) for w in range(1, 4)
        ] + [
            _make_xseason(2024, w, "F2", "PB", 5.0) for w in range(1, 4)
        ]
        trades = [_make_trade(2024, "F1", "F2", ["PB"], ["PA"])]
        angles = detect_trade_outcome(records, trades, 2024, 3)
        assert len(angles) == 1
        assert angles[0].strength == 2  # NOTABLE (gap = 75)

    def test_small_gap_no_angle(self):
        """Gap < 20 points = no angle."""
        records = [
            _make_xseason(2024, w, "F1", "PA", 20.0) for w in range(1, 4)
        ] + [
            _make_xseason(2024, w, "F2", "PB", 18.0) for w in range(1, 4)
        ]
        trades = [_make_trade(2024, "F1", "F2", ["PB"], ["PA"])]
        angles = detect_trade_outcome(records, trades, 2024, 3)
        assert len(angles) == 0

    def test_insufficient_weeks_silence(self):
        """Fewer than 3 post-trade weeks = silence."""
        records = [
            _make_xseason(2024, 1, "F1", "PA", 30.0),
            _make_xseason(2024, 2, "F1", "PA", 30.0),
            _make_xseason(2024, 1, "F2", "PB", 5.0),
            _make_xseason(2024, 2, "F2", "PB", 5.0),
        ]
        trades = [_make_trade(2024, "F1", "F2", ["PB"], ["PA"])]
        angles = detect_trade_outcome(records, trades, 2024, 2)
        assert len(angles) == 0

    def test_empty_trades_no_angle(self):
        """No trades = no angles."""
        angles = detect_trade_outcome([], [], 2024, 5)
        assert len(angles) == 0


# ── Detector 16: THE_ONE_THAT_GOT_AWAY ──────────────────────────────


class TestTheOneThatGotAway:
    def test_detects_productive_drop(self):
        """Dropped player scoring 50+ on another franchise = MINOR."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 10.0),
            _make_xseason(2024, 2, "F1", "P1", 8.0),
            _make_xseason(2024, 4, "F2", "P1", 18.0),
            _make_xseason(2024, 5, "F2", "P1", 20.0),
            _make_xseason(2024, 6, "F2", "P1", 15.0),
        ]
        drops = [_PlayerDrop(season=2024, franchise_id="F1", player_id="P1",
                              occurred_at="2024-10-03T12:00:00Z")]
        angles = detect_the_one_that_got_away(records, drops, 2024, 7)
        assert len(angles) == 1
        assert angles[0].category == "THE_ONE_THAT_GOT_AWAY"
        assert "P1" in angles[0].headline
        assert "F1" in angles[0].headline

    def test_low_production_no_angle(self):
        """Dropped player scoring under 50 = no angle."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 10.0),
            _make_xseason(2024, 4, "F2", "P1", 10.0),
            _make_xseason(2024, 5, "F2", "P1", 10.0),
            _make_xseason(2024, 6, "F2", "P1", 10.0),
        ]
        drops = [_PlayerDrop(season=2024, franchise_id="F1", player_id="P1",
                              occurred_at="2024-10-03T12:00:00Z")]
        angles = detect_the_one_that_got_away(records, drops, 2024, 7)
        assert len(angles) == 0

    def test_insufficient_weeks_silence(self):
        """Fewer than 3 post-drop weeks = silence."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 10.0),
            _make_xseason(2024, 4, "F2", "P1", 30.0),
            _make_xseason(2024, 5, "F2", "P1", 30.0),
        ]
        drops = [_PlayerDrop(season=2024, franchise_id="F1", player_id="P1",
                              occurred_at="2024-10-03T12:00:00Z")]
        angles = detect_the_one_that_got_away(records, drops, 2024, 5)
        assert len(angles) == 0

    def test_duplicate_drops_single_angle(self):
        """Same player dropped multiple times produces one angle."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 10.0),
            _make_xseason(2024, 4, "F2", "P1", 20.0),
            _make_xseason(2024, 5, "F2", "P1", 18.0),
            _make_xseason(2024, 6, "F2", "P1", 22.0),
        ]
        drops = [
            _PlayerDrop(season=2024, franchise_id="F1", player_id="P1",
                         occurred_at="2024-10-03T12:00:00Z"),
            _PlayerDrop(season=2024, franchise_id="F1", player_id="P1",
                         occurred_at="2024-10-04T12:00:00Z"),
        ]
        angles = detect_the_one_that_got_away(records, drops, 2024, 7)
        assert len(angles) == 1

    def test_empty_drops_no_angle(self):
        """No drops = no angles."""
        angles = detect_the_one_that_got_away([], [], 2024, 5)
        assert len(angles) == 0


# ── Transaction loading (DB integration) ─────────────────────────────


def _insert_trade_event(con, *, league_id, season, franchise_a, franchise_b,
                        gave_a, gave_b, occurred_at=None, _suffix=""):
    """Insert a TRANSACTION_TRADE event mirroring the real MFL payload shape.

    The structured ``players_added_ids`` / ``players_dropped_ids`` fields
    are emitted empty (matching what the canonicalize layer produces for
    trade events). The actual player IDs live inside ``raw_mfl_json``
    under ``franchise1_gave_up`` and ``franchise2_gave_up``.

    ``_suffix`` is appended to the external ID for tests that need
    multiple canonical rows for the same logical trade (deduplication).
    """
    if occurred_at is None:
        occurred_at = f"{season}-10-01T12:00:00Z"

    raw_inner = json.dumps({
        "comments": "",
        "expires": "0",
        "franchise": franchise_a,
        "franchise2": franchise_b,
        "franchise1_gave_up": ",".join(gave_a) + ("," if gave_a else ""),
        "franchise2_gave_up": ",".join(gave_b) + ("," if gave_b else ""),
        "timestamp": "0",
        "type": "TRADE",
    }, sort_keys=True)

    payload = {
        "mfl_type": "TRADE",
        "franchise_id": franchise_a,
        "player_id": None,
        "players_added_ids": [],
        "players_dropped_ids": [],
        "player_ids_involved": [],
        "bid_amount": None,
        "raw_mfl_json": raw_inner,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"trade_{league_id}_{season}_{franchise_a}_{franchise_b}_{occurred_at}{_suffix}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "TRANSACTION_TRADE",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "TRANSACTION_TRADE",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


class TestTransactionLoading:
    def test_loads_trades_from_raw_mfl_json(self, tmp_path):
        """Loader reads player IDs from raw_mfl_json, not structured fields.

        This is the key regression test for the trade-loader bug: the old
        loader read empty structured fields and silently dropped every
        trade event. The new loader reads from raw_mfl_json where MFL
        actually puts the player IDs.
        """
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_trade_event(con, league_id=LEAGUE, season=SEASON,
                            franchise_a="F1", franchise_b="F2",
                            gave_a=["PA"], gave_b=["PB"],
                            occurred_at="2024-10-01T12:00:00Z")
        con.commit()
        con.close()

        trades = _load_season_trades(db_path, LEAGUE, SEASON)
        assert len(trades) == 1
        t = trades[0]
        assert t.franchise_a_id == "F1"
        assert t.franchise_b_id == "F2"
        assert "PA" in t.franchise_a_gave_up
        assert "PB" in t.franchise_b_gave_up

    def test_deduplicates_canonical_duplicates(self, tmp_path):
        """Multiple canonical rows for the same logical trade collapse to one.

        Production data shows 3 canonical rows per logical trade (the
        canonicalize layer surfaces multiple representations). The loader
        deduplicates on (occurred_at, frozenset({franchise_a, franchise_b})).
        """
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        ts = "2024-10-01T12:00:00Z"
        for i in range(3):
            _insert_trade_event(con, league_id=LEAGUE, season=SEASON,
                                franchise_a="F1", franchise_b="F2",
                                gave_a=["PA"], gave_b=["PB"],
                                occurred_at=ts, _suffix=f"_{i}")
        con.commit()
        con.close()

        trades = _load_season_trades(db_path, LEAGUE, SEASON)
        assert len(trades) == 1  # deduplicated from 3 rows

    def test_self_trade_discarded(self, tmp_path):
        """A trade where franchise == franchise2 is silently discarded."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_trade_event(con, league_id=LEAGUE, season=SEASON,
                            franchise_a="F1", franchise_b="F1",
                            gave_a=["PA"], gave_b=["PB"])
        con.commit()
        con.close()

        trades = _load_season_trades(db_path, LEAGUE, SEASON)
        assert len(trades) == 0

    def test_loads_drops(self, tmp_path):
        """Load drop records from various transaction types."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_transaction(con, league_id=LEAGUE, season=SEASON,
                             event_type="TRANSACTION_FREE_AGENT",
                             franchise_id="F1",
                             players_added_ids="PA",
                             players_dropped_ids="PB",
                             occurred_at="2024-10-01T12:00:00Z")
        _insert_transaction(con, league_id=LEAGUE, season=SEASON,
                             event_type="TRANSACTION_TRADE",
                             franchise_id="F2",
                             players_added_ids="PB",
                             players_dropped_ids="PC,PD",
                             occurred_at="2024-10-02T12:00:00Z")
        con.commit()
        con.close()

        drops = _load_season_drops(db_path, LEAGUE, SEASON)
        dropped_ids = {d.player_id for d in drops}
        assert "PB" in dropped_ids
        assert "PC" in dropped_ids
        assert "PD" in dropped_ids


# ── Full pipeline with Dimension 4 (DB integration) ─────────────────


class TestFullPipelineDimension4:
    def test_trade_outcome_via_pipeline(self, tmp_path):
        """Full pipeline detects trade outcome from DB data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        ts = "2024-09-15T12:00:00Z"
        # F1 gave PB to F2, F2 gave PA to F1
        _insert_trade_event(con, league_id=LEAGUE, season=SEASON,
                            franchise_a="F1", franchise_b="F2",
                            gave_a=["PB"], gave_b=["PA"],
                            occurred_at=ts)
        for w in range(1, 6):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="PA", score=25.0)
        for w in range(1, 6):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F2", player_id="PB", score=8.0)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        trade_angles = [a for a in angles if a.category == "TRADE_OUTCOME"]
        assert len(trade_angles) == 1
        assert "PA" in trade_angles[0].headline
        assert "PB" in trade_angles[0].headline

    def test_got_away_via_pipeline(self, tmp_path):
        """Full pipeline detects the one that got away from DB data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_transaction(con, league_id=LEAGUE, season=SEASON,
                             event_type="TRANSACTION_FREE_AGENT",
                             franchise_id="F1",
                             players_added_ids="PX",
                             players_dropped_ids="P1",
                             occurred_at="2024-10-03T12:00:00Z")
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=8.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F1", player_id="P1", score=6.0)
        for w in range(4, 8):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F2", player_id="P1", score=18.0)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=7,
        )
        away_angles = [a for a in angles if a.category == "THE_ONE_THAT_GOT_AWAY"]
        assert len(away_angles) == 1
        assert "P1" in away_angles[0].headline
        assert "F1" in away_angles[0].headline


# ══════════════════════════════════════════════════════════════════════
# Phase 5 — Dimension 5: FAAB & Waiver Efficiency (Detectors 17-19)
# ══════════════════════════════════════════════════════════════════════


def _insert_faab_award(con, *, league_id, season, franchise_id, player_id,
                        bid_amount, occurred_at=None):
    """Insert a WAIVER_BID_AWARDED event."""
    if occurred_at is None:
        occurred_at = f"{season}-10-05T12:00:00Z"
    payload = {
        "franchise_id": franchise_id,
        "player_id": player_id,
        "bid_amount": bid_amount,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"faab_{league_id}_{season}_{franchise_id}_{player_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WAIVER_BID_AWARDED",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WAIVER_BID_AWARDED",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


def _insert_draft_pick(con, *, league_id, season, franchise_id, player_id,
                         bid_amount=None):
    """Insert a DRAFT_PICK event."""
    occurred_at = f"{season}-09-01T12:00:00Z"
    payload = {
        "mfl_type": "AUCTION_INIT",
        "franchise_id": franchise_id,
        "player_id": player_id,
        "bid_amount": bid_amount,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"dp_{league_id}_{season}_{franchise_id}_{player_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "DRAFT_PICK",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "DRAFT_PICK",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


# ── Detector 17: FAAB_ROI_NOTABLE ───────────────────────────────────


class TestFaabRoi:
    def test_detects_high_roi(self):
        """FAAB pickup scoring 3x+ bid = NOTABLE."""
        records = [
            _make_xseason(2024, w, "F1", "P1", 12.0) for w in range(1, 5)
        ]
        faab = [_FaabAcquisition(season=2024, franchise_id="F1",
                                  player_id="P1", bid_amount=10.0)]
        # Total: 48 pts, 4.8x the $10 bid
        angles = detect_faab_roi(records, faab, 2024, 4)
        assert len(angles) == 1
        assert angles[0].category == "FAAB_ROI_NOTABLE"
        assert angles[0].strength == 2
        assert "P1" in angles[0].headline
        assert "$10" in angles[0].headline

    def test_low_roi_no_angle(self):
        """FAAB pickup scoring < 3x bid = no angle."""
        records = [
            _make_xseason(2024, w, "F1", "P1", 5.0) for w in range(1, 4)
        ]
        faab = [_FaabAcquisition(season=2024, franchise_id="F1",
                                  player_id="P1", bid_amount=10.0)]
        # Total: 15 pts, 1.5x the $10 bid — below 3x
        angles = detect_faab_roi(records, faab, 2024, 3)
        assert len(angles) == 0

    def test_insufficient_weeks_silence(self):
        """Fewer than 3 weeks = silence."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 50.0),
            _make_xseason(2024, 2, "F1", "P1", 50.0),
        ]
        faab = [_FaabAcquisition(season=2024, franchise_id="F1",
                                  player_id="P1", bid_amount=5.0)]
        angles = detect_faab_roi(records, faab, 2024, 2)
        assert len(angles) == 0

    def test_empty_faab_no_angle(self):
        angles = detect_faab_roi([], [], 2024, 5)
        assert len(angles) == 0


# ── Detector 18: FAAB_FRANCHISE_EFFICIENCY ───────────────────────────


class TestFaabFranchiseEfficiency:
    def test_detects_top_franchise(self):
        """Franchise with 1.5x+ league average FAAB production = MINOR."""
        records = [
            # F1's FAAB pickup P1 scores a lot
            _make_xseason(2024, w, "F1", "P1", 20.0) for w in range(1, 6)
        ] + [
            # F2's FAAB pickup P2 scores modestly
            _make_xseason(2024, w, "F2", "P2", 5.0) for w in range(1, 6)
        ] + [
            # F3's FAAB pickup P3 scores modestly
            _make_xseason(2024, w, "F3", "P3", 6.0) for w in range(1, 6)
        ]
        faab = [
            _FaabAcquisition(season=2024, franchise_id="F1", player_id="P1", bid_amount=20.0),
            _FaabAcquisition(season=2024, franchise_id="F2", player_id="P2", bid_amount=15.0),
            _FaabAcquisition(season=2024, franchise_id="F3", player_id="P3", bid_amount=10.0),
        ]
        # F1: 100 pts, F2: 25 pts, F3: 30 pts. Avg: ~51.7. F1 is ~1.9x avg.
        angles = detect_faab_franchise_efficiency(records, faab, 2024, 5)
        assert len(angles) == 1
        assert angles[0].category == "FAAB_FRANCHISE_EFFICIENCY"
        assert "F1" in angles[0].headline

    def test_close_production_no_angle(self):
        """All franchises near the average = no angle."""
        records = [
            _make_xseason(2024, w, "F1", "P1", 10.0) for w in range(1, 4)
        ] + [
            _make_xseason(2024, w, "F2", "P2", 10.0) for w in range(1, 4)
        ] + [
            _make_xseason(2024, w, "F3", "P3", 10.0) for w in range(1, 4)
        ]
        faab = [
            _FaabAcquisition(season=2024, franchise_id="F1", player_id="P1", bid_amount=10.0),
            _FaabAcquisition(season=2024, franchise_id="F2", player_id="P2", bid_amount=10.0),
            _FaabAcquisition(season=2024, franchise_id="F3", player_id="P3", bid_amount=10.0),
        ]
        angles = detect_faab_franchise_efficiency(records, faab, 2024, 3)
        assert len(angles) == 0  # all equal, leader is 1.0x avg

    def test_fewer_than_3_franchises_silence(self):
        """Need 3+ franchises with FAAB data."""
        records = [_make_xseason(2024, 1, "F1", "P1", 50.0)]
        faab = [_FaabAcquisition(season=2024, franchise_id="F1", player_id="P1", bid_amount=5.0)]
        angles = detect_faab_franchise_efficiency(records, faab, 2024, 1)
        assert len(angles) == 0


# ── Detector 19: WAIVER_DEPENDENCY ───────────────────────────────────


class TestWaiverDependency:
    def test_detects_high_dependency(self):
        """30%+ scoring from non-drafted starters = MINOR."""
        records = [
            # Drafted player P1: 70 pts
            _make_xseason(2024, 1, "F1", "P1", 35.0),
            _make_xseason(2024, 2, "F1", "P1", 35.0),
            # Non-drafted player P2: 40 pts
            _make_xseason(2024, 1, "F1", "P2", 20.0),
            _make_xseason(2024, 2, "F1", "P2", 20.0),
        ]
        drafted = {"F1": {"P1"}}  # only P1 was drafted
        # P2 is non-drafted: 40/110 = 36%
        angles = detect_waiver_dependency(records, drafted, 2024, 2)
        assert len(angles) == 1
        assert angles[0].category == "WAIVER_DEPENDENCY"
        assert "F1" in angles[0].headline
        assert "36%" in angles[0].headline

    def test_low_dependency_no_angle(self):
        """Under 30% non-drafted scoring = no angle."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 80.0),  # drafted
            _make_xseason(2024, 1, "F1", "P2", 10.0),   # non-drafted
        ]
        drafted = {"F1": {"P1"}}
        # P2 is non-drafted: 10/90 = 11%
        angles = detect_waiver_dependency(records, drafted, 2024, 1)
        assert len(angles) == 0

    def test_no_draft_data_silence(self):
        """No draft data = silence."""
        records = [_make_xseason(2024, 1, "F1", "P1", 50.0)]
        angles = detect_waiver_dependency(records, {}, 2024, 1)
        assert len(angles) == 0

    def test_bench_excluded(self):
        """Bench players don't count toward dependency ratio."""
        records = [
            _make_xseason(2024, 1, "F1", "P1", 50.0),  # drafted starter
            _make_xseason(2024, 1, "F1", "P2", 40.0, is_starter=False),  # non-drafted bench
        ]
        drafted = {"F1": {"P1"}}
        angles = detect_waiver_dependency(records, drafted, 2024, 1)
        assert len(angles) == 0  # bench excluded, 0% non-drafted starters


# ── FAAB/draft loading (DB integration) ──────────────────────────────


class TestFaabDraftLoading:
    def test_loads_faab_acquisitions(self, tmp_path):
        """Load FAAB awards from DB."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_faab_award(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F1", player_id="P1", bid_amount=25.0)
        _insert_faab_award(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F2", player_id="P2", bid_amount=10.0)
        con.commit()
        con.close()

        acqs = _load_season_faab_acquisitions(db_path, LEAGUE, SEASON)
        assert len(acqs) == 2
        assert acqs[0].franchise_id == "F1"
        assert acqs[0].bid_amount == 25.0

    def test_loads_drafted_players(self, tmp_path):
        """Load drafted players per franchise from DB."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_draft_pick(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F1", player_id="P1", bid_amount=50.0)
        _insert_draft_pick(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F1", player_id="P2", bid_amount=20.0)
        _insert_draft_pick(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F2", player_id="P3", bid_amount=30.0)
        con.commit()
        con.close()

        drafted = _load_season_drafted_players(db_path, LEAGUE, SEASON)
        assert "P1" in drafted["F1"]
        assert "P2" in drafted["F1"]
        assert "P3" in drafted["F2"]

    def test_empty_returns_empty(self, tmp_path):
        """No data returns empty structures."""
        db_path = _fresh_db(tmp_path)
        assert _load_season_faab_acquisitions(db_path, LEAGUE, SEASON) == []
        assert _load_season_drafted_players(db_path, LEAGUE, SEASON) == {}


# ── Full pipeline with Dimension 5 (DB integration) ─────────────────


class TestFullPipelineDimension5:
    def test_faab_roi_via_pipeline(self, tmp_path):
        """Full pipeline detects FAAB ROI from DB data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_faab_award(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F1", player_id="P1", bid_amount=10.0)
        for w in range(1, 5):
            _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=w,
                                  franchise_id="F1", player_id="P1", score=15.0)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=4,
        )
        roi_angles = [a for a in angles if a.category == "FAAB_ROI_NOTABLE"]
        assert len(roi_angles) == 1
        assert "P1" in roi_angles[0].headline

    def test_waiver_dependency_via_pipeline(self, tmp_path):
        """Full pipeline detects waiver dependency from DB data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Draft P1 for F1
        _insert_draft_pick(con, league_id=LEAGUE, season=SEASON,
                            franchise_id="F1", player_id="P1", bid_amount=50.0)
        # P1 (drafted) scores 60
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=30.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F1", player_id="P1", score=30.0)
        # P2 (not drafted) scores 50
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P2", score=25.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=2,
                              franchise_id="F1", player_id="P2", score=25.0)
        con.commit()
        con.close()

        angles = detect_player_narrative_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=2,
        )
        dep_angles = [a for a in angles if a.category == "WAIVER_DEPENDENCY"]
        # P2 non-drafted: 50/(60+50) = 45%
        assert len(dep_angles) == 1
        assert "45%" in dep_angles[0].headline


