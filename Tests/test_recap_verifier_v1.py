"""Tests for Recap Verifier v1 (Categories 1-3: Score, Superlative, Streak).

Exercises each verifier category against synthetic data:

Category 1: SCORE — correct scores pass, wrong/transposed/invented fail
Category 2: SUPERLATIVE — correct season-high/all-time pass, false claims fail
Category 3: STREAK — correct streak counts pass, wrong counts and snap/extend logic fail

Also tests the full verification pipeline and SHAREABLE RECAP extraction.
"""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.core.recaps.verification.recap_verifier_v1 import (
    VerificationFailure,
    VerificationResult,
    _build_reverse_name_map,
    _compute_streaks,
    _extract_nearby_score,
    _extract_shareable_recap,
    _find_nearby_franchise,
    _MatchupFact,
    _resolve_display_name,
    verify_recap_v1,
    verify_scores,
    verify_streaks,
    verify_superlatives,
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
                          player_id, score, is_starter=True):
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = json.dumps({
        "week": week, "franchise_id": franchise_id, "player_id": player_id,
        "score": score, "is_starter": is_starter, "should_start": is_starter,
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


def _insert_franchise(con, *, league_id, season, franchise_id, name):
    con.execute(
        """INSERT OR REPLACE INTO franchise_directory
           (league_id, season, franchise_id, name, updated_at)
           VALUES (?, ?, ?, ?, '2024-01-01T00:00:00Z')""",
        (league_id, season, franchise_id, name))


def _make_matchup(week, winner_id, loser_id, winner_score, loser_score):
    return _MatchupFact(
        week=week, winner_id=winner_id, loser_id=loser_id,
        winner_score=winner_score, loser_score=loser_score,
    )


# ── Unit: extraction helpers ────────────────────────────────────────


class TestExtractShareableRecap:
    def test_extracts_between_delimiters(self):
        text = (
            "Facts block here.\n\n"
            "--- SHAREABLE RECAP ---\n"
            "The actual recap prose.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        assert _extract_shareable_recap(text) == "The actual recap prose."

    def test_returns_full_text_without_delimiters(self):
        text = "Just some recap text without markers."
        assert _extract_shareable_recap(text) == text

    def test_empty_text(self):
        assert _extract_shareable_recap("") == ""

    def test_strips_whitespace(self):
        text = "--- SHAREABLE RECAP ---\n  Hello  \n--- END SHAREABLE RECAP ---"
        assert _extract_shareable_recap(text) == "Hello"


class TestBuildReverseNameMap:
    def test_basic_reverse_mapping(self):
        name_map = {"F1": "Alpha Team", "F2": "Beta Squad"}
        reverse = _build_reverse_name_map(name_map)
        assert reverse["Alpha Team"] == "F1"
        assert reverse["alpha team"] == "F1"
        assert reverse["Beta Squad"] == "F2"
        assert reverse["beta squad"] == "F2"

    def test_empty_map(self):
        assert _build_reverse_name_map({}) == {}


class TestResolveDisplayName:
    def test_resolves_exact_case(self):
        reverse = {"Alpha Team": "F1", "alpha team": "F1"}
        assert _resolve_display_name("F1", reverse) == "Alpha Team"

    def test_fallback_to_id(self):
        assert _resolve_display_name("F99", {}) == "F99"


class TestFindNearbyFranchise:
    def test_finds_preceding_franchise(self):
        text = "Alpha Team put up 120.50 against Beta Squad"
        reverse = {"alpha team": "F1", "beta squad": "F2"}
        # Score "120.50" is at position 18; Alpha Team precedes it
        assert _find_nearby_franchise(text, 18, reverse) == "F1"

    def test_falls_back_to_following_franchise(self):
        text = "The score was 120.50 from Beta Squad"
        reverse = {"beta squad": "F2"}
        # No franchise name before the score — should find Beta Squad after
        assert _find_nearby_franchise(text, 14, reverse) == "F2"

    def test_returns_none_when_no_match(self):
        text = "Someone scored 120.50 this week"
        assert _find_nearby_franchise(text, 15, {}) is None


class TestExtractNearbyScore:
    def test_finds_score_near_keyword(self):
        text = "Alpha scored a season-high 145.30 this week"
        # "season-high" starts around position 16
        result = _extract_nearby_score(text, 16)
        assert result is not None
        assert abs(result - 145.30) < 0.01

    def test_returns_none_when_no_score(self):
        text = "This was the highest score of the season"
        result = _extract_nearby_score(text, 13)
        assert result is None


# ── Unit: Category 1 — Score Verification ────────────────────────────


class TestVerifyScores:
    def _setup(self):
        matchups = [
            _make_matchup(5, "F1", "F2", 130.50, 110.20),
            _make_matchup(5, "F3", "F4", 95.80, 88.40),
        ]
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
            "Gamma Crew": "F3", "gamma crew": "F3",
            "Delta Force": "F4", "delta force": "F4",
        }
        return matchups, reverse

    def test_correct_scores_pass(self):
        matchups, reverse = self._setup()
        text = "Alpha Team put up 130.50 to beat Beta Squad's 110.20."
        failures = verify_scores(text, matchups, 5, reverse)
        assert failures == []

    def test_invented_score_skipped(self):
        """Scores not in any matchup are skipped (likely player/FAAB numbers)."""
        matchups, reverse = self._setup()
        text = "Alpha Team put up 135.50 this week."
        failures = verify_scores(text, matchups, 5, reverse)
        assert failures == []

    def test_wrong_attribution_fails(self):
        """A matchup score attributed to the wrong franchise is flagged."""
        matchups, reverse = self._setup()
        # 95.80 belongs to Gamma Crew but attributed to Alpha Team
        text = "Alpha Team scored 95.80 in a close one."
        failures = verify_scores(text, matchups, 5, reverse)
        assert len(failures) == 1
        assert failures[0].category == "SCORE"

    def test_transposed_score_detected(self):
        matchups, reverse = self._setup()
        # Attributing Beta's score (110.20) to Alpha
        text = "Alpha Team put up 110.20 this week."
        failures = verify_scores(text, matchups, 5, reverse)
        assert len(failures) == 1
        assert failures[0].category == "SCORE"
        assert "130.50" in failures[0].evidence  # shows the correct score

    def test_wrong_franchise_attribution(self):
        matchups, reverse = self._setup()
        # Alpha scored 130.50, not Gamma's 95.80
        text = "Alpha Team scored 95.80 in a tough loss."
        failures = verify_scores(text, matchups, 5, reverse)
        assert len(failures) == 1
        assert failures[0].category == "SCORE"

    def test_skips_low_scores(self):
        """Scores below 40 are likely player/FAAB scores, not matchup scores."""
        matchups, reverse = self._setup()
        text = "Alpha Team picked up a player for 25.00 FAAB."
        failures = verify_scores(text, matchups, 5, reverse)
        assert failures == []

    def test_no_matchups_returns_empty(self):
        text = "Alpha Team scored 130.50."
        reverse = {"alpha team": "F1", "Alpha Team": "F1"}
        failures = verify_scores(text, [], 5, reverse)
        assert failures == []

    def test_score_without_nearby_franchise_skipped(self):
        matchups, reverse = self._setup()
        text = "The final score was 130.50 in a great game."
        # No franchise name near the score — should be skipped, not failed
        failures = verify_scores(text, matchups, 5, {})
        assert failures == []


# ── Unit: Category 2 — Superlative Verification ─────────────────────


class TestVerifySuperlatives:
    def _make_season_matchups(self):
        return [
            _make_matchup(1, "F1", "F2", 120.50, 110.20),
            _make_matchup(2, "F1", "F2", 145.30, 100.10),
            _make_matchup(3, "F1", "F2", 130.00, 95.80),
        ]

    def test_correct_season_high_passes(self):
        matchups = self._make_season_matchups()
        text = "Alpha set a season-high 145.30 in week 2."
        failures = verify_superlatives(text, matchups, None, SEASON, None, None)
        assert failures == []

    def test_false_season_high_fails(self):
        matchups = self._make_season_matchups()
        # Actual season high is 145.30, claiming 150.00
        text = "Alpha set a season-high 150.00 in week 2."
        failures = verify_superlatives(text, matchups, None, SEASON, None, None)
        assert len(failures) == 1
        assert failures[0].category == "SUPERLATIVE"
        assert "145.30" in failures[0].evidence

    def test_correct_season_low_passes(self):
        matchups = self._make_season_matchups()
        text = "Beta hit a season-low 95.80 this week."
        failures = verify_superlatives(text, matchups, None, SEASON, None, None)
        assert failures == []

    def test_false_season_low_fails(self):
        matchups = self._make_season_matchups()
        text = "Beta hit a season-low 85.00 this week."
        failures = verify_superlatives(text, matchups, None, SEASON, None, None)
        assert len(failures) == 1
        assert failures[0].category == "SUPERLATIVE"

    def test_correct_alltime_high_passes(self):
        season = self._make_season_matchups()
        alltime = season + [_make_matchup(1, "F1", "F2", 160.00, 90.00)]
        text = "That 160.00 is the all-time high in league history."
        failures = verify_superlatives(text, season, alltime, SEASON, None, None)
        assert failures == []

    def test_false_alltime_high_fails(self):
        season = self._make_season_matchups()
        alltime = season + [_make_matchup(1, "F1", "F2", 160.00, 90.00)]
        # Claiming 145.30 is the all-time high when 160.00 exists
        text = "That 145.30 is the highest score in league history."
        failures = verify_superlatives(text, season, alltime, SEASON, None, None)
        assert len(failures) == 1
        assert "160.00" in failures[0].evidence

    def test_player_season_high_passes(self):
        matchups = self._make_season_matchups()
        # Player high is 51.85, different from team high
        text = "Josh Allen posted a season-high 51.85."
        failures = verify_superlatives(text, matchups, None, SEASON, 51.85, None)
        assert failures == []

    def test_alltime_player_high_passes(self):
        season = self._make_season_matchups()
        text = "That 61.30 is an all-time record for player scoring."
        failures = verify_superlatives(text, season, season, SEASON, None, 61.30)
        assert failures == []

    def test_no_score_near_superlative_skipped(self):
        matchups = self._make_season_matchups()
        text = "That was the highest score of the season by a mile."
        failures = verify_superlatives(text, matchups, None, SEASON, None, None)
        assert failures == []

    def test_across_n_seasons_pattern(self):
        season = self._make_season_matchups()
        alltime = season + [_make_matchup(1, "F1", "F2", 160.00, 90.00)]
        text = "The 145.30 is the best score across 16 seasons."
        failures = verify_superlatives(text, season, alltime, SEASON, None, None)
        assert len(failures) == 1

    def test_empty_matchups_no_failures(self):
        text = "A season-high 145.30 was posted."
        failures = verify_superlatives(text, [], None, SEASON, None, None)
        # No matchups to compare against — can't verify, no failure
        assert failures == []


# ── Unit: Category 3 — Streak Verification ───────────────────────────


class TestComputeStreaks:
    def test_win_streak(self):
        matchups = [
            _make_matchup(1, "F1", "F2", 120, 100),
            _make_matchup(2, "F1", "F2", 115, 105),
            _make_matchup(3, "F1", "F2", 130, 90),
        ]
        streaks = _compute_streaks(matchups, through_week=3)
        assert streaks["F1"] == 3  # 3-game win streak
        assert streaks["F2"] == -3  # 3-game losing streak

    def test_broken_streak(self):
        matchups = [
            _make_matchup(1, "F1", "F2", 120, 100),
            _make_matchup(2, "F1", "F2", 115, 105),
            _make_matchup(3, "F2", "F1", 130, 90),  # F2 wins
        ]
        streaks = _compute_streaks(matchups, through_week=3)
        assert streaks["F1"] == -1
        assert streaks["F2"] == 1

    def test_through_week_filter(self):
        matchups = [
            _make_matchup(1, "F1", "F2", 120, 100),
            _make_matchup(2, "F1", "F2", 115, 105),
            _make_matchup(3, "F2", "F1", 130, 90),
        ]
        streaks = _compute_streaks(matchups, through_week=2)
        assert streaks["F1"] == 2  # only sees weeks 1-2
        assert streaks["F2"] == -2

    def test_empty_matchups(self):
        assert _compute_streaks([], through_week=5) == {}


class TestVerifyStreaks:
    def _setup(self):
        matchups = [
            _make_matchup(1, "F1", "F2", 120, 100),
            _make_matchup(2, "F1", "F2", 115, 105),
            _make_matchup(3, "F1", "F2", 130, 90),
        ]
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }
        return matchups, reverse

    def test_correct_win_streak_passes(self):
        matchups, reverse = self._setup()
        text = "Alpha Team has won 3 straight games."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert failures == []

    def test_correct_losing_streak_passes(self):
        matchups, reverse = self._setup()
        text = "Beta Squad is on a 3-game losing streak."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert failures == []

    def test_wrong_streak_count_fails(self):
        matchups, reverse = self._setup()
        text = "Alpha Team has won 5 straight games."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert failures[0].category == "STREAK"
        assert "5" in failures[0].claim

    def test_wrong_losing_streak_count_fails(self):
        matchups, reverse = self._setup()
        text = "Beta Squad is on a 5-game losing streak."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert "5" in failures[0].claim

    def test_pre_week_streak_accepted(self):
        """A streak that was snapped this week should still be valid as pre-week."""
        matchups = [
            _make_matchup(1, "F1", "F2", 120, 100),
            _make_matchup(2, "F1", "F2", 115, 105),
            _make_matchup(3, "F2", "F1", 130, 90),  # F1's streak broken
        ]
        reverse = {"Alpha Team": "F1", "alpha team": "F1",
                    "Beta Squad": "F2", "beta squad": "F2"}
        # Claiming the pre-week streak count is still valid
        text = "Alpha Team had won 2 straight before this week."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert failures == []

    def test_snap_losing_streak_correct(self):
        """Team was losing, then won — snapped is correct."""
        matchups = [
            _make_matchup(1, "F2", "F1", 120, 100),  # F1 loses
            _make_matchup(2, "F2", "F1", 115, 105),  # F1 loses
            _make_matchup(3, "F1", "F2", 130, 90),   # F1 wins — snaps streak
        ]
        reverse = {"Alpha Team": "F1", "alpha team": "F1",
                    "Beta Squad": "F2", "beta squad": "F2"}
        text = "Alpha Team snapped their losing streak this week."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert failures == []

    def test_snap_losing_streak_when_no_streak(self):
        """Can't snap a streak that didn't exist."""
        matchups = [
            _make_matchup(1, "F1", "F2", 120, 100),  # F1 wins
            _make_matchup(2, "F1", "F2", 115, 105),  # F1 wins
            _make_matchup(3, "F1", "F2", 130, 90),   # F1 wins
        ]
        reverse = {"Alpha Team": "F1", "alpha team": "F1",
                    "Beta Squad": "F2", "beta squad": "F2"}
        text = "Alpha Team snapped their losing streak."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert "no losing streak" in failures[0].evidence.lower()

    def test_snap_when_actually_extended(self):
        """Team lost again — streak extended, not snapped."""
        matchups = [
            _make_matchup(1, "F2", "F1", 120, 100),
            _make_matchup(2, "F2", "F1", 115, 105),
            _make_matchup(3, "F2", "F1", 130, 90),  # still losing
        ]
        reverse = {"Alpha Team": "F1", "alpha team": "F1",
                    "Beta Squad": "F2", "beta squad": "F2"}
        text = "Alpha Team snapped their losing streak."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert "extended" in failures[0].evidence.lower()

    def test_no_franchise_near_streak_skipped(self):
        matchups, reverse = self._setup()
        text = "Someone has won 5 straight games."
        # No franchise name nearby — should skip, not fail
        failures = verify_streaks(text, matchups, 3, {})
        assert failures == []


# ── Integration: Full pipeline ───────────────────────────────────────


class TestVerifyRecapV1Pipeline:
    def _build_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        # Insert franchises
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Alpha Team")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Beta Squad")

        # Insert 5 weeks of matchups
        # F1 wins weeks 1-4, F2 wins week 5
        for w in range(1, 5):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="F1", loser_id="F2",
                            winner_score=120.00 + w, loser_score=100.00 + w)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=5,
                        winner_id="F2", loser_id="F1",
                        winner_score=135.50, loser_score=110.20)

        con.commit()
        con.close()
        return db_path

    def test_clean_recap_passes(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Beta Squad posted 135.50 to beat Alpha Team's 110.20 in Week 5. "
            "Alpha Team had won 4 straight before this loss.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert result.passed is True
        assert result.hard_failure_count == 0
        assert result.checks_run == 3

    def test_wrong_score_fails(self, tmp_path):
        db_path = self._build_db(tmp_path)
        # Beta Squad actually scored 135.50 — attributing Alpha's 110.20 to Beta
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Beta Squad posted 110.20 to beat Alpha Team.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert result.passed is False
        assert result.hard_failure_count >= 1
        assert any(f.category == "SCORE" for f in result.hard_failures)

    def test_wrong_streak_count_fails(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team had won 6 straight games before the loss to Beta Squad.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert result.passed is False
        assert any(f.category == "STREAK" for f in result.hard_failures)

    def test_false_season_high_fails(self, tmp_path):
        db_path = self._build_db(tmp_path)
        # Actual season high is 135.50 (week 5)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team posted a season-high 145.00 this week.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert result.passed is False
        assert any(f.category == "SUPERLATIVE" for f in result.hard_failures)

    def test_correct_season_high_passes(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Beta Squad posted a season-high 135.50 in Week 5.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        # Should pass — 135.50 IS the season high
        assert result.passed is True

    def test_empty_text_passes(self, tmp_path):
        db_path = self._build_db(tmp_path)
        result = verify_recap_v1("", db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert result.passed is True
        assert result.checks_run == 0

    def test_text_without_delimiters_still_verifies(self, tmp_path):
        db_path = self._build_db(tmp_path)
        # No SHAREABLE RECAP markers — verifier should still work
        # Beta scored 135.50, attributing Alpha's 110.20 to Beta is wrong
        text = "Beta Squad posted 110.20 against Alpha Team."
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert result.passed is False

    def test_result_properties(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Beta Squad posted 135.50.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=5)
        assert isinstance(result, VerificationResult)
        assert isinstance(result.hard_failures, tuple)
        assert isinstance(result.soft_failures, tuple)
        assert result.checks_run == 3


class TestVerifyRecapV1WithPlayerScores:
    """Integration tests with player-level scoring data."""

    def _build_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Alpha Team")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Beta Squad")

        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="F1", loser_id="F2",
                        winner_score=120.50, loser_score=100.20)

        # Player scores — season high is 51.85
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                             franchise_id="F1", player_id="P1", score=51.85)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                             franchise_id="F1", player_id="P2", score=30.00)

        con.commit()
        con.close()
        return db_path

    def test_correct_player_season_high_passes(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Josh Allen posted a season-high 51.85 for Alpha Team.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=1)
        assert result.passed is True

    def test_false_player_season_high_fails(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Josh Allen posted a season-high 55.00 for Alpha Team.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=1)
        assert result.passed is False
        assert any(f.category == "SUPERLATIVE" for f in result.hard_failures)


class TestVerifyRecapV1AllTime:
    """Integration tests with cross-season all-time claims."""

    def _build_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=2023,
                          franchise_id="F1", name="Alpha Team")
        _insert_franchise(con, league_id=LEAGUE, season=2023,
                          franchise_id="F2", name="Beta Squad")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Alpha Team")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Beta Squad")

        # 2023 season — high score of 160.00
        _insert_matchup(con, league_id=LEAGUE, season=2023, week=1,
                        winner_id="F1", loser_id="F2",
                        winner_score=160.00, loser_score=90.00)

        # 2024 season — high score of 135.50
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="F1", loser_id="F2",
                        winner_score=135.50, loser_score=100.20)

        # Player scores across seasons
        _insert_player_score(con, league_id=LEAGUE, season=2023, week=1,
                             franchise_id="F1", player_id="P1", score=61.30)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                             franchise_id="F1", player_id="P1", score=51.85)

        con.commit()
        con.close()
        return db_path

    def test_false_alltime_claim_fails(self, tmp_path):
        """The Josh Allen fabrication case: claiming 51.85 is all-time high
        when 61.30 exists in a prior season."""
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "That 51.85 is the highest individual score in league history.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=1)
        assert result.passed is False
        assert any(f.category == "SUPERLATIVE" for f in result.hard_failures)
        # Evidence should mention the actual all-time high
        assert any("61.30" in f.evidence for f in result.hard_failures)

    def test_correct_alltime_claim_passes(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "The all-time high player score remains 61.30 from last season.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=1)
        assert result.passed is True

    def test_team_alltime_high_passes(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "The 160.00 remains the all-time team scoring record.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=1)
        assert result.passed is True


class TestVerifyRecapV1StreakSnap:
    """Integration tests for the snapped/extended streak error class."""

    def _build_db(self, tmp_path, *, f1_wins_week3=False):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Alpha Team")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Beta Squad")

        # F1 loses weeks 1-2 (2-game losing streak entering week 3)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="F2", loser_id="F1",
                        winner_score=120.00, loser_score=100.00)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=2,
                        winner_id="F2", loser_id="F1",
                        winner_score=115.00, loser_score=105.00)

        # Week 3: either F1 wins (snaps streak) or F2 wins (extends)
        if f1_wins_week3:
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=3,
                            winner_id="F1", loser_id="F2",
                            winner_score=130.00, loser_score=90.00)
        else:
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=3,
                            winner_id="F2", loser_id="F1",
                            winner_score=130.00, loser_score=90.00)

        con.commit()
        con.close()
        return db_path

    def test_snap_when_actually_won(self, tmp_path):
        """F1 won in week 3 → snapping streak is correct."""
        db_path = self._build_db(tmp_path, f1_wins_week3=True)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team snapped their losing streak with a win.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=3)
        assert result.passed is True

    def test_snap_when_actually_lost(self, tmp_path):
        """F1 lost in week 3 → can't snap what's being extended."""
        db_path = self._build_db(tmp_path, f1_wins_week3=False)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team snapped their losing streak this week.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=3)
        assert result.passed is False
        assert any(f.category == "STREAK" for f in result.hard_failures)
        assert any("extended" in f.evidence.lower() for f in result.hard_failures)


# ── Edge cases ───────────────────────────────────────────────────────


class TestEdgeCases:
    def test_both_franchises_nearby_skips_transposition(self):
        """When both matchup franchises appear near a score, skip — can't
        reliably determine attribution in 'X beat Y SCORE' patterns."""
        matchups = [_make_matchup(5, "F1", "F2", 130.50, 110.20)]
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }
        text = (
            "Alpha Team posted 110.20. "
            "Beta Squad hit 130.50."
        )
        score_failures = verify_scores(text, matchups, 5, reverse)
        assert score_failures == []

    def test_solo_franchise_transpositions_detected(self):
        """Genuine transpositions: scores far apart, each near wrong franchise."""
        matchups = [_make_matchup(5, "F1", "F2", 130.50, 110.20)]
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }
        # Scores are >80 chars apart so they won't be pair-verified
        text = (
            "Alpha Team put up 110.20 in what was a really disappointing "
            "performance from a team that had been on a roll all season long. "
            "Meanwhile on the other side of the league, Beta Squad managed "
            "only 130.50 despite having the roster advantage on paper."
        )
        score_failures = verify_scores(text, matchups, 5, reverse)
        assert len(score_failures) == 2

    def test_verification_result_tuple_types(self):
        result = VerificationResult(
            passed=False,
            hard_failures=(
                VerificationFailure("SCORE", "HARD", "x", "y"),
            ),
            soft_failures=(),
            checks_run=3,
        )
        assert result.hard_failure_count == 1
        assert result.soft_failure_count == 0
        assert result.passed is False
