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
    verify_banned_phrases,
    verify_cross_week_consistency,
    verify_recap_v1,
    verify_scores,
    verify_series_records,
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

    # ── Possessive-object attribution (backlog B, row 20 pattern) ────
    # When the snap clause names the streak owner as a possessor
    # ("X snapped Y's losing streak"), attribute to the possessor Y
    # directly — the proximity heuristic otherwise misattributes when
    # the subject X has a short first name absent from the alias map.

    def test_snap_possessive_object_row20_pattern(self):
        """Verbatim row 20 prose: 'Ben snapped Brandon's 11-game losing streak...'

        Ben's Gods' first word is "ben" (3 chars, below 5-char alias
        threshold). Under the pre-fix attribution heuristic, pass-1
        before "snapped" found nothing and pass-2 picked up "brandon"
        inside the snap clause — producing a failure citing Brandon
        Knows Ball as the snap-claim subject. With possessive-object
        attribution, Brandon is correctly identified as the streak
        owner and the failure explicitly frames it that way.
        """
        # F_BEN beat F_BRANDON in w11. Brandon lost weeks 1-10 (to
        # OTHER) and loses w11 to Ben — pre-week streak -10, current -11.
        matchups = []
        for w in range(1, 11):
            matchups.append(_make_matchup(w, "OTHER", "F_BRANDON", 120, 90))
        matchups.append(_make_matchup(11, "F_BEN", "F_BRANDON", 111.60, 104.15))
        reverse = {
            "Ben's Gods": "F_BEN", "ben's gods": "F_BEN",
            "Brandon Knows Ball": "F_BRANDON",
            "brandon knows ball": "F_BRANDON",
            "brandon": "F_BRANDON",  # 7-char first-word alias (built in prod)
            "Other Team": "OTHER", "other team": "OTHER",
        }
        text = (
            "Ben snapped Brandon's 11-game losing streak with a "
            "111.60-104.15 victory, though Brandon actually put up "
            "his best score in weeks."
        )
        failures = verify_streaks(text, matchups, 11, reverse)
        assert len(failures) == 1
        # The failure must cite Brandon as the streak owner, not as the
        # snap-claim subject — that's the correction backlog B targets.
        assert "Brandon Knows Ball" in failures[0].claim
        assert "losing streak was snapped" in failures[0].claim
        assert "extended to 11" in failures[0].evidence
        assert "not snapped" in failures[0].evidence

    def test_snap_possessive_object_multiword_franchise(self):
        """Possessor is a multi-word franchise name — still attributable."""
        matchups = [
            _make_matchup(1, "F_OTHER", "F_ITCAV", 120, 100),
            _make_matchup(2, "F_OTHER", "F_ITCAV", 115, 105),
            _make_matchup(3, "F_WINNER", "F_ITCAV", 130, 90),
        ]
        reverse = {
            "Italian Cavallini": "F_ITCAV",
            "italian cavallini": "F_ITCAV",
            "italian": "F_ITCAV",
            "Other Team": "F_OTHER", "other team": "F_OTHER",
            "Winners": "F_WINNER", "winners": "F_WINNER",
        }
        text = (
            "Winners snapped Italian Cavallini's 2-game losing streak "
            "with a 130-90 win."
        )
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert "Italian Cavallini" in failures[0].claim
        assert "extended to 3" in failures[0].evidence

    def test_snap_possessive_object_unmappable_possessor_silenced(self):
        """Unmappable possessor (short first name) → snap check is silent.

        If we can't resolve the possessor to a franchise, silence is
        preferred over misattribution. The pre-fix behaviour would fall
        through to _find_nearby_franchise pass-2 and land on some other
        franchise; the possessive path prevents that.

        This test uses prose without an explicit game count so the
        unrelated explicit-count check elsewhere in verify_streaks
        doesn't fire — isolating the snap-check behaviour.
        """
        matchups = [
            _make_matchup(1, "F_OTHER", "F_BEN", 120, 100),
            _make_matchup(2, "F_OTHER", "F_BEN", 115, 105),
            _make_matchup(3, "F_WINNER", "F_BEN", 130, 90),
        ]
        reverse = {
            "Ben's Gods": "F_BEN", "ben's gods": "F_BEN",
            # Note: "ben" NOT in map — below 5-char threshold
            "Other Team": "F_OTHER", "other team": "F_OTHER",
            "Winners": "F_WINNER", "winners": "F_WINNER",
        }
        text = "Winners snapped Ben's losing streak with a win."
        failures = verify_streaks(text, matchups, 3, reverse)
        # Ben unmappable → snap check emits no failure. Whether any
        # other checks fire is out of scope for backlog B.
        snap_failures = [
            f for f in failures
            if "snapped" in f.claim.lower()
            or "snapped" in f.evidence.lower()
        ]
        assert snap_failures == []

    def test_snap_possessive_object_pronoun_falls_through(self):
        """Pronoun possessor ('his/their/the') → falls through to heuristic path."""
        matchups = [
            _make_matchup(1, "F_WINNER", "F1", 120, 100),
            _make_matchup(2, "F_WINNER", "F1", 115, 105),
            _make_matchup(3, "F_WINNER", "F1", 130, 90),
        ]
        reverse = {"Alpha Team": "F1", "alpha team": "F1",
                    "Winner Team": "F_WINNER", "winner team": "F_WINNER"}
        # "his" is lowercase → does NOT match possessive-object pattern
        # (which requires a leading capital letter). Falls through to
        # the normal subject-attribution path: Alpha Team is subject
        # (before "snapped"), Alpha Team lost → streak extended, flag.
        text = "Alpha Team snapped his losing streak."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert "extended" in failures[0].evidence.lower()

    def test_snap_possessive_object_possessor_had_no_streak(self):
        """Possessor is mappable but never had a losing streak → flag."""
        matchups = [
            _make_matchup(1, "F_BRANDON", "F_OTHER", 120, 100),  # Brandon won
            _make_matchup(2, "F_BRANDON", "F_OTHER", 115, 105),  # Brandon won
            _make_matchup(3, "F_WINNER", "F_BRANDON", 130, 90),  # Brandon lost once
        ]
        reverse = {
            "Brandon Knows Ball": "F_BRANDON",
            "brandon knows ball": "F_BRANDON",
            "brandon": "F_BRANDON",
            "Other Team": "F_OTHER", "other team": "F_OTHER",
            "Winners": "F_WINNER", "winners": "F_WINNER",
        }
        # Brandon had NO losing streak entering w3 (coming off a 2-0 run).
        text = "Winners snapped Brandon's losing streak this week."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert len(failures) == 1
        assert "no losing streak" in failures[0].evidence.lower()
        assert "Brandon Knows Ball" in failures[0].claim

    def test_snap_subject_attribution_still_works(self):
        """Regression guard: non-possessive snap claims use heuristic unchanged."""
        matchups = [
            _make_matchup(1, "F2", "F1", 120, 100),
            _make_matchup(2, "F2", "F1", 115, 105),
            _make_matchup(3, "F1", "F2", 130, 90),
        ]
        reverse = {"Alpha Team": "F1", "alpha team": "F1",
                    "Beta Squad": "F2", "beta squad": "F2"}
        # No possessive construction — falls through to existing path.
        text = "Alpha Team snapped their losing streak this week."
        failures = verify_streaks(text, matchups, 3, reverse)
        assert failures == []

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
        assert result.checks_run == 6

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
        assert result.checks_run == 6


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


# ── Unit: Category 4 — Series Record Verification ───────────────────


class TestVerifySeriesRecords:
    def _make_matchups(self):
        """F1 beats F2 in 7 of 10 meetings."""
        matchups = []
        for w in range(1, 8):
            matchups.append(_make_matchup(w, "F1", "F2", 120.0, 100.0))
        for w in range(8, 11):
            matchups.append(_make_matchup(w, "F2", "F1", 115.0, 105.0))
        return matchups

    def _reverse(self):
        return {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }

    def test_correct_series_record_passes(self):
        matchups = self._make_matchups()
        reverse = self._reverse()
        text = "Alpha Team leads the series 7-3 against Beta Squad."
        failures = verify_series_records(text, matchups, reverse)
        assert failures == []

    def test_reversed_order_passes(self):
        matchups = self._make_matchups()
        reverse = self._reverse()
        text = "Beta Squad trails 7-3 in the series against Alpha Team."
        failures = verify_series_records(text, matchups, reverse)
        assert failures == []

    def test_wrong_series_record_fails(self):
        matchups = self._make_matchups()
        reverse = self._reverse()
        text = "Alpha Team leads the series 8-2 against Beta Squad."
        failures = verify_series_records(text, matchups, reverse)
        assert len(failures) == 1
        assert failures[0].category == "SERIES"
        assert "7-3" in failures[0].evidence

    def test_no_series_keyword_skipped(self):
        matchups = self._make_matchups()
        reverse = self._reverse()
        # "7-3" without series/rivalry context — should not be checked
        text = "Alpha Team won 7-3 innings today against Beta Squad."
        failures = verify_series_records(text, matchups, reverse)
        assert failures == []

    def test_no_matchups_returns_empty(self):
        reverse = self._reverse()
        text = "Alpha Team leads the series 5-2 against Beta Squad."
        failures = verify_series_records(text, [], reverse)
        assert failures == []

    def test_single_franchise_skipped(self):
        matchups = self._make_matchups()
        reverse = self._reverse()
        # Only one franchise mentioned — can't verify H2H
        text = "Alpha Team has a 7-3 record in the series."
        failures = verify_series_records(text, matchups, reverse)
        assert failures == []


class TestVerifySeriesRecordsIntegration:
    """Integration tests with full DB."""

    def _build_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Alpha Team")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Beta Squad")

        # F1 beats F2 in weeks 1-3, F2 beats F1 in week 4
        for w in range(1, 4):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="F1", loser_id="F2",
                            winner_score=120.00 + w, loser_score=100.00 + w)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=4,
                        winner_id="F2", loser_id="F1",
                        winner_score=130.00, loser_score=110.00)

        con.commit()
        con.close()
        return db_path

    def test_correct_series_passes_pipeline(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team leads the series 3-1 against Beta Squad.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=4)
        # No series failures
        series_failures = [f for f in result.hard_failures if f.category == "SERIES"]
        assert series_failures == []

    def test_wrong_series_fails_pipeline(self, tmp_path):
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team leads the series 5-1 against Beta Squad.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=4)
        series_failures = [f for f in result.hard_failures if f.category == "SERIES"]
        assert len(series_failures) == 1


# ── Unit: Category 5 — Banned Phrase Detection ──────────────────────


class TestVerifyBannedPhrases:
    def test_clean_text_passes(self):
        text = "Alpha Team posted 130.50 to beat Beta Squad's 110.20."
        failures = verify_banned_phrases(text)
        assert failures == []

    def test_kill_list_phrase_detected(self):
        text = "It was the kind of chaos that makes fantasy football beautiful."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1
        assert failures[0].category == "BANNED_PHRASE"
        assert failures[0].severity == "SOFT"

    def test_delivered_a_statement_detected(self):
        text = "Alpha Team delivered a statement this week."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1
        assert "delivered a statement" in failures[0].claim

    def test_speculation_kicking_themselves(self):
        text = "Ben has to be kicking himself after that loss."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1
        assert failures[0].category == "SPECULATION"
        assert failures[0].severity == "SOFT"

    def test_speculation_that_stings(self):
        text = "Losing by 0.30 — that stings."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1
        assert failures[0].category == "SPECULATION"

    def test_speculation_probably_regret(self):
        text = "Steve probably regrets that bench decision."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1
        assert failures[0].category == "SPECULATION"

    def test_speculation_has_to_be_frustrating(self):
        text = "That has to be frustrating for the owner."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1

    def test_speculation_had_to_sting(self):
        text = "That loss had to sting for Brandon."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1

    def test_multiple_violations_all_reported(self):
        text = (
            "It was the kind of chaos that makes fantasy football great. "
            "Ben has to be kicking himself. That stings."
        )
        failures = verify_banned_phrases(text)
        assert len(failures) == 3

    def test_case_insensitive(self):
        text = "DELIVERED A STATEMENT this week."
        failures = verify_banned_phrases(text)
        assert len(failures) == 1

    def test_soft_failures_dont_block_pass(self, tmp_path):
        """Soft failures flag for review but don't set passed=False."""
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
        con.commit()
        con.close()

        text = (
            "--- SHAREABLE RECAP ---\n"
            "Alpha Team delivered a statement with 120.50-100.20.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(text, db_path=db_path, league_id=LEAGUE,
                                  season=SEASON, week=1)
        # Scores are correct, so no hard failures
        assert result.passed is True
        # But soft failure flagged
        assert result.soft_failure_count >= 1
        assert any(f.category == "BANNED_PHRASE" for f in result.soft_failures)


# ── Unit: Category 6 — Cross-Week Consistency ────────────────────────


class TestCrossWeekStreakConsistency:
    def _reverse(self):
        return {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }

    def test_consistent_growing_streak_passes(self):
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team has a 3-game winning streak."),
            (4, "Alpha Team extended their 4-game winning streak."),
            (5, "Alpha Team has won 5 straight games."),
        ]
        failures = verify_cross_week_consistency(weeks, reverse)
        assert failures == []

    def test_streak_decrease_flagged(self):
        """Same streak type decreases between close weeks — contradiction."""
        reverse = self._reverse()
        weeks = [
            (8, "Alpha Team is on a 5-game winning streak."),
            (10, "Alpha Team has a 3-game winning streak."),
        ]
        failures = verify_cross_week_consistency(weeks, reverse)
        assert len(failures) == 1
        assert failures[0].category == "CONSISTENCY"
        assert "5" in failures[0].claim
        assert "3" in failures[0].claim

    def test_streak_reset_allowed(self):
        """Small streak after a gap is fine — streak may have broken and restarted."""
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team is on a 3-game winning streak."),
            (10, "Alpha Team has won 2 straight games."),
        ]
        # Gap of 7 weeks and count dropped below 3 — allowed (reset)
        failures = verify_cross_week_consistency(weeks, reverse)
        assert failures == []

    def test_different_franchises_independent(self):
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team is on a 5-game winning streak."),
            (5, "Beta Squad has a 3-game winning streak."),
        ]
        failures = verify_cross_week_consistency(weeks, reverse)
        assert failures == []

    def test_empty_weeks_passes(self):
        reverse = self._reverse()
        failures = verify_cross_week_consistency([], reverse)
        assert failures == []


class TestCrossWeekSeriesConsistency:
    def _reverse(self):
        return {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }

    def test_series_grows_by_one_passes(self):
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team leads the series 7-3 against Beta Squad."),
            (10, "Alpha Team leads the series 8-3 against Beta Squad."),
        ]
        failures = verify_cross_week_consistency(weeks, reverse)
        assert failures == []

    def test_series_total_jumps_impossibly(self):
        """Total meetings can't jump by more than weeks_between."""
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team leads the series 7-3 against Beta Squad."),
            (5, "Alpha Team leads the series 12-5 against Beta Squad."),
        ]
        # 10 total -> 17 total in 2 weeks = impossible
        failures = verify_cross_week_consistency(weeks, reverse)
        assert len(failures) >= 1
        assert any(f.category == "CONSISTENCY" for f in failures)

    def test_series_wins_decrease_flagged(self):
        """Wins can never decrease."""
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team leads the series 7-3 against Beta Squad."),
            (8, "Alpha Team leads the series 6-4 against Beta Squad."),
        ]
        failures = verify_cross_week_consistency(weeks, reverse)
        assert len(failures) >= 1
        assert any("decrease" in f.evidence.lower() for f in failures)

    def test_single_week_no_failures(self):
        reverse = self._reverse()
        weeks = [
            (3, "Alpha Team leads the series 7-3 against Beta Squad."),
        ]
        failures = verify_cross_week_consistency(weeks, reverse)
        assert failures == []


# ── Regression: 2025 w11/w13 verifier false positives ────────────────
#
# These tests pin the three verifier parse bugs (V1, V2, V3) identified
# in OBSERVATIONS_2026_04_14_Q4_SUPERLATIVE_DIAGNOSIS.md. Each test uses
# prose drawn directly from the six rejected drafts in that diagnosis.
# Companion tests verify that genuine violations are still caught so the
# fix does not simply defang the check.


class TestRegressionW11W13FalsePositives:
    """Pin the V1/V2/V3 parse bugs surfaced in the 2026-04-14 diagnosis."""

    # ── V1: "previous season high" ───────────────────────────────────

    def _season_matchups_51_85(self):
        # Team scores are irrelevant for this check — only the player
        # season high (51.85) matters. Use any valid matchup shape.
        return [_make_matchup(1, "F1", "F2", 120.00, 100.00)]

    def test_v1_previous_season_high_not_flagged(self):
        """w11 a1/a2/a3: 'breaks the previous season high of 48.10'.

        51.85 is the current season high (Allen's Week 11 score). The
        model is correctly positioning 48.10 as the *prior* high — a
        temporally displaced claim we cannot evaluate. Skip.
        """
        matchups = self._season_matchups_51_85()
        text = (
            "Josh Allen dropped 51.85 — breaks the previous "
            "season high of 48.10 and powered Miller to another win."
        )
        failures = verify_superlatives(
            text, matchups, None, SEASON, 51.85, None,
        )
        assert failures == [], (
            f"expected no failures for 'previous season high' construction, "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_v1_prior_season_high_not_flagged(self):
        """Synonym check: 'prior' should behave the same as 'previous'."""
        matchups = self._season_matchups_51_85()
        text = "That 51.85 topped the prior season high of 48.10."
        failures = verify_superlatives(
            text, matchups, None, SEASON, 51.85, None,
        )
        assert failures == []

    def test_v1_bare_season_high_still_flagged(self):
        """Sanity: a bare (non-temporal-qualified) wrong claim is still caught.

        Without 'previous/prior/former/past', a season-high claim remains
        subject to the max comparison. 48.10 is not the actual season high.
        """
        matchups = self._season_matchups_51_85()
        text = "Allen's 48.10 is the season high."
        failures = verify_superlatives(
            text, matchups, None, SEASON, 51.85, None,
        )
        assert len(failures) == 1
        assert failures[0].category == "SUPERLATIVE"
        assert "48.10" in failures[0].claim

    # ── V2: "all-time record of <integer>" ───────────────────────────

    def test_v2_alltime_record_of_integer_not_flagged(self):
        """w13 a3: '...27.95 points watching from the bench as the streak
        marches toward the all-time record of 15.'

        The '15' is the all-time losing-streak record (games), not a
        scoring record. The 27.95 nearby is unrelated — Trevor Lawrence's
        bench points. Verifier should recognize 'record of <integer>' as
        a count claim and skip.
        """
        season = [_make_matchup(1, "F1", "F2", 150.00, 100.00)]
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        text = (
            "Trevor Lawrence's 27.95 points watched from the bench as "
            "the streak marches toward the all-time record of 15."
        )
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, 77.00,
        )
        assert failures == [], (
            f"expected no failures for 'all-time record of 15' (count), "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_v2_alltime_record_of_decimal_still_flagged(self):
        """Sanity: 'all-time record' with a decimal score nearby (not an
        integer count) is still verified. An incorrect scoring claim
        must still flag.
        """
        season = [_make_matchup(1, "F1", "F2", 160.00, 100.00)]
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        text = "That 145.30 is the all-time record."
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        assert len(failures) == 1
        assert failures[0].category == "SUPERLATIVE"
        assert "145.30" in failures[0].claim

    # ── V3: " but " clause-break for PLAYER_SCORE ────────────────────

    def _build_v3_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Warmongers")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Stu's Crew")

        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=13,
                        winner_id="F1", loser_id="F2",
                        winner_score=96.95, loser_score=94.60)

        # Bowers' actual score is 20.30. The draft also mentions 53.90
        # as a bench total (not a player score).
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=13,
                             franchise_id="F1", player_id="P1",
                             score=20.30)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=13,
                             franchise_id="F1", player_id="P2",
                             score=27.20)

        con.commit()
        con.close()
        return db_path

    def test_v3_player_but_bench_total_not_flagged(self, tmp_path):
        """w13 a1: 'got 20.30 from Brock Bowers but left 53.90 on the bench'.

        53.90 is a bench total appearing after the clause-break 'but'.
        Verifier must not fuse it into a Bowers attribution.
        """
        # Player directory entry — tests use a minimal player name map.
        db_path = self._build_v3_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Insert player directory rows if schema supports it.
        try:
            con.execute(
                "INSERT OR IGNORE INTO player_directory "
                "(player_id, name, position) VALUES (?, ?, ?)",
                ("P1", "Bowers, Brock", "TE"),
            )
            con.execute(
                "INSERT OR IGNORE INTO player_directory "
                "(player_id, name, position) VALUES (?, ?, ?)",
                ("P2", "Goff, Jared", "QB"),
            )
            con.commit()
        except sqlite3.OperationalError:
            # Schema may differ; skip gracefully
            pass
        con.close()

        text = (
            "--- SHAREABLE RECAP ---\n"
            "The Warmongers got 20.30 from Brock Bowers but left 53.90 "
            "on the bench, including Jared Goff's 27.20.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=13,
        )
        # No PLAYER_SCORE failure should be raised for Bowers/53.90.
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert player_score_failures == [], (
            f"expected no PLAYER_SCORE failures, got "
            f"{[(f.claim, f.evidence) for f in player_score_failures]}"
        )


# ─── V4/V5/V6 parse-false-positive regressions ───────────────────────
#
# Fixtures are reproduced from prompt_audit rows captured in the
# 2026-04-14 wider SUPERLATIVE classification pass
# (scripts/audit_queries/OBSERVATIONS_2026_04_14_SUPERLATIVE_WIDER_PASS.md).
#
# Source rows:
#   V4: id=45 (2024 w13 a1), id=17b (2025 w10 a1)
#   V5: id=14 (2025 w9 a1)
#   V6: id=5  (2025 w3 a1)
#
# Each category has a companion "bare claim still flags" test that
# guards against the fix simply defanging the check.
class TestRegressionSuperlativeWiderPass:
    """Pin V4/V5/V6 parse bugs surfaced in the 2026-04-14 wider pass."""

    # ── V4: ordinal-qualifier prefix ("second-lowest", "3rd-highest") ─

    def _season_low_matchups(self):
        """Actual season low is 88.40; 120.20 is not the season low."""
        return [
            _make_matchup(1, "F1", "F2", 130.50, 110.20),
            _make_matchup(2, "F3", "F4", 95.80, 88.40),
            _make_matchup(3, "F1", "F3", 120.50, 100.10),
        ]

    def test_v4_second_lowest_not_flagged_row45(self):
        """id=45 (2024 w13 a1): 'Steve falls to 8-5 after his second-
        lowest output of the season. Stu edged Eddie 120.20-114.05.'

        The ordinal 'second-' negates the 'lowest of the season'
        superlative — this is Steve's #2-worst score, not the season
        minimum. The nearby 120.20 is Stu's matchup score in the next
        sentence, unrelated to the superlative. Skip.
        """
        text = (
            "Steve falls to 8-5 after his second-lowest output of the "
            "season. Stu edged Eddie 120.20-114.05."
        )
        failures = verify_superlatives(
            text, self._season_low_matchups(), None, SEASON, None, None,
        )
        # Filter to SEASON-LOW-shaped failures to avoid conflation with
        # any other check that might fire on this prose.
        low_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "low" in f.claim.lower()
        ]
        assert low_failures == [], (
            f"expected no season-low failure for 'second-lowest' "
            f"(ordinal prefix), got {[(f.claim, f.evidence) for f in low_failures]}"
        )

    def test_v4_second_lowest_not_flagged_row17b(self):
        """id=17b (2025 w10 a1): 'Brandon managed just 90.10 total —
        his second-lowest score of the season.' Same shape as row 45."""
        text = (
            "Brandon managed just 90.10 total — his second-lowest "
            "score of the season."
        )
        failures = verify_superlatives(
            text, self._season_low_matchups(), None, SEASON, None, None,
        )
        low_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "low" in f.claim.lower()
        ]
        assert low_failures == [], (
            f"expected no season-low failure for 'his second-lowest', "
            f"got {[(f.claim, f.evidence) for f in low_failures]}"
        )

    def test_v4_numeric_ordinal_high_not_flagged(self):
        """Numeric-ordinal variant: '3rd-highest' / '2nd-highest' —
        same class as word-form ordinals."""
        text = "The Warmongers posted their 3rd-highest score of the season at 145.30."
        matchups = [
            _make_matchup(1, "F1", "F2", 192.15, 100.00),  # actual high
            _make_matchup(2, "F1", "F2", 160.00, 110.00),
        ]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert high_failures == [], (
            f"expected no season-high failure for '3rd-highest', "
            f"got {[(f.claim, f.evidence) for f in high_failures]}"
        )

    def test_v4_bare_season_low_still_flagged(self):
        """Sanity: a bare 'lowest of the season' claim with a wrong
        score still flags. The V4 guard must not defang genuine
        violations.
        """
        text = "That 120.20 is the lowest score of the season."
        failures = verify_superlatives(
            text, self._season_low_matchups(), None, SEASON, None, None,
        )
        low_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "low" in f.claim.lower()
        ]
        assert len(low_failures) == 1, (
            f"expected one season-low failure for bare wrong claim, "
            f"got {[(f.claim, f.evidence) for f in low_failures]}"
        )
        assert "120.20" in low_failures[0].claim

    # ── V5: possessive pronoun / personal-scope marker ───────────────

    def test_v5_possessive_personal_high_not_flagged_row14(self):
        """id=14 (2025 w9 a1): 'Brock Bowers (37.3) carried the
        Warmongers past Brandon\'s 116.75 — easily his highest output
        in nine tries this season.'

        The superlative is scoped to Brandon personally via both
        possessive 'his' and personal-scope marker 'in nine tries'.
        The verifier lacks per-franchise/per-player season-high data,
        so it should skip rather than compare to the league-wide max.
        """
        text = (
            "Brock Bowers (37.3) carried the Warmongers past Brandon's "
            "116.75 — easily his highest output in nine tries this "
            "season."
        )
        # Actual league high is 192.15, well above the 116.75 the
        # verifier would extract.
        matchups = [
            _make_matchup(1, "F1", "F2", 192.15, 100.00),
            _make_matchup(9, "F3", "F4", 116.75, 105.00),
        ]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert high_failures == [], (
            f"expected no season-high failure for possessive-scoped "
            f"'his highest ... in nine tries', "
            f"got {[(f.claim, f.evidence) for f in high_failures]}"
        )

    def test_v5_possessive_low_not_flagged(self):
        """Parity: possessive-scoped season-low claim scopes to a
        person/team, not the league."""
        text = "Brandon managed 90.10 — his lowest output of the season."
        matchups = [
            _make_matchup(1, "F1", "F2", 130.50, 70.00),  # actual low
            _make_matchup(2, "F3", "F4", 100.00, 90.10),
        ]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        low_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "low" in f.claim.lower()
        ]
        assert low_failures == [], (
            f"expected no season-low failure for 'his lowest output', "
            f"got {[(f.claim, f.evidence) for f in low_failures]}"
        )

    def test_v5_bare_league_season_high_still_flagged(self):
        """Sanity: a bare 'season high' claim without possessive or
        personal-scope marker is still subject to the max check.
        """
        text = "That 116.75 is the season high."
        matchups = [
            _make_matchup(1, "F1", "F2", 192.15, 100.00),
        ]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert len(high_failures) == 1
        assert "116.75" in high_failures[0].claim

    # ── V6: frequency-marker guard for all-time loop ─────────────────

    def test_v6_nth_time_in_league_history_not_flagged_row5(self):
        """id=5 (2025 w3 a1): 'marking just the 323rd time in league
        history a starter has been completely shut out. Pat stayed
        perfect with a 125.30-111.95 win.'

        'Nth time in league history' is an event-frequency claim, not
        a scoring record. The verifier's all-time loop fires on
        'league history' and extracts 125.30 from an unrelated
        adjacent clause. Skip.
        """
        text = (
            "Brandon's week got ugly when CeeDee Lamb put up a zero, "
            "marking just the 323rd time in league history a starter "
            "has been completely shut out. Pat stayed perfect with a "
            "125.30-111.95 win."
        )
        season = [_make_matchup(3, "F1", "F2", 125.30, 111.95)]
        # All-time high is much larger than any nearby extracted score,
        # so a bare match would flag.
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        alltime_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "all-time" in f.claim.lower()
        ]
        assert alltime_failures == [], (
            f"expected no all-time failure for 'Nth time in league "
            f"history' (frequency construction), "
            f"got {[(f.claim, f.evidence) for f in alltime_failures]}"
        )

    def test_v6_only_time_in_league_history_not_flagged(self):
        """Synonym: 'only time in league history' is also a
        frequency construction."""
        text = (
            "That zero is the only time in league history a starter "
            "was benched mid-game. Final: 125.30-111.95."
        )
        season = [_make_matchup(3, "F1", "F2", 125.30, 111.95)]
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        alltime_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "all-time" in f.claim.lower()
        ]
        assert alltime_failures == []

    def test_v6_first_time_in_league_history_not_flagged(self):
        """Synonym: 'first time in league history' — frequency."""
        text = (
            "For the first time in league history, a team scored a zero. "
            "Final: 125.30-111.95."
        )
        season = [_make_matchup(3, "F1", "F2", 125.30, 111.95)]
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        alltime_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "all-time" in f.claim.lower()
        ]
        assert alltime_failures == []

    def test_v6_rare_in_league_history_still_verified(self):
        """Sanity: the guard deliberately excludes bare frequency
        adjectives like 'rare'. A claim that 192.15 is 'a rare feat
        in league history' still verifies against the all-time max —
        if it's wrong, it flags.
        """
        text = "That 145.30 is a rare feat in league history."
        season = [_make_matchup(1, "F1", "F2", 145.30, 100.00)]
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        alltime_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "all-time" in f.claim.lower()
        ]
        assert len(alltime_failures) == 1, (
            f"expected one all-time failure for 'rare feat in league "
            f"history' (V6 does not guard bare 'rare'), "
            f"got {[(f.claim, f.evidence) for f in alltime_failures]}"
        )
        assert "145.30" in alltime_failures[0].claim

    def test_v6_bare_league_history_record_still_flagged(self):
        """Sanity: 'league history' without a frequency marker still
        verifies against the all-time max.
        """
        text = "That 145.30 is the best score in league history."
        season = [_make_matchup(1, "F1", "F2", 145.30, 100.00)]
        alltime = season + [_make_matchup(1, "F1", "F2", 198.80, 90.00)]
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        alltime_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "all-time" in f.claim.lower()
        ]
        assert len(alltime_failures) == 1
        assert "145.30" in alltime_failures[0].claim

