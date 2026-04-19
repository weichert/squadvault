"""Tests for Recap Verifier v1 (Categories 1-7).

Exercises each verifier category against synthetic data:

Category 1: SCORE — correct scores pass, wrong/transposed/invented fail
Category 2: SUPERLATIVE — correct season-high/all-time pass, false claims fail
Category 3: STREAK — correct streak counts pass, wrong counts and snap/extend logic fail
Category 7: PLAYER_FRANCHISE — cross-franchise misattribution detection

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
    verify_faab_claims,
    verify_player_franchise,
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


def _insert_faab_bid(con, *, league_id, season, franchise_id, player_id,
                      bid_amount, timestamp="2024-10-15T12:00:00Z"):
    payload = json.dumps({
        "franchise_id": franchise_id, "player_id": player_id,
        "bid_amount": bid_amount, "mfl_type": "BBID_WAIVER",
    }, sort_keys=True)
    ext_id = f"faab_{league_id}_{season}_{franchise_id}_{player_id}_{bid_amount}"
    con.execute(
        """INSERT INTO memory_events (league_id, season, external_source, external_id,
           event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, 'test', ?, 'WAIVER_BID_AWARDED', ?, ?, ?)""",
        (league_id, season, ext_id, timestamp, timestamp, payload))
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events (league_id, season, event_type,
           action_fingerprint, best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, 'WAIVER_BID_AWARDED', ?, ?, 100, ?, ?)""",
        (league_id, season, f"fp_{ext_id}", me_id, timestamp, timestamp))


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

    def test_first_word_alias_3_chars_allowed(self):
        """First-word aliases as short as 3 chars are added (substring
        hazards handled by word-boundary matching at lookup time, not by
        a length threshold at map-build time)."""
        name_map = {
            "F1": "Ben's Gods",
            "F2": "Stu's Crew",
            "F3": "Robb's Raiders",
        }
        reverse = _build_reverse_name_map(name_map)
        assert reverse.get("ben") == "F1"
        assert reverse.get("stu") == "F2"
        assert reverse.get("robb") == "F3"

    def test_last_word_alias_added(self):
        """Last-word aliases (≥5 chars, unique, stop-word filtered) are
        added so short-forms like 'Warmongers' match 'Weichert's Warmongers'."""
        name_map = {
            "F1": "Weichert's Warmongers",
            "F2": "Paradis' Playmakers",
            "F3": "Robb's Raiders",
        }
        reverse = _build_reverse_name_map(name_map)
        assert reverse.get("warmongers") == "F1"
        assert reverse.get("playmakers") == "F2"
        assert reverse.get("raiders") == "F3"

    def test_last_word_alias_respects_min_length(self):
        """Last-word aliases under 5 chars are not added ('gods', 'crew',
        'haze', 'ball' are too short / too common)."""
        name_map = {
            "F1": "Ben's Gods",
            "F2": "Stu's Crew",
            "F3": "Purple Haze",
            "F4": "Brandon Knows Ball",
        }
        reverse = _build_reverse_name_map(name_map)
        assert "gods" not in reverse
        assert "crew" not in reverse
        assert "haze" not in reverse
        assert "ball" not in reverse

    def test_last_word_alias_stop_words_excluded(self):
        """'draft' is stop-worded because it collides with fantasy-draft
        language in prose ('auction draft', 'FAAB draft investment')."""
        name_map = {"F1": "Miller's Genuine Draft"}
        reverse = _build_reverse_name_map(name_map)
        assert "draft" not in reverse
        # Full name and first-word alias still work
        assert reverse["Miller's Genuine Draft"] == "F1"
        assert reverse["miller's genuine draft"] == "F1"
        assert reverse.get("miller") == "F1"

    def test_last_word_alias_ambiguity_rejected(self):
        """When two franchises share the same last word, no alias is
        added (same uniqueness rule as first-word aliases)."""
        name_map = {
            "F1": "Alpha Raiders",
            "F2": "Beta Raiders",
        }
        reverse = _build_reverse_name_map(name_map)
        assert "raiders" not in reverse

    def test_first_word_alias_ambiguity_rejected(self):
        """When two franchises share the same first word, no alias is
        added — even after the threshold drop to 3 chars."""
        name_map = {
            "F1": "Ben's Gods",
            "F2": "Ben's Gang",
        }
        reverse = _build_reverse_name_map(name_map)
        assert "ben" not in reverse

    def test_owner_alias_added_when_owner_map_supplied(self):
        """Owner first names become aliases when owner_map is supplied.
        Handles league-insider prose like 'Michele stayed perfect' or
        'KP put up 169' where the owner's first name doesn't appear
        anywhere in the franchise name."""
        name_map = {
            "F_CAVALLINI": "Italian Cavallini",
            "F_KP": "Paradis' Playmakers",
            "F_WEICHERT": "Weichert's Warmongers",
        }
        owner_map = {
            "F_CAVALLINI": "Michele Baroi",
            "F_KP": "KP Paradis",
            "F_WEICHERT": "Steve Weichert",
        }
        reverse = _build_reverse_name_map(name_map, owner_map)
        assert reverse.get("michele") == "F_CAVALLINI"
        assert reverse.get("kp") == "F_KP"  # 2-char alias allowed
        assert reverse.get("steve") == "F_WEICHERT"

    def test_owner_alias_not_added_without_owner_map(self):
        """No owner aliases when owner_map is None (backward compat)."""
        name_map = {"F1": "Italian Cavallini"}
        reverse = _build_reverse_name_map(name_map)
        assert "michele" not in reverse

    def test_owner_alias_does_not_override_existing_alias(self):
        """If an owner's first name already matches a franchise alias,
        the existing alias wins (no override)."""
        name_map = {
            "F1": "Miller's Genuine Draft",
            "F2": "Purple Haze",
        }
        # Owner of F2 is hypothetically named "Miller" — collides with
        # F1's first-word alias. Existing alias must win.
        owner_map = {"F1": "Jon Doe", "F2": "Miller Smith"}
        reverse = _build_reverse_name_map(name_map, owner_map)
        assert reverse.get("miller") == "F1"  # still F1, not F2

    def test_owner_alias_ambiguity_rejected(self):
        """When two owners share the same first name, no alias is added."""
        name_map = {"F1": "Alpha Team", "F2": "Beta Squad"}
        owner_map = {"F1": "Steve Smith", "F2": "Steve Jones"}
        reverse = _build_reverse_name_map(name_map, owner_map)
        assert "steve" not in reverse

    def test_owner_alias_skipped_for_unknown_franchise(self):
        """Owner names for franchises not in name_map are silently
        ignored (defensive against partial data)."""
        name_map = {"F1": "Alpha Team"}
        owner_map = {"F1": "Steve", "F_UNKNOWN": "Michele"}
        reverse = _build_reverse_name_map(name_map, owner_map)
        assert reverse.get("steve") == "F1"
        assert "michele" not in reverse


class TestFindNearbyFranchiseIds:
    """Word-boundary matching prevents substring misattribution hazards."""

    def test_short_alias_word_boundary_not_matched_inside_word(self):
        """'ben' must not match inside 'bench' or 'forbidden'."""
        from squadvault.core.recaps.verification.recap_verifier_v1 import (
            _find_nearby_franchise_ids,
        )
        reverse = {"ben": "F1", "ben's gods": "F1"}
        text = "The bench was forbidden to sit this week."
        # Position doesn't matter much — the window covers the whole text.
        found = _find_nearby_franchise_ids(text, 10, reverse)
        assert "F1" not in found

    def test_short_alias_matches_as_subject(self):
        """'ben' must match 'Ben dropped to 3-7' as a legitimate subject."""
        from squadvault.core.recaps.verification.recap_verifier_v1 import (
            _find_nearby_franchise_ids,
        )
        reverse = {"ben": "F1", "ben's gods": "F1"}
        text = "Ben dropped to 3-7 after the loss."
        found = _find_nearby_franchise_ids(text, 10, reverse)
        assert "F1" in found

    def test_short_alias_not_matched_before_player_name(self):
        """'brandon' as an alias must not match inside 'Brandon Aubrey'
        (capital-letter lookahead rejects whitespace + capital letter)."""
        from squadvault.core.recaps.verification.recap_verifier_v1 import (
            _find_nearby_franchise_ids,
        )
        reverse = {"brandon": "F1", "brandon knows ball": "F1"}
        text = "Brandon Aubrey kicked four field goals this week."
        found = _find_nearby_franchise_ids(text, 10, reverse)
        assert "F1" not in found

    def test_last_word_alias_matches(self):
        """'Warmongers' alone matches the Weichert's Warmongers franchise."""
        from squadvault.core.recaps.verification.recap_verifier_v1 import (
            _find_nearby_franchise_ids,
        )
        reverse = {
            "weichert's warmongers": "F1",
            "weichert": "F1",
            "warmongers": "F1",
        }
        text = "Jahmyr Gibbs posted 36.70 points for the Warmongers."
        found = _find_nearby_franchise_ids(text, 25, reverse)
        assert "F1" in found


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

    def test_v8_matchup_line_score_before_dash_skipped(self):
        """V8: score in matchup line '137.50-103.10' is a team score,
        not a superlative claim. The 103.10 after the dash must be
        skipped. Source: Finding 3, FP-SUPERLATIVE-MATCHUP-LINE."""
        text = "They cruised to a 137.50-103.10 win this season"
        # "season" is near the end — _extract_nearby_score should not
        # return 103.10 (part of matchup line) or 137.50 (also part).
        pos = text.index("season")
        result = _extract_nearby_score(text, pos)
        assert result is None, (
            f"expected None (both scores are matchup-line), got {result}"
        )

    def test_v8_matchup_line_score_after_dash_skipped(self):
        """V8: reversed order '103.10-137.50' also detected."""
        text = "Their 103.10-137.50 loss set a new season low"
        pos = text.index("season")
        result = _extract_nearby_score(text, pos)
        assert result is None, (
            f"expected None (both scores are matchup-line), got {result}"
        )

    def test_v8_standalone_score_still_extracted(self):
        """V8 does not interfere with standalone scores."""
        text = "Alpha posted a season-high 145.30 in the blowout."
        pos = text.index("season")
        result = _extract_nearby_score(text, pos)
        assert result is not None
        assert abs(result - 145.30) < 0.01


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
        assert result.checks_run == 8

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
        assert result.checks_run == 8


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


# ── Shared fixtures: STREAK idiomatic-possessor regression ──────────
#
# Reproduce the alias-map topology at the heart of the captured
# id=54 / id=25 failures: the snap-verb subject has a short first
# name ("ben", "kp") excluded from reverse_name_map by the len<5
# substring-safety filter in _build_reverse_name_map. Without the
# idiomatic guard, _find_nearby_franchise pass-2 lands on the
# possessor after the snap verb, producing a wrong-subject
# STREAK failure against prose that never claimed a literal streak
# was snapped.

def _brandon_losing_matchups():
    """Brandon 0-10 entering week 11, loses W11 to Ben → 0-11.

    Mirrors the fixture topology in test_snap_possessive_object_row20_pattern:
    F_BRANDON loses weeks 1-10 to OTHER; in week 11, F_BEN beats
    F_BRANDON 111.60-104.15. Shared across id=54 prose
    (rhetorical target) and positive-control #5 (literal streak,
    existing resolver still authoritative).
    """
    matchups = []
    for w in range(1, 11):
        matchups.append(_make_matchup(w, "OTHER", "F_BRANDON", 120, 90))
    matchups.append(_make_matchup(11, "F_BEN", "F_BRANDON", 111.60, 104.15))
    return matchups


def _reverse_map_ben_brandon():
    """Alias map where 'ben' is excluded (len<5 threshold).

    Matches production behavior: _build_reverse_name_map includes
    first-word aliases only when len>=5, so "Brandon" (7 chars) is
    included but "ben" (3 chars) is not. This is the condition that
    causes _find_nearby_franchise pass-1 to fall through to pass-2
    when the snap subject is "Ben ...".
    """
    return {
        "Ben's Gods": "F_BEN", "ben's gods": "F_BEN",
        # Note: "ben" intentionally NOT in map (3 chars, below
        # 5-char first-word alias threshold).
        "Brandon Knows Ball": "F_BRANDON",
        "brandon knows ball": "F_BRANDON",
        "brandon": "F_BRANDON",  # 7-char first-word alias (built in prod)
        "Other Team": "OTHER", "other team": "OTHER",
    }


class TestRegressionStreakPossessiveIdiomatic:
    """Pin STREAK idiomatic-target possessive-scope fix.

    Captured failures: id=54 (2025 W11 a1), id=25 (2025 W13).

    Mechanism: _SNAP_PATTERN fires on a SOFT trailing keyword
    (losing/winning/straight/consecutive) when the actual
    streak-like noun is rhetorical ("season", "momentum", "run",
    "slide"). The span ends before any literal "streak" noun, so
    _POSSESSIVE_OBJECT_STREAK fails inside the span and
    _find_nearby_franchise pass-2 picks up the possessor after the
    snap verb, emitting a wrong-subject STREAK failure against
    prose that never claimed a literal streak was snapped.

    Fix: _has_idiomatic_snap_possessor guard silences snap checks
    whose span (a) does NOT end with "streak"/"skid" AND (b)
    contains a proper-noun possessor. Literal-streak spans pass
    through to the existing resolvers, unchanged.

    Out of scope: id=7 pronoun-possessive + short-alias subject
    variant ("Robb snapped his losing streak") — span ends on
    literal "streak" so this guard does not apply; remains in
    backlog.
    """

    # ── Captured: id=54 (2025 W11 a1) ────────────────────────────
    def test_id54_perfect_losing_season_not_flagged(self):
        """Verbatim id=54 prose: 'snapped Brandon's perfect losing season...'

        Span ends at "losing" — no literal "streak" noun follows.
        Guard fires on the proper-noun possessor "Brandon's"; snap
        check silences rather than falling through to pass-2
        proximity attribution.
        """
        matchups = _brandon_losing_matchups()
        reverse = _reverse_map_ben_brandon()
        text = (
            "Ben snapped Brandon's perfect losing season with a "
            "111.60-104.15 victory, though Brandon actually put up "
            "his best score in weeks."
        )
        failures = verify_streaks(text, matchups, 11, reverse)
        streak_failures = [f for f in failures if f.category == "STREAK"]
        assert streak_failures == [], (
            f"expected no STREAK failures for idiomatic 'losing season' "
            f"target; got: {[(f.claim, f.evidence) for f in streak_failures]}"
        )

    # ── Captured: id=25 (2025 W13) ───────────────────────────────
    def test_id25_purple_haze_momentum_not_flagged(self):
        """Verbatim id=25 prose: 'snapped Purple Haze's modest momentum...'

        Greedy 80-char window consumes the possessor clause but
        stops at "losing" before reaching the trailing "streak"
        attached to a DIFFERENT possessor ("Pat's four-game losing
        streak"). Guard fires on proper-noun possessor "Purple
        Haze's"; snap check silences.
        """
        matchups = [
            _make_matchup(1, "F_ROBB", "F_HAZE", 120, 100),
            _make_matchup(2, "F_HAZE", "F_ROBB", 110, 90),
            _make_matchup(3, "F_ROBB", "F_HAZE", 101, 97),
        ]
        reverse = {
            "Robb's Team": "F_ROBB", "robb's team": "F_ROBB",
            "Purple Haze": "F_HAZE", "purple haze": "F_HAZE",
            "purple": "F_HAZE",
        }
        text = (
            "Robb snapped Purple Haze's modest momentum with a "
            "101-97 victory, ending Pat's four-game losing streak "
            "that defined his last month."
        )
        failures = verify_streaks(text, matchups, 3, reverse)
        # The second clause references Pat's streak but Pat is not
        # in this fixture's matchups or alias map — intentional:
        # the guard must silence the first clause regardless of
        # what the unrelated second clause does.
        streak_failures = [
            f for f in failures if f.category == "STREAK"
            and "Purple Haze" in (f.claim + f.evidence)
        ]
        assert streak_failures == [], (
            f"expected no STREAK failure attributing to Purple Haze for "
            f"idiomatic 'momentum' target; got: "
            f"{[(f.claim, f.evidence) for f in streak_failures]}"
        )

    # ── Synthetic: idiomatic 'run' ───────────────────────────────
    def test_idiomatic_synthetic_winning_run_not_flagged(self):
        """'snapped Brandon's winning run' — idiomatic 'run' target.

        SOFT trailing keyword "winning" fires _SNAP_PATTERN; span
        ends at "winning" (the literal noun is "run", not "streak").
        Guard fires on proper-noun possessor "Brandon's".
        """
        matchups = _brandon_losing_matchups()
        reverse = _reverse_map_ben_brandon()
        text = "Ben snapped Brandon's winning run with a 111.60-104.15 victory."
        failures = verify_streaks(text, matchups, 11, reverse)
        streak_failures = [f for f in failures if f.category == "STREAK"]
        assert streak_failures == [], (
            f"expected no STREAK failures for idiomatic 'winning run' "
            f"target; got: {[(f.claim, f.evidence) for f in streak_failures]}"
        )

    # ── Synthetic: idiomatic 'slide' ─────────────────────────────
    def test_idiomatic_synthetic_losing_slide_not_flagged(self):
        """'snapped Brandon's multi-week losing slide' — idiomatic 'slide'.

        Documented in the guard docstring. SOFT trailing keyword
        "losing" fires _SNAP_PATTERN; span ends at "losing" (the
        literal noun is "slide"). Guard fires on proper-noun
        possessor "Brandon's".
        """
        matchups = _brandon_losing_matchups()
        reverse = _reverse_map_ben_brandon()
        text = (
            "Ben snapped Brandon's multi-week losing slide with a "
            "111.60-104.15 win."
        )
        failures = verify_streaks(text, matchups, 11, reverse)
        streak_failures = [f for f in failures if f.category == "STREAK"]
        assert streak_failures == [], (
            f"expected no STREAK failures for idiomatic 'losing slide' "
            f"target; got: {[(f.claim, f.evidence) for f in streak_failures]}"
        )

    # ── Positive control: literal 'streak' + possessive ──────────
    def test_literal_streak_possessive_still_resolves(self):
        """Pin that _POSSESSIVE_OBJECT_STREAK still fires on literal 'streak'.

        Span ends on the literal "streak" noun, so the guard
        returns False and the existing possessive-object resolver
        takes over. Mirrors test_snap_possessive_object_row20_pattern
        — if this regresses, the literal-streak passthrough branch
        of the guard is broken.
        """
        matchups = _brandon_losing_matchups()
        reverse = _reverse_map_ben_brandon()
        # Same fixture, but prose names the literal streak — the
        # captured failure from id=20 (already resolved by c103e4d).
        # Brandon's pre-week streak is -10 (not -11), so the 11-game
        # claim is false and the existing resolver must still raise
        # the possessive-scoped failure.
        text = (
            "Ben snapped Brandon's 11-game losing streak with a "
            "111.60-104.15 victory."
        )
        failures = verify_streaks(text, matchups, 11, reverse)
        streak_failures = [f for f in failures if f.category == "STREAK"]
        # The existing resolver emits a failure that cites Brandon
        # Knows Ball as the streak owner (not as the snap-claim
        # subject). Pre-week streak was -10, current is -11 →
        # "extended" evidence branch.
        assert len(streak_failures) == 1, (
            f"expected exactly one STREAK failure from the existing "
            f"possessive-object resolver; got: "
            f"{[(f.claim, f.evidence) for f in streak_failures]}"
        )
        assert "Brandon Knows Ball" in streak_failures[0].claim
        assert "losing streak was snapped" in streak_failures[0].claim
        assert "extended to 11" in streak_failures[0].evidence
        assert "not snapped" in streak_failures[0].evidence

    # ── Positive control: literal 'streak' + pronoun ─────────────
    def test_literal_streak_pronoun_unchanged(self):
        """Pin that pronoun-possessive literal 'streak' still passes through.

        Span ends on literal "streak", so the guard returns False.
        Pronoun "their" fails _POSSESSIVE_OBJECT_STREAK's
        leading-capital requirement, so the resolver also skips.
        Falls through to _find_nearby_franchise pass-1, which picks
        up "Alpha Team" before the snap verb. Alpha Team had no
        losing streak entering this week → existing heuristic emits
        a failure. This test pins that the guard does NOT silence
        the existing subject-attribution path for literal-streak
        claims.
        """
        matchups = [
            _make_matchup(1, "F_ALPHA", "F_BETA", 120, 100),
            _make_matchup(2, "F_ALPHA", "F_BETA", 115, 105),
            _make_matchup(3, "F_ALPHA", "F_BETA", 130, 90),
        ]
        reverse = {
            "Alpha Team": "F_ALPHA", "alpha team": "F_ALPHA",
            "alpha": "F_ALPHA",
            "Beta Squad": "F_BETA", "beta squad": "F_BETA",
            "beta": "F_BETA",
        }
        # Alpha Team won all three weeks — no losing streak to snap.
        # The literal-streak claim must still be caught by the
        # existing proximity heuristic.
        text = "Alpha Team snapped their losing streak with a 130-90 win."
        failures = verify_streaks(text, matchups, 3, reverse)
        streak_failures = [f for f in failures if f.category == "STREAK"]
        assert len(streak_failures) == 1, (
            f"expected exactly one STREAK failure from the existing "
            f"proximity-heuristic path; got: "
            f"{[(f.claim, f.evidence) for f in streak_failures]}"
        )
        assert "Alpha Team" in streak_failures[0].claim
        assert "no losing streak" in streak_failures[0].evidence


# ─── P1/P2 PLAYER_SCORE parse-false-positive regressions ─────────────
#
# Fixtures reproduce prompt_audit rows captured in the 2026-04-14 Q5
# resolution pass (OBSERVATIONS_2026_04_14_Q5_RESOLUTION.md):
#
#   P1: id=40 (2024 w10 a1), id=41 (2024 w10 a2)
#   P2: id=47 (2024 w14 a1), id=9  (2025 w5 a1), id=15 (2025 w9 a2)
#
# Both classes have a companion "bare claim still flags" sanity test
# to guard against the fix simply defanging verify_player_scores.
#
# Unlike TestRegressionW11W13FalsePositives (V3), the fixture below
# includes league_id and season when inserting into player_directory.
# Without them the INSERT OR IGNORE silently drops the row, the name
# map is empty, and verify_player_scores returns [] — a trivial pass
# that does not exercise the fix surface.
class TestRegressionQ5PlayerScoreFalsePositives:
    """Pin P1/P2 PLAYER_SCORE parse bugs (Q5 resolution)."""

    def _build_db(
        self, tmp_path, *, week, player_id, display_name, actual_score,
        winner_score=98.00, loser_score=90.00,
    ):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Warmongers")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Brandon")

        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=week,
                        winner_id="F1", loser_id="F2",
                        winner_score=winner_score, loser_score=loser_score)

        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=week,
                             franchise_id="F1", player_id=player_id,
                             score=actual_score)

        # Include league_id + season so the row actually lands. See class
        # docstring for why this matters.
        con.execute(
            "INSERT OR REPLACE INTO player_directory "
            "(league_id, season, player_id, name, position) "
            "VALUES (?, ?, ?, ?, ?)",
            (LEAGUE, SEASON, player_id, display_name, "WR"),
        )

        con.commit()
        con.close()
        return db_path

    # ── P1: XX.XX substring inside XXX.XX game score ─────────────────

    def test_p1_xx_xx_inside_game_score_not_flagged_row40(self, tmp_path):
        """id=40 (2024 w10 a1): game score 119.10 contains substring
        "19.10", which the unanchored XX.XX pattern matches at offset 1.
        The digit-boundary guard must skip the match rather than flag
        "19.10" against the nearest player (Ja'Marr Chase, whose actual
        score is 23.45).
        """
        db_path = self._build_db(
            tmp_path, week=10, player_id="P1",
            display_name="Chase, Ja'Marr", actual_score=23.45,
            winner_score=119.10, loser_score=89.00,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Ja'Marr Chase cruised to a 119.10-89.00 beatdown.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=10,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert player_score_failures == [], (
            f"expected no PLAYER_SCORE failures (19.10 is a substring "
            f"inside 119.10, not a standalone attribution), "
            f"got {[(f.claim, f.evidence) for f in player_score_failures]}"
        )

    def test_p1_xx_xx_inside_game_score_not_flagged_row41(self, tmp_path):
        """id=41 (2024 w10 a2): same prose pattern, different attempt.
        Confirms the guard holds across variant phrasings of the same
        XXX.XX-XX.XX construction."""
        db_path = self._build_db(
            tmp_path, week=10, player_id="P1",
            display_name="Chase, Ja'Marr", actual_score=23.45,
            winner_score=119.10, loser_score=89.00,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Ja'Marr Chase showed out in the 119.10-89.00 rout.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=10,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert player_score_failures == [], (
            f"expected no PLAYER_SCORE failures, "
            f"got {[(f.claim, f.evidence) for f in player_score_failures]}"
        )

    def test_p1_bare_xx_xx_misattribution_still_flagged(self, tmp_path):
        """Sanity: a true XX.XX misattribution (not a digit-prefixed
        substring) must still flag. The digit-boundary guard skips
        substring matches inside larger decimals only — it does not
        defang the check for standalone claims."""
        db_path = self._build_db(
            tmp_path, week=10, player_id="P1",
            display_name="Chase, Ja'Marr", actual_score=23.45,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Ja'Marr Chase posted 19.10 in the blowout.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=10,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert len(player_score_failures) == 1, (
            f"expected exactly one PLAYER_SCORE failure for 19.10 vs "
            f"actual 23.45, got "
            f"{[(f.claim, f.evidence) for f in player_score_failures]}"
        )
        assert "19.10" in player_score_failures[0].claim

    # ── P2: bench-aggregate past the existing " but " separator ──────

    def test_p2_bench_and_separator_not_flagged_row47(self, tmp_path):
        """id=47 (2024 w14 a1): "leaving Aaron Rodgers and 47.60 points
        on the bench". The separator between the player name and the
        bench total is " and ", which is not caught by the existing
        " but " guard. The P2 guard catches it via the trailing
        "points on the bench" construction."""
        db_path = self._build_db(
            tmp_path, week=14, player_id="P1",
            display_name="Rodgers, Aaron", actual_score=15.00,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "They fell short, leaving Aaron Rodgers and 47.60 points "
            "on the bench.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=14,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert player_score_failures == [], (
            f"expected no PLAYER_SCORE failures (47.60 is a bench total "
            f"past the ' and ' separator), "
            f"got {[(f.claim, f.evidence) for f in player_score_failures]}"
        )

    def test_p2_bench_with_trailing_clause_not_flagged_row9(self, tmp_path):
        """id=9 (2025 w5 a1): "Saquon Barkley and 51.50 points on the
        bench with Stefon Diggs posting 19.60". The bench construction
        immediately follows the flagged score; the trailing " with …"
        clause does not interfere with the forward-peek guard."""
        db_path = self._build_db(
            tmp_path, week=5, player_id="P1",
            display_name="Barkley, Saquon", actual_score=22.50,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Saquon Barkley and 51.50 points on the bench told the "
            "story of the week.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=5,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert player_score_failures == [], (
            f"expected no PLAYER_SCORE failures (51.50 is a bench total), "
            f"got {[(f.claim, f.evidence) for f in player_score_failures]}"
        )

    def test_p2_bench_fresh_clause_not_flagged_row15(self, tmp_path):
        """id=15 (2025 w9 a2): "Chuba Hubbard, meanwhile, left 52.60
        points on the bench, including …". Neither ' and ' nor ' but '
        separates the name from the bench total — the prose uses a
        fresh "NAME … left N.NN" construction. The trailing "points on
        the bench" marker carries the signal."""
        db_path = self._build_db(
            tmp_path, week=9, player_id="P1",
            display_name="Hubbard, Chuba", actual_score=18.40,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Chuba Hubbard, meanwhile, left 52.60 points on the bench, "
            "including a 14.60 performance from another starter.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=9,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert player_score_failures == [], (
            f"expected no PLAYER_SCORE failures (52.60 is a bench total), "
            f"got {[(f.claim, f.evidence) for f in player_score_failures]}"
        )

    def test_p2_bare_misattribution_still_flagged(self, tmp_path):
        """Sanity: a misattributed score without the "points on the
        bench" construction must still flag. The forward-peek guard is
        signature-specific, not a blanket suppression."""
        db_path = self._build_db(
            tmp_path, week=14, player_id="P1",
            display_name="Rodgers, Aaron", actual_score=15.00,
        )
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Aaron Rodgers posted 47.60 in the comeback win.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=14,
        )
        player_score_failures = [
            f for f in result.hard_failures if f.category == "PLAYER_SCORE"
        ]
        assert len(player_score_failures) == 1, (
            f"expected exactly one PLAYER_SCORE failure for 47.60 vs "
            f"actual 15.00, got "
            f"{[(f.claim, f.evidence) for f in player_score_failures]}"
        )
        assert "47.60" in player_score_failures[0].claim


# ─── S1/S2 SERIES parse-false-positive regressions ───────────────────
#
# Fixtures reproduce prompt_audit rows captured in the 2026-04-14 Q5
# resolution pass (OBSERVATIONS_2026_04_14_Q5_RESOLUTION.md):
#
#   S1: id=3  (2025 w2 a1)  — 3-part W-L-T misread as 2-part W-L
#   S2: id=18 (2025 w10 a2) — season record confused with H2H record
#
# Both classes have companion sanity tests to guard against defanging
# verify_series_records.
class TestRegressionQ5SeriesFalsePositives:
    """Pin S1/S2 SERIES parse bugs (Q5 resolution)."""

    def _reverse(self):
        return {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
            "Miller": "F3", "miller": "F3",
            "Eddie": "F4", "eddie": "F4",
        }

    # ── S1: 3-part W-L-T misread as 2-part W-L ───────────────────────

    def _s1_matchups(self):
        """Build Alpha vs Beta all-time record of 16 wins, 12 losses.
        Ties are not tracked in h2h_records, so the W-L comparison
        against a 16-12-1 claim will match on W=16, L=12."""
        matchups = []
        for w in range(1, 17):
            matchups.append(_make_matchup(w, "F1", "F2", 120.0, 100.0))
        for w in range(17, 29):
            matchups.append(_make_matchup(w, "F2", "F1", 115.0, 105.0))
        return matchups

    def test_s1_three_part_wlt_not_misread_as_wl_row3(self):
        """id=3 (2025 w2 a1): "extending their series lead to 16-12-1
        across 29 all-time meetings".

        Before the fix: greedy [^.]{0,40} backtracked to 11 chars ("lead
        to 16-"), where "12-1" became a valid W-L match with the tie
        group unfilled — misreading 16-12-1 as 12-1 and flagging it
        against a 16-12 actual. The extended lookbehind (?<![\\d-])
        forbids the match from starting after a hyphen, forcing greedy
        to find a boundary where the full triple is captured.
        """
        matchups = self._s1_matchups()
        reverse = self._reverse()
        text = (
            "Alpha Team is extending their series lead to 16-12-1 across "
            "29 all-time meetings with Beta Squad."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures (16-12-1 is the correct 3-part "
            f"record against a 16-12 actual W-L), "
            f"got {[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s1_three_part_wlt_wrong_flags_with_correct_claim_string(self):
        """Parse-correctness: when a 3-part W-L-T claim is wrong (20-8-1
        vs actual 16-12), the failure must carry the full "20-8-1"
        claim string — not a mangled "8-1" from the same S1 parse bug.

        On unfixed code: the verifier flags but misreads 20-8-1 as 8-1,
        producing claim "Series record 8-1" — a second manifestation of
        the S1 bug that would be silently shipped to commissioner review
        with wrong content. The extended lookbehind forces greedy to
        capture the full triple, and the claim string becomes accurate.

        Combines defanging-sanity (wrong claim still flags) with parse-
        correctness (claim string matches the prose). The upstream
        TestVerifySeriesRecords::test_wrong_series_record_fails covers
        pure defanging for 2-part W-L shapes.
        """
        matchups = self._s1_matchups()
        reverse = self._reverse()
        text = (
            "Alpha Team is extending their series lead to 20-8-1 across "
            "29 all-time meetings with Beta Squad."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected exactly one SERIES failure (claimed 20-8-1 vs "
            f"actual 16-12), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "20-8-1" in series_failures[0].claim, (
            f"expected claim string to carry the full 3-part record "
            f"20-8-1 (not the S1-mangled 8-1), "
            f"got claim={series_failures[0].claim!r}"
        )

    def test_s1_two_part_wl_still_parses_correctly(self):
        """Sanity: a 2-part W-L record (no tie) must still parse and
        verify correctly. The lookbehind change affects where the match
        can start, not whether the optional tie group participates."""
        matchups = self._s1_matchups()
        reverse = self._reverse()
        text = (
            "Alpha Team is extending their series lead to 16-12 against "
            "Beta Squad."
        )
        failures = verify_series_records(text, matchups, reverse)
        assert failures == [], (
            f"expected no failures for correct 16-12 claim, "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    # ── S2: season record confused with H2H series record ────────────

    def _s2_matchups(self):
        """Miller vs Eddie H2H: neither 7-3 nor reversed. Actual record
        is 4-3 (Miller leads). The 7-3 claim is Miller's SEASON record,
        not their rivalry vs Eddie."""
        matchups = []
        for w in range(1, 5):
            matchups.append(_make_matchup(w, "F3", "F4", 120.0, 100.0))
        for w in range(5, 8):
            matchups.append(_make_matchup(w, "F4", "F3", 115.0, 105.0))
        return matchups

    def test_s2_season_record_not_misread_as_h2h_row18(self):
        """id=18 (2025 w10 a2): "Josh Allen's 26.40 points led Miller
        to his second straight win and a 7-3 record".

        Before the fix: "7-3 record" matched via the second branch
        (record keyword), proximity picked Miller-Eddie as the nearest
        pair, and the Miller-Eddie H2H (4-3) failed the comparison
        → false flag. The S2 guard detects the single-team determiner
        "a " before "7-3" combined with the absence of H2H markers in
        match text and post-context, and skips the comparison.
        """
        matchups = self._s2_matchups()
        reverse = self._reverse()
        text = (
            "Josh Allen's 26.40 points led Miller to his second straight "
            "win and a 7-3 record. Eddie was competitive throughout."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures (7-3 is Miller's season W-L, "
            f"not a rivalry total vs Eddie), "
            f"got {[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s2_h2h_record_vs_opponent_still_flagged(self):
        """Sanity: a genuine H2H claim with 'vs/against' in post-context
        must still verify. The S2 guard only suppresses when the
        post-context lacks an H2H marker."""
        matchups = self._s2_matchups()
        reverse = self._reverse()
        text = (
            "Miller improved to a 7-3 record against Eddie in their "
            "all-time series."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (7-3 claim vs actual 4-3 "
            f"H2H, with 'against' + 'all-time series' making the claim "
            f"unambiguously head-to-head), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    def test_s2_series_keyword_in_match_overrides_determiner(self):
        """Sanity: when the match text itself contains an unambiguous
        H2H marker ("series", "rivalry", "all-time", "lead"), the S2
        guard does not fire regardless of determiner pre-context. The
        guard is keyed on the AMBIGUOUS "record" keyword only."""
        matchups = self._s2_matchups()
        reverse = self._reverse()
        # "a 7-3 series lead" has "series" in match text AND "lead" —
        # determiner "a" before 7-3 should NOT suppress verification.
        text = "Miller holds a 7-3 series lead over Eddie."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (unambiguous H2H claim via "
            f"'series lead'), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    # ── S3: franchise short-form matches inside player names ─────────

    def test_s3_short_form_alias_inside_player_name_not_matched(self):
        """id=3 (2025 w2 a1), second manifestation: the "brandon" short-
        form alias was matching inside the kicker name "Brandon Aubrey"
        via bare substring search, causing Brandon Knows Ball to be
        added to nearby_fids. With a canonical Brandon-vs-Ben H2H pair
        in the matchups table whose actual record doesn't match the
        claim, the misattribution fires a false SERIES flag.

        The real franchise in the row 3 prose ("Paradis' Playmakers")
        sits outside the 300-char context window, so the correct
        outcome after removing the short-form hazard is silence:
        nearby_fids drops below two and the check skips without
        flagging.

        Fixture reproduces the bug: Brandon-vs-Ben canonical record is
        10-5 (not 16-12-1), and the prose claims 16-12-1. On unfixed
        code the short-form match fires the flag; on fixed code the
        short-form is rejected and the check silently skips.
        """
        # Build matchups where Brandon Knows Ball (F5) vs Ben's Gods
        # (F6) actual record is 10-5. The 16-12-1 claim in prose does
        # not match this — on unfixed code, the nearby-pair check picks
        # up both franchises (brandon-inside-Aubrey + ben's-gods-full)
        # and the false-attribution path fires.
        matchups = []
        for w in range(1, 11):
            matchups.append(_make_matchup(w, "F5", "F6", 120.0, 100.0))
        for w in range(11, 16):
            matchups.append(_make_matchup(w, "F6", "F5", 115.0, 105.0))
        reverse = {
            "Brandon Knows Ball": "F5",
            "brandon knows ball": "F5",
            "brandon": "F5",  # single-word alias — the hazard surface
            "Ben's Gods": "F6",
            "ben's gods": "F6",
        }
        text = (
            "Jonathan Taylor led the charge with 28.50 points, while "
            "Brandon Aubrey kicked his way to 24.50 points. Ben's Gods "
            "lost the matchup 169.60-128.75, extending the series lead "
            "to 16-12-1 across 29 all-time meetings."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        # Brandon Knows Ball should NOT be added to nearby_fids via the
        # "brandon" short-form match inside "Brandon Aubrey". With only
        # Ben's Gods correctly identified, nearby_fids has one entry
        # and verify_series_records exits silently.
        assert series_failures == [], (
            f"expected no SERIES failures (brandon short-form inside "
            f"'Brandon Aubrey' should not add Brandon Knows Ball to "
            f"nearby_fids), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s3_short_form_alias_as_franchise_subject_still_matches(self):
        """Sanity: a legitimate franchise short-form used as a subject
        (lowercase-verb follow like "Alpha won") must still match. The
        lookahead rejects only whitespace + capital letter, not general
        usage."""
        matchups = self._s1_matchups()
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1", "alpha": "F1",
            "Beta Squad": "F2", "beta squad": "F2", "beta": "F2",
        }
        # Both short-forms used as franchise subjects followed by
        # lowercase words — Alpha "extended" and "over Beta across".
        # The 16-12 claim is correct; verifier should match the pair
        # via short-form aliases and pass cleanly.
        text = (
            "Alpha extended their all-time series record over Beta to "
            "16-12 across 28 meetings."
        )
        failures = verify_series_records(text, matchups, reverse)
        assert failures == [], (
            f"expected no failures — alpha/beta short-forms as "
            f"franchise subjects should match and the 16-12 claim "
            f"should verify correctly, "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_s3_multi_word_franchise_name_always_matches(self):
        """Sanity: multi-word franchise names (interior whitespace)
        use the simple \\b rule regardless of following capital — a
        space inside the name already aligns it to franchise boundaries,
        so "Brandon Knows Ball Aubrey" (hypothetical) would still
        correctly match the franchise."""
        matchups = self._s1_matchups()
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1",
            "Beta Squad": "F2", "beta squad": "F2",
        }
        # Multi-word "Alpha Team" directly in prose with a wrong claim.
        text = (
            "Alpha Team improved their all-time series record to 20-8 "
            "against Beta Squad."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (20-8 claim vs actual 16-12 "
            f"H2H), got {[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "20-8" in series_failures[0].claim

    # ── S4: season-record idiom pre-context misread as H2H ───────────

    def _s4_row17_matchups(self):
        """Paradis' Playmakers vs Italian Cavallini H2H: 13-12 (25
        meetings). Neither 8-2 nor 2-8. The 8-2 claim in the captured
        row-17 prose is Paradis' season W-L after W10, not the
        Paradis-vs-Italian rivalry total."""
        matchups = []
        for w in range(1, 14):
            matchups.append(_make_matchup(w, "F_PP", "F_IC", 120.0, 100.0))
        for w in range(14, 26):
            matchups.append(_make_matchup(w, "F_IC", "F_PP", 115.0, 105.0))
        return matchups

    def _s4_row17_reverse(self):
        """Reverse name map with Paradis' Playmakers / Italian
        Cavallini plus the short-form owner aliases that appear in the
        captured prose (KP, Michele, Paradis). Single-word aliases
        pass the S3 word-boundary check in context."""
        return {
            "Paradis' Playmakers": "F_PP", "paradis' playmakers": "F_PP",
            "paradis": "F_PP", "kp": "F_PP",
            "Italian Cavallini": "F_IC", "italian cavallini": "F_IC",
            "michele": "F_IC",
        }

    def test_s4_moved_to_idiom_not_misread_as_h2h_row17(self):
        """id=17 (2025 w10 a1) captured prose middle paragraph:

            "...KP's team moved to 8-2 and maintains the league's
             best record despite leaving 36.45 points on the bench..."

        Before S4: Branch-2 of _SERIES_RECORD_PATTERN fires on
        "8-2 and maintains the league's best record" (38 chars
        between "8-2" and "record", inside the 40-char window).
        match text contains "record" but none of the narrow H2H
        markers (series/rivalry/meetings/all-time/lead/head-to-head)
        — S2's marker path does not trigger. Pre-context ends with
        "moved to " — not a determiner — so S2's determiner path
        does not trigger either. Falls through to H2H comparison,
        which pulls Paradis' Playmakers and Italian Cavallini from
        the 300-char window, compares claimed 8-2 to canonical
        13-12, and flags.

        After S4: idiom "moved to " at the end of the 40-char
        pre-context matches _SEASON_RECORD_IDIOM_PATTERN. Since
        post-context within 40 chars of match.end() has no H2H
        marker either, the guard skips.
        """
        matchups = self._s4_row17_matchups()
        reverse = self._s4_row17_reverse()
        text = (
            "The week belonged to Jonathan Taylor, who posted 48.10 "
            "points for Paradis' Playmakers in their 137.50-103.10 "
            "win over Italian Cavallini. That's the highest "
            "individual score by any starter this season, topping "
            "the previous mark of 46.75. KP's team moved to 8-2 and "
            "maintains the league's best record despite leaving "
            "36.45 points on the bench with Daniel Jones sitting at "
            "20.05. Michele's Italian Cavallini dropped to 5-5 "
            "after leaving 59.20 bench points, led by Tyler "
            "Allgeier's 17.70."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures (8-2 is Paradis' season "
            f"record after W10, not the Paradis-vs-Italian "
            f"Cavallini 13-12 H2H), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s4_dropped_to_idiom_with_record_keyword_skipped(self):
        """Synthetic: "Miller dropped to 5-5 record after today's
        loss." The pattern fires on 5-5 via Branch-2 trailing
        "record". match text has "record" but no narrow H2H marker
        — S2's marker path passes through. Pre-context ends with
        "dropped to " — not a determiner — S2's determiner path
        passes through. On unfixed code, the verifier falls to H2H
        comparison: Miller (F3) and Eddie (F4) both appear in the
        300-char window, canonical H2H is 4-3, 5-5 ≠ 4-3 and ≠ 3-4
        → false SERIES flag. On fixed code, S4 idiom "dropped to "
        catches it and skips.
        """
        matchups = self._s2_matchups()
        reverse = self._reverse()
        text = (
            "Miller dropped to 5-5 record after today's loss. "
            "Eddie remains one game back."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures (5-5 is Miller's season "
            f"record; S4 'dropped to' idiom should skip), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s4_idiom_verb_sweep(self):
        """Every verb/locative in _SEASON_RECORD_IDIOM_PATTERN must
        suppress a season-record misread. Each phrasing pairs a
        wrong 5-5 claim with the Miller-vs-Eddie 4-3 canonical H2H
        — if the idiom doesn't trigger the skip, the verifier flags.

        Sweep covers all 10 idioms:
          moved to, dropped to, fell to, improved to, climbed to,
          rose to, advanced to, sits at, stands at, now at.
        """
        matchups = self._s2_matchups()
        reverse = self._reverse()
        variants = [
            "Miller moved to 5-5 record after today's loss. Eddie remains one game back.",
            "Miller dropped to 5-5 record after today's loss. Eddie remains one game back.",
            "Miller fell to 5-5 record after today's loss. Eddie remains one game back.",
            "Miller improved to 5-5 record after today's win. Eddie remains one game back.",
            "Miller climbed to 5-5 record after today's win. Eddie remains one game back.",
            "Miller rose to 5-5 record after today's win. Eddie remains one game back.",
            "Miller advanced to 5-5 record after today's win. Eddie remains one game back.",
            "Miller sits at 5-5 record after today's game. Eddie remains one game back.",
            "Miller stands at 5-5 record after today's game. Eddie remains one game back.",
            "Miller is now at 5-5 record after today's game. Eddie remains one game back.",
        ]
        for text in variants:
            failures = verify_series_records(text, matchups, reverse)
            series_failures = [
                f for f in failures if f.category == "SERIES"
            ]
            assert series_failures == [], (
                f"expected no SERIES failures for S4 idiom variant "
                f"{text!r}, got "
                f"{[(f.claim, f.evidence) for f in series_failures]}"
            )

    def test_s4_idiom_with_h2h_post_context_still_flagged(self):
        """Scope-guard: S4 is gated by `not _s2_has_h2h_context`. An
        idiom followed by an H2H marker in the 40-char post-context
        ("vs/versus/against/head-to-head/all-time") must not
        suppress a legitimately verifiable H2H claim.

        "Miller moved to 7-3 record versus Eddie" — the Branch-2
        match captures "7-3 record" (greedy `[^.]{0,40}` backtracks
        to length 0 so "record" fits at offset 4). match text has
        no narrow H2H marker. Pre-context has the "moved to " idiom
        (S4 triggers). BUT post-context "versus Eddie." contains
        "versus" → H2H context overrides → skip suppressed →
        comparison runs → 7-3 ≠ actual 4-3 → flag.
        """
        matchups = self._s2_matchups()
        reverse = self._reverse()
        text = "Miller moved to 7-3 record versus Eddie."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (7-3 claim with "
            f"'versus Eddie' H2H post-context overrides S4 skip; "
            f"vs canonical 4-3), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    def test_s4_h2h_marker_in_match_text_overrides_idiom(self):
        """Scope-guard: when the match text itself contains a narrow
        H2H marker (series/rivalry/all-time/meetings/lead/head-to-
        head), the S2/S4 branch is never entered. Idiom
        pre-context cannot suppress in that case.

        "Miller moved to 7-3 series lead over Eddie" — greedy
        Branch-2 captures "7-3 series lead" (lead is further into
        the trailing window than series, so greedy prefers it).
        match text has both "series" and "lead" → h2h_marker True
        → S4 branch not entered → comparison runs → 7-3 ≠ actual
        4-3 → flag.
        """
        matchups = self._s2_matchups()
        reverse = self._reverse()
        text = "Miller moved to 7-3 series lead over Eddie."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (unambiguous H2H claim "
            f"via 'series lead' overrides idiom, 7-3 vs actual 4-3), "
            f"got {[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    def test_s4_absent_idiom_absent_determiner_falls_through(self):
        """Regression guard: when pre-context has no determiner
        (S2 shape), no idiom (S4 shape), and no possessive-'s
        (S6 shape), the verifier must still verify as before. The
        test prose "The 7-3 record for Miller was notable" fires
        Branch-2 on "7-3 record" (keyword "record" 13 chars after
        the W-L, inside the 40-char window). Pre-context ends with
        "The " — not a determiner, not an idiom, not a possessive.
        Match text contains only "record" (ambiguous keyword, no
        h2h marker), post-context has no H2H language → falls
        through to H2H comparison → 7-3 ≠ actual 4-3 → flag. This
        test asserts the skip heuristics did not broaden beyond
        their intended shapes.
        """
        matchups = self._s2_matchups()
        reverse = self._reverse()
        text = "The 7-3 record for Miller was notable. Eddie was in the game."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (no determiner, no idiom, "
            f"no possessive; 7-3 must still fall through to H2H "
            f"comparison vs canonical 4-3), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    # ── S5: parenthesized-WL standings list misread as H2H ───────────

    def _s5_w13_matchups(self):
        """Alpha Team vs Miller H2H: 4-1 (5 meetings). Neither 11-2
        nor 9-4 nor 8-5. The W-Ls in the captured W13 row are
        standings-list season records (KP at 11-2, Miller at 9-4,
        Steve at 8-5, Pat at 8-5) — not any pair's rivalry total.
        Under pre-S5 logic the match fell through to H2H comparison,
        was misattributed to a pair pulled from the 300-char window,
        and flagged against that pair's actual H2H."""
        matchups = []
        for w in range(1, 5):
            matchups.append(_make_matchup(w, "F1", "F3", 120.0, 100.0))
        matchups.append(_make_matchup(5, "F3", "F1", 115.0, 105.0))
        return matchups

    def _s5_w13_reverse(self):
        """Reverse name map with the short-form aliases that appear
        in the captured W13 prose (KP, Miller, Steve, Pat)."""
        return {
            "Alpha Team": "F1", "alpha team": "F1",
            "Miller": "F3", "miller": "F3",
            "Steve": "F5", "steve": "F5",
            "KP": "F6", "kp": "F6",
            "Pat": "F7", "pat": "F7",
        }

    def test_s5_paren_standings_list_not_misread_as_h2h_w13(self):
        """2025 W13 approved recap captured prose:

            "The playoff picture tightens with five weeks left. KP
             holds a commanding lead at 11-2, while Miller (9-4),
             Steve (8-5), and Pat (8-5) battle for the remaining
             spots."

        Before S5: greedy Branch-1 captures "lead at 11-2, while
        Miller (9-4), Steve (8-5" — keyword "lead" + 37-char gap +
        W-L "8-5". match.group(0) contains three W-L tokens
        including `(9-4)` inside parens. has_h2h_marker=True
        ("lead" in match), so the existing S2/S4 guard does NOT
        skip. The verifier falls through to H2H comparison: nearby
        franchises (KP, Miller, Steve, Pat) pull a pair from the
        300-char window, claim 8-5 fails that pair's real H2H →
        false SERIES flag.

        After S5: `(9-4)` inside match.group(0) matches
        _S5_PAREN_WL. S5 is evaluated BEFORE the has_h2h_marker
        check, so the paren signal overrides the "lead" marker.
        Skip fires.
        """
        matchups = self._s5_w13_matchups()
        reverse = self._s5_w13_reverse()
        text = (
            "The playoff picture tightens with five weeks left. KP "
            "holds a commanding lead at 11-2, while Miller (9-4), "
            "Steve (8-5), and Pat (8-5) battle for the remaining spots."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures for paren-standings-list "
            f"prose (W-L tokens are season records, parenthesized "
            f"format is never used for H2H series), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s5_paren_wl_overrides_h2h_marker_in_match(self):
        """Scope-guard: S5 is evaluated BEFORE the has_h2h_marker
        check and fires even when the match text contains an
        unambiguous H2H marker like "lead"/"leads"/"series".
        Rationale: in standings prose "lead" frames a conference
        or division lead, not a series lead. The parenthesized
        W-L format `(W-L)` is specific to standings listings and
        never appears in real H2H series prose.

        "Alpha Team leads the pack at 8-2, with Miller (6-4)
        trailing behind." — greedy Branch-1 captures through the
        "(6-4" paren. has_h2h_marker=True ("leads" in match).
        Pre-S5, skip would be blocked by the h2h_marker veto →
        falls through → Alpha-vs-Miller canonical 4-1 ≠ claimed
        8-2 → flag. Post-S5, the paren-WL check fires first and
        skips.
        """
        matchups = self._s5_w13_matchups()
        reverse = self._s5_w13_reverse()
        text = (
            "Alpha Team leads the pack at 8-2, with Miller (6-4) "
            "trailing behind."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures (paren W-L standings-list "
            f"signal overrides h2h marker 'leads' in match), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s5_no_paren_falls_through_to_h2h(self):
        """Sanity: a bare "leads the series X-Y" claim without
        any parenthesized W-L must still fall through to H2H
        verification. Ensures S5 did not over-broaden into
        unconditionally skipping any match containing a list-like
        comma.

        With Alpha vs Miller canonical H2H 4-1, claim "8-2" fails
        comparison → flag."""
        matchups = self._s5_w13_matchups()
        reverse = self._s5_w13_reverse()
        text = "Alpha Team leads the series 8-2 against Miller."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (no paren W-L to trigger "
            f"S5 skip; 8-2 claim vs canonical 4-1 H2H), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "8-2" in series_failures[0].claim

    # ── S6: possessive proper-noun pre-context misread as H2H ────────

    def _s6_w10_matchups(self):
        """Purple Haze vs Stu's Crew H2H: 9-12 (21 meetings).
        Neither 8-2 nor 2-8. The 8-2 claim in the captured W10 row
        is Pat's season record, not a PH-vs-SC rivalry total."""
        matchups = []
        for w in range(1, 10):
            matchups.append(_make_matchup(w, "F_PH", "F_SC", 120.0, 100.0))
        for w in range(10, 22):
            matchups.append(_make_matchup(w, "F_SC", "F_PH", 115.0, 105.0))
        return matchups

    def _s6_w10_reverse(self):
        """Reverse name map for the W10 captured prose."""
        return {
            "Purple Haze": "F_PH", "purple haze": "F_PH",
            "Stu's Crew": "F_SC", "stu's crew": "F_SC",
            "stu": "F_SC",
            "Pat": "F7", "pat": "F7",
            "Steve": "F5", "steve": "F5",
        }

    def test_s6_possessive_season_record_not_misread_as_h2h_w10(self):
        """2025 W10 approved recap captured prose:

            "...Stu knocked off Purple Haze 112.70-93.40 despite
             having two starters on bye — the most in the league
             this week. Pat's 8-2 record took its first hit in two
             weeks, but he's still tied for the division lead."

        Before S6: Branch-2 of _SERIES_RECORD_PATTERN fires on
        "8-2 record" (keyword "record" immediately after W-L).
        match text contains "record" but no narrow H2H marker —
        S2's marker path passes through. Pre-context ends with
        "Pat's " — not in S2's determiner set (a/an/his/her/their),
        not an S4 idiom. Falls through to H2H comparison: Purple
        Haze and Stu's Crew both appear in the 300-char window,
        claim 8-2 compared against their 9-12 canonical H2H →
        false SERIES flag.

        After S6: pre-40 "Pat's " matches \\w{2,}[\u2019']s\\s+$
        possessive pattern → skip.
        """
        matchups = self._s6_w10_matchups()
        reverse = self._s6_w10_reverse()
        text = (
            "Stu knocked off Purple Haze 112.70-93.40 despite having "
            "two starters on bye — the most in the league this week. "
            "Pat's 8-2 record took its first hit in two weeks, but "
            "he's still tied for the division lead."
        )
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"expected no SERIES failures (8-2 is Pat's season "
            f"record, marked by possessive 'Pat's' in pre-context, "
            f"not a series record between any pair), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )

    def test_s6_possessive_with_h2h_post_context_still_flagged(self):
        """Scope-guard: S6, like S2/S4, is gated by
        `not has_post_h2h`. A possessive construction followed by
        an H2H marker like "vs"/"against" in the 40-char post-window
        must not suppress a legitimately verifiable H2H claim.

        "Pat's 7-3 record against Miller..." — pre-40 ends with
        "Pat's " (S6 would fire alone), but post-40 contains
        "against" (h2h context overrides) → skip suppressed →
        comparison runs → 7-3 ≠ actual 4-1 → flag.
        """
        matchups = self._s5_w13_matchups()  # Alpha/Pat vs Miller 4-1
        reverse = {
            "Alpha Team": "F1", "alpha team": "F1",
            "Miller": "F3", "miller": "F3",
            # Alias Pat to Alpha's franchise so the nearby pair is
            # (F1, F3) with canonical 4-1 H2H.
            "Pat": "F1", "pat": "F1",
        }
        text = "Pat's 7-3 record against Miller tells the story."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (possessive 'Pat's' + "
            f"post-context 'against Miller' is a legitimate H2H "
            f"claim; 7-3 vs canonical 4-1), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    def test_s6_h2h_marker_in_match_text_overrides_possessive(self):
        """Scope-guard: when match text itself contains a narrow
        H2H marker (series/rivalry/all-time/meetings/lead/head-to-
        head), _should_skip_series_match returns False before any
        pre-context check runs. Possessive pre-context cannot
        suppress in that case.

        "Miller's 7-3 all-time record vs Alpha" — greedy Branch-2
        captures with "all-time" and "record" inside match. match
        text has "all-time" (h2h marker) → h2h_marker=True →
        helper returns False immediately. Possessive "Miller's "
        never gets evaluated. 7-3 ≠ canonical 4-1 → flag.
        """
        matchups = self._s5_w13_matchups()
        reverse = self._s5_w13_reverse()
        text = "Miller's 7-3 all-time record against Alpha Team."
        failures = verify_series_records(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"expected one SERIES failure (unambiguous 'all-time' "
            f"h2h marker in match overrides possessive pre-context; "
            f"7-3 vs canonical 4-1), got "
            f"{[(f.claim, f.evidence) for f in series_failures]}"
        )
        assert "7-3" in series_failures[0].claim

    def test_s6_possessive_apostrophe_sweep(self):
        """The possessive-'s regex must handle both straight
        (U+0027) and curly (U+2019) apostrophes — LLM outputs
        freely mix both, and recap_text is not apostrophe-
        normalized before the skip heuristic runs."""
        matchups = self._s6_w10_matchups()
        reverse = self._s6_w10_reverse()
        variants = [
            # Straight apostrophe (U+0027)
            "Stu knocked off Purple Haze. Pat's 8-2 record took its first hit.",
            # Curly apostrophe (U+2019)
            "Stu knocked off Purple Haze. Pat\u2019s 8-2 record took its first hit.",
        ]
        for text in variants:
            failures = verify_series_records(text, matchups, reverse)
            series_failures = [
                f for f in failures if f.category == "SERIES"
            ]
            assert series_failures == [], (
                f"expected no SERIES failures for possessive-'s "
                f"apostrophe variant {text!r}, got "
                f"{[(f.claim, f.evidence) for f in series_failures]}"
            )

    def test_s5_s6_apply_in_cross_week_extract_too(self):
        """Integration guard: _should_skip_series_match is called
        from both verify_series_records AND _extract_series_claims
        (which feeds verify_cross_week_consistency). The cross-week
        consistency check must NOT extract claims from prose that
        the per-week check correctly ignored — otherwise a
        legitimate W4 series claim paired with a W10 possessive
        season-record "claim" produces a false cross-week
        CONSISTENCY flag even though the per-week SERIES check
        passes W10.

        This mirrors the 2025 W4/W10 cross-week flag observed
        before S6 landed: W4 "leads the series 9-12" (real,
        verified) paired with W10 "Pat's 8-2 record"
        (fabrication-shaped, S6-skipped) must not produce a
        cross-week CONSISTENCY failure.
        """
        reverse = self._s6_w10_reverse()
        reverse.update({
            "Alpha Team": "F_PH", "alpha team": "F_PH",
        })
        week_narratives = [
            (4, "Alpha Team leads the series 9-12 against Stu's Crew."),
            (10, "Pat's 8-2 record took its first hit in two weeks."),
        ]
        failures = verify_cross_week_consistency(week_narratives, reverse)
        consistency_failures = [
            f for f in failures if f.category == "CONSISTENCY"
        ]
        assert consistency_failures == [], (
            f"expected no CONSISTENCY failures (W10 'Pat's 8-2 "
            f"record' is a possessive season record, must not be "
            f"extracted as a series claim against W4's legitimate "
            f"9-12), got "
            f"{[(f.claim, f.evidence) for f in consistency_failures]}"
        )


# ─── V7 SUPERLATIVE forward-lookback regressions ─────────────────────
#
# Captured prompt_audit row 17 (2025 w10 a1):
#   "...That's the highest individual score by any starter this
#    season, topping the previous mark of 46.75."
#
# _has_previous_qualifier's 40-char backward window missed the
# disambiguating phrase because "topping the previous mark" sits
# AFTER the "highest" trigger. Without a forward scan, the verifier
# pulled 103.10 (the losing team's game score in the prior sentence,
# nearest XX.XX to "highest") and flagged a false SUPERLATIVE.
#
# The fix is strictly additive: backward scan runs first and returns
# early on match; the forward scan only runs on a backward miss, is
# bounded by the first sentence-terminal punctuation, and requires an
# explicit comparison-verb + qualifier construction (not bare
# "previous") to avoid over-skipping narratively unrelated prose.
class TestRegressionV7SuperlativeForwardLookback:
    """Pin the V7 forward-lookback fix for _has_previous_qualifier."""

    # ── V7: captured-prose target (row 17) ───────────────────────────

    def test_v7_captured_row17_topping_previous_mark_not_flagged(self):
        """id=17 (2025 w10 a1) captured prose:

            "Jonathan Taylor posted 48.10 points for Paradis' Playmakers
             in their 137.50-103.10 win over Italian Cavallini. That's
             the highest individual score by any starter this season,
             topping the previous mark of 46.75."

        Before V7: backward window from "highest" sees only
        "...over Italian Cavallini. That's the " — no qualifier — so
        the helper returned False and _extract_nearby_score pulled
        103.10 (nearest XX.XX to "highest"), which matches neither
        actual_season_high_team (137.50) nor season_player_high
        (48.10) → false SUPERLATIVE flag. After V7: forward scan sees
        "topping the previous mark" in the same sentence → skip.
        """
        text = (
            "Jonathan Taylor posted 48.10 points for Paradis' Playmakers "
            "in their 137.50-103.10 win over Italian Cavallini. That's "
            "the highest individual score by any starter this season, "
            "topping the previous mark of 46.75."
        )
        matchups = [_make_matchup(10, "F1", "F2", 137.50, 103.10)]
        failures = verify_superlatives(
            text, matchups, None, SEASON, 48.10, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert high_failures == [], (
            f"expected no season-high failure for 'topping the "
            f"previous mark' (V7 forward-lookback), "
            f"got {[(f.claim, f.evidence) for f in high_failures]}"
        )

    # ── V7: symmetric coverage across the three superlative loops ────

    def test_v7_season_low_breaking_prior_not_flagged(self):
        """Symmetric SEASON_LOW case: 'breaking the prior low of X'
        after the 'lowest of the season' trigger must also skip.

        Fixture shape mirrors the captured row-17 structure: the
        nearest XX.XX to the 'lowest' trigger is a score from the
        prior clause (92.10, one side of the reported matchup), NOT
        the actual season minimum (80.00 from a different matchup).
        Without V7 the verifier would extract 92.10 and flag against
        actual 80.00; with V7 the forward scan finds 'breaking the
        prior low' and skips.
        """
        text = (
            "Italian Cavallini's 92.10 loss in the 137.50-92.10 "
            "matchup was the lowest of the season, breaking the "
            "prior low of 45.00."
        )
        matchups = [
            _make_matchup(1, "F1", "F2", 137.50, 92.10),
            _make_matchup(2, "F3", "F4", 130.00, 80.00),  # actual low = 80
        ]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        low_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "low" in f.claim.lower()
        ]
        assert low_failures == [], (
            f"expected no season-low failure for 'breaking the prior "
            f"low' (V7 forward-lookback, SEASON_LOW parity), "
            f"got {[(f.claim, f.evidence) for f in low_failures]}"
        )

    def test_v7_alltime_surpassing_previous_record_not_flagged(self):
        """Symmetric ALLTIME case: 'surpassing the previous record of
        X' after the 'league history' trigger must also skip.

        Fixture shape mirrors row 17: nearest XX.XX to 'league
        history' is 103.10 (the losing team in a prior-sentence
        matchup), NOT the actual all-time high (220.00 from an older
        season). Without V7 the verifier flags 103.10 against 220.00;
        with V7 'surpassing the previous record' skips.
        """
        text = (
            "Bob won 137.50-103.10 over Carl in a blowout. That "
            "result was the highest in league history, surpassing "
            "the previous record of 198.80."
        )
        season = [_make_matchup(1, "F1", "F2", 137.50, 103.10)]
        alltime = season + [_make_matchup(1, "F1", "F2", 220.00, 90.00)]
        failures = verify_superlatives(
            text, season, alltime, SEASON, None, None,
        )
        alltime_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "all-time" in f.claim.lower()
        ]
        assert alltime_failures == [], (
            f"expected no all-time failure for 'surpassing the "
            f"previous record' (V7 forward-lookback, ALLTIME parity), "
            f"got {[(f.claim, f.evidence) for f in alltime_failures]}"
        )

    def test_v7_synonym_verbs_eclipsing_beating_exceeded(self):
        """Synonym sweep: the full verb set recognised by the forward
        pattern (topping/breaking/surpassing/eclipsing/beating/
        exceeding/overtaking/overtook) must each trigger the skip.

        Fixture shape mirrors row 17 so the extracted nearby score
        (103.10, losing team from prior sentence) differs from the
        actual season-high (137.50) — i.e. the unfixed verifier would
        flag on every variant below.
        """
        variants = [
            "Bob won 137.50-103.10. That's the highest of the season, eclipsing the prior mark of 48.10.",
            "Bob won 137.50-103.10. That's the highest of the season, beating the previous best of 48.10.",
            "Bob won 137.50-103.10. That's the highest of the season, exceeded the old record of 48.10.",
            "Bob won 137.50-103.10. That's the highest of the season, overtook the prior high of 48.10.",
            "Bob won 137.50-103.10. That's the highest of the season, broke the previous mark of 48.10.",
        ]
        matchups = [_make_matchup(1, "F1", "F2", 137.50, 103.10)]
        for text in variants:
            failures = verify_superlatives(
                text, matchups, None, SEASON, None, None,
            )
            high_failures = [
                f for f in failures if f.category == "SUPERLATIVE"
                and "high" in f.claim.lower()
            ]
            assert high_failures == [], (
                f"expected no season-high failure for V7 verb variant "
                f"{text!r}, got {[(f.claim, f.evidence) for f in high_failures]}"
            )

    # ── V7: conservative-guard boundaries ────────────────────────────

    def test_v7_forward_qualifier_past_period_does_not_skip(self):
        """Sentence-boundary guard: a 'topping the previous' phrase
        sitting in the NEXT sentence must not leak backward and cause
        a spurious skip. The period between the two sentences stops
        the forward scan.

        Wrong claim: 103.10 is NOT the season high (137.50 is). The
        unrelated "topping the previous week's mark" in the next
        sentence must not defang the verifier.
        """
        text = (
            "That 103.10 is the season high. Bob kept topping the "
            "previous week's mark all year."
        )
        matchups = [_make_matchup(1, "F1", "F2", 137.50, 103.10)]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert len(high_failures) == 1, (
            f"expected one season-high failure — V7 forward scan must "
            f"not cross a sentence-terminal '.', "
            f"got {[(f.claim, f.evidence) for f in high_failures]}"
        )
        assert "103.10" in high_failures[0].claim

    def test_v7_comparison_verb_without_qualifier_does_not_skip(self):
        """Narrow-scope guard: the forward pattern requires a
        recognised qualifier (previous/prior/former/past/old) in
        addition to the comparison verb. A verb-only phrase like
        'topping teammate Bob's earlier 118' is NOT disambiguating
        and must not cause a skip.

        Wrong claim: 103.10 is not the season high.
        """
        text = (
            "That 103.10 was the season high, topping teammate Bob's "
            "earlier 118 with room to spare."
        )
        matchups = [_make_matchup(1, "F1", "F2", 137.50, 103.10)]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert len(high_failures) == 1, (
            f"expected one season-high failure — V7 forward pattern "
            f"requires verb+qualifier, not bare verb, "
            f"got {[(f.claim, f.evidence) for f in high_failures]}"
        )
        assert "103.10" in high_failures[0].claim

    def test_v7_bare_previous_without_comparison_verb_does_not_skip(self):
        """Narrow-scope guard: a bare 'previous' forward — without a
        recognised comparison verb — must not cause a skip. This is
        the wider-slice parity of the backward helper's tightness:
        the forward window is wider (to end-of-sentence, up to 120
        chars), so it requires explicit verb framing.

        Wrong claim: 103.10 is not the season high; 'his previous
        game was only 80' is narratively unrelated to the superlative.
        """
        text = (
            "That 103.10 was the season high this week, while his "
            "previous game was only 80 points."
        )
        matchups = [_make_matchup(1, "F1", "F2", 137.50, 103.10)]
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        high_failures = [
            f for f in failures if f.category == "SUPERLATIVE"
            and "high" in f.claim.lower()
        ]
        assert len(high_failures) == 1, (
            f"expected one season-high failure — bare forward "
            f"'previous' without comparison verb must not skip, "
            f"got {[(f.claim, f.evidence) for f in high_failures]}"
        )
        assert "103.10" in high_failures[0].claim

    # ── V7: V1-corpus compatibility (backward path unchanged) ────────

    def test_v7_backward_qualifier_still_skips_unchanged(self):
        """V1 backward-path parity: prose with 'previous' BEFORE the
        trigger still skips via the unchanged backward scan. V7 is
        purely additive — backward returns True first and short-
        circuits before the forward scan runs.
        """
        text = "That 51.85 topped the previous season high of 48.10."
        matchups = [_make_matchup(1, "F1", "F2", 120.00, 100.00)]
        failures = verify_superlatives(
            text, matchups, None, SEASON, 51.85, None,
        )
        assert failures == [], (
            f"expected no failures — backward 'previous' still skips "
            f"(V1 path unchanged), got {[(f.claim, f.evidence) for f in failures]}"
        )


# ── Category 7: Player-Franchise Attribution ────────────────────────


class TestPlayerFranchiseAttribution:
    """Pin Finding 4 from OBSERVATIONS_2026_04_15: cross-franchise
    misattribution passes PLAYER_SCORE but should be caught by
    PLAYER_FRANCHISE.

    The Finding 4 pattern: Watson (franchise 0002) scored 22.90 but the
    model wrote his score into a paragraph about Paradis' Playmakers
    (franchise 0008) vs Brandon (franchise 0003). The score is real, so
    PLAYER_SCORE passes. The franchise context is wrong.
    """

    def _build_db(self, tmp_path):
        """Three-franchise setup: Watson on F_STEVE, matchup is F_KP vs F_BRANDON."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F_STEVE", name="Steve's Warmongers")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F_KP", name="Paradis' Playmakers")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F_BRANDON", name="Brandon Knows Ball")

        # Watson is on F_STEVE, not F_KP
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=14,
                             franchise_id="F_STEVE", player_id="P_WATSON",
                             score=22.90)

        # Taylor is on F_KP (correct attribution baseline)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=14,
                             franchise_id="F_KP", player_id="P_TAYLOR",
                             score=48.10)

        # Matchup: F_KP vs F_BRANDON (Watson's franchise not involved)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=14,
                        winner_id="F_KP", loser_id="F_BRANDON",
                        winner_score=150.00, loser_score=44.00)

        # Matchup: F_STEVE vs some other team (not relevant to the test
        # but ensures Watson's franchise has a matchup)
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F_OTHER", name="Other Team")
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=14,
                        winner_id="F_STEVE", loser_id="F_OTHER",
                        winner_score=120.00, loser_score=90.00)

        con.execute(
            "INSERT OR REPLACE INTO player_directory "
            "(league_id, season, player_id, name, position) "
            "VALUES (?, ?, ?, ?, ?)",
            (LEAGUE, SEASON, "P_WATSON", "Watson, Christian", "WR"),
        )
        con.execute(
            "INSERT OR REPLACE INTO player_directory "
            "(league_id, season, player_id, name, position) "
            "VALUES (?, ?, ?, ?, ?)",
            (LEAGUE, SEASON, "P_TAYLOR", "Taylor, Jonathan", "RB"),
        )

        con.commit()
        con.close()
        return db_path

    def test_wrong_franchise_flags_finding4_pattern(self, tmp_path):
        """Finding 4: Watson (on Steve's) mentioned with score in a
        paragraph about Paradis' Playmakers vs Brandon. Neither franchise
        is Watson's. Must flag PLAYER_FRANCHISE HARD."""
        db_path = self._build_db(tmp_path)
        name_map = {"F_STEVE": "Steve's Warmongers",
                     "F_KP": "Paradis' Playmakers",
                     "F_BRANDON": "Brandon Knows Ball",
                     "F_OTHER": "Other Team"}
        reverse = _build_reverse_name_map(name_map)

        text = (
            "Paradis' Playmakers blew out Brandon Knows Ball by 106.60. "
            "Christian Watson added 22.90 in his first week since a "
            "$20 FAAB pickup."
        )
        failures = verify_player_franchise(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
            week=14, reverse_name_map=reverse,
        )
        pf = [f for f in failures if f.category == "PLAYER_FRANCHISE"]
        assert len(pf) == 1, (
            f"expected exactly 1 PLAYER_FRANCHISE failure, "
            f"got {len(pf)}: {[(f.claim, f.evidence) for f in pf]}"
        )
        assert pf[0].severity == "HARD"
        assert "christian watson" in pf[0].claim.lower()
        assert "Steve's Warmongers" in pf[0].evidence

    def test_correct_franchise_passes(self, tmp_path):
        """Taylor (on F_KP) mentioned with score in a paragraph about
        Paradis' Playmakers. Correct attribution — no failure."""
        db_path = self._build_db(tmp_path)
        name_map = {"F_STEVE": "Steve's Warmongers",
                     "F_KP": "Paradis' Playmakers",
                     "F_BRANDON": "Brandon Knows Ball",
                     "F_OTHER": "Other Team"}
        reverse = _build_reverse_name_map(name_map)

        text = (
            "Paradis' Playmakers blew out Brandon Knows Ball by 106.60. "
            "Jonathan Taylor led the way with 48.10 points."
        )
        failures = verify_player_franchise(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
            week=14, reverse_name_map=reverse,
        )
        pf = [f for f in failures if f.category == "PLAYER_FRANCHISE"]
        assert pf == [], (
            f"expected no PLAYER_FRANCHISE failures for correct "
            f"attribution, got {[(f.claim, f.evidence) for f in pf]}"
        )

    def test_player_near_own_franchise_and_opponent_passes(self, tmp_path):
        """Taylor near both own franchise (Paradis') and opponent
        (Brandon). Own franchise present → pass."""
        db_path = self._build_db(tmp_path)
        name_map = {"F_STEVE": "Steve's Warmongers",
                     "F_KP": "Paradis' Playmakers",
                     "F_BRANDON": "Brandon Knows Ball",
                     "F_OTHER": "Other Team"}
        reverse = _build_reverse_name_map(name_map)

        text = (
            "Paradis' Playmakers crushed Brandon Knows Ball 150-44. "
            "Jonathan Taylor's 48.10 was the highlight of the beatdown."
        )
        failures = verify_player_franchise(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
            week=14, reverse_name_map=reverse,
        )
        pf = [f for f in failures if f.category == "PLAYER_FRANCHISE"]
        assert pf == [], (
            f"expected no failures when own franchise is in the window, "
            f"got {[(f.claim, f.evidence) for f in pf]}"
        )

    def test_no_franchise_context_silence(self, tmp_path):
        """Watson mentioned with score but no franchise names nearby.
        No opinion is safer than a false positive → silence."""
        db_path = self._build_db(tmp_path)
        # Empty reverse map: no franchise names to find
        reverse: dict[str, str] = {}

        text = "Christian Watson scored 22.90 this week."
        failures = verify_player_franchise(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
            week=14, reverse_name_map=reverse,
        )
        assert failures == [], (
            f"expected silence when no franchise context available, "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_no_score_attribution_no_check(self, tmp_path):
        """Watson mentioned near wrong franchise but WITHOUT an
        attributed score. The franchise check requires a tightly
        attributed score to trigger — casual mentions are not checked."""
        db_path = self._build_db(tmp_path)
        name_map = {"F_STEVE": "Steve's Warmongers",
                     "F_KP": "Paradis' Playmakers",
                     "F_BRANDON": "Brandon Knows Ball",
                     "F_OTHER": "Other Team"}
        reverse = _build_reverse_name_map(name_map)

        # Watson near Paradis'/Brandon but no XX.XX score within 25 chars
        text = (
            "Paradis' Playmakers crushed Brandon Knows Ball. "
            "Christian Watson was unavailable for comment."
        )
        failures = verify_player_franchise(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
            week=14, reverse_name_map=reverse,
        )
        assert failures == [], (
            f"expected no failures when player has no attributed score, "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_integration_checks_run_includes_category_7(self, tmp_path):
        """Full verify_recap_v1 includes Category 7 in checks_run count."""
        db_path = self._build_db(tmp_path)
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Paradis' Playmakers blew out Brandon Knows Ball by 106.60. "
            "Christian Watson added 22.90 in his first week.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=14,
        )
        assert result.checks_run == 8
        pf = [f for f in result.hard_failures
              if f.category == "PLAYER_FRANCHISE"]
        assert len(pf) == 1, (
            f"expected 1 PLAYER_FRANCHISE failure from full pipeline, "
            f"got {len(pf)}: {[(f.claim, f.evidence) for f in pf]}"
        )


# ── Regression: V8 FP-SUPERLATIVE-MATCHUP-LINE ─────────────────────


class TestRegressionV8SuperlativeMatchupLine:
    """Pin Finding 3 from OBSERVATIONS_2026_04_15: a team score in a
    matchup-line format (A.AA-B.BB) gets extracted by
    _extract_nearby_score and miscompared against the season
    high/low, producing a false SUPERLATIVE failure.

    Source: prompt_audit row 17 (2025 w10 a1) — prose contains
    "in their 137.50-103.10 win over Italian Cavallini" and the
    word "season" in the same paragraph. The verifier extracts
    103.10 as the nearest score to "season" and flags it against
    the actual season-high team score.
    """

    def test_v8_matchup_line_not_flagged_as_season_high(self):
        """Row 17 pattern: matchup score 103.10 from '137.50-103.10 win'
        must NOT be flagged as a season-high claim."""
        matchups = [
            _make_matchup(1, "F1", "F2", 145.30, 100.10),
            _make_matchup(10, "F3", "F4", 137.50, 103.10),
        ]
        text = (
            "F3 cruised to a 137.50-103.10 win over F4. It was the "
            "best output of the season for F3."
        )
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        sup = [f for f in failures if f.category == "SUPERLATIVE"]
        assert sup == [], (
            f"expected no SUPERLATIVE failures (103.10 and 137.50 are "
            f"matchup-line scores, not standalone claims), "
            f"got {[(f.claim, f.evidence) for f in sup]}"
        )

    def test_v8_matchup_line_not_flagged_as_season_low(self):
        """Same pattern for season low — the losing score in a matchup
        line must not be flagged."""
        matchups = [
            _make_matchup(1, "F1", "F2", 145.30, 100.10),
            _make_matchup(10, "F3", "F4", 137.50, 90.10),
        ]
        text = (
            "F4 managed just 90.10 in the 137.50-90.10 rout. It was "
            "the second-lowest output of the season."
        )
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        sup = [f for f in failures if f.category == "SUPERLATIVE"]
        assert sup == [], (
            f"expected no SUPERLATIVE failures (90.10 is in a matchup "
            f"line AND has an ordinal qualifier), "
            f"got {[(f.claim, f.evidence) for f in sup]}"
        )

    def test_v8_standalone_season_high_still_flagged(self):
        """A genuine false season-high claim (standalone score, not in
        a matchup line) must still flag. V8 only protects matchup-line
        scores — it does not defang the check for standalone claims."""
        matchups = [
            _make_matchup(1, "F1", "F2", 145.30, 100.10),
        ]
        text = (
            "F4 set a new season-high with 103.10 points."
        )
        failures = verify_superlatives(
            text, matchups, None, SEASON, None, None,
        )
        sup = [f for f in failures if f.category == "SUPERLATIVE"]
        assert len(sup) == 1, (
            f"expected 1 SUPERLATIVE failure for false standalone "
            f"season-high claim, got {len(sup)}"
        )
        assert "103.10" in sup[0].claim


# ── Category 8: FAAB Transaction Verification ───────────────────────


class TestFaabClaimVerification:
    """Pin Finding 6 from OBSERVATIONS_2026_04_15: FAAB dollar amounts
    in prose were not verified against canonical WAIVER_BID_AWARDED.

    The model writes "$20 FAAB pickup" and the verifier had no check
    to confirm the amount. A future regen could invent "$45 FAAB pickup"
    and pass verification cleanly.
    """

    def _build_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F1", name="Steve's Warmongers")
        _insert_franchise(con, league_id=LEAGUE, season=SEASON,
                          franchise_id="F2", name="Brandon Knows Ball")

        # Watson picked up for $20.45 FAAB
        _insert_faab_bid(con, league_id=LEAGUE, season=SEASON,
                         franchise_id="F1", player_id="P_WATSON",
                         bid_amount=20.45)

        # Allen picked up for $21.00 FAAB
        _insert_faab_bid(con, league_id=LEAGUE, season=SEASON,
                         franchise_id="F2", player_id="P_ALLEN",
                         bid_amount=21.00)

        con.execute(
            "INSERT OR REPLACE INTO player_directory "
            "(league_id, season, player_id, name, position) "
            "VALUES (?, ?, ?, ?, ?)",
            (LEAGUE, SEASON, "P_WATSON", "Watson, Christian", "WR"),
        )
        con.execute(
            "INSERT OR REPLACE INTO player_directory "
            "(league_id, season, player_id, name, position) "
            "VALUES (?, ?, ?, ?, ?)",
            (LEAGUE, SEASON, "P_ALLEN", "Allen, Keenan", "WR"),
        )

        con.commit()
        con.close()
        return db_path

    def test_correct_faab_amount_passes(self, tmp_path):
        """$20 FAAB for Watson matches canonical $20.45 within ±1.0."""
        db_path = self._build_db(tmp_path)
        text = "Christian Watson added 22.90 after a $20 FAAB pickup."
        failures = verify_faab_claims(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        assert failures == [], (
            f"expected no failures ($20 matches canonical $20.45), "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_exact_faab_amount_passes(self, tmp_path):
        """$21 FAAB for Allen matches canonical $21.00 exactly."""
        db_path = self._build_db(tmp_path)
        text = "Keenan Allen ($21 FAAB) scored 15.60 this week."
        failures = verify_faab_claims(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        assert failures == [], (
            f"expected no failures ($21 matches canonical $21.00), "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_fabricated_faab_amount_flags(self, tmp_path):
        """$45 FAAB for Watson is fabricated — canonical is $20.45."""
        db_path = self._build_db(tmp_path)
        text = "Christian Watson, a $45 FAAB pickup, scored big."
        failures = verify_faab_claims(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        faab = [f for f in failures if f.category == "FAAB_CLAIM"]
        assert len(faab) == 1, (
            f"expected 1 FAAB_CLAIM failure, "
            f"got {len(faab)}: {[(f.claim, f.evidence) for f in faab]}"
        )
        assert faab[0].severity == "HARD"
        assert "$45" in faab[0].claim
        assert "$20.45" in faab[0].evidence

    def test_no_faab_keyword_no_check(self, tmp_path):
        """Dollar amount without FAAB keyword is not checked (could be
        auction draft amount)."""
        db_path = self._build_db(tmp_path)
        # "$45" near player but no FAAB/waiver/pickup keyword
        text = "Christian Watson, a $45 draft investment, scored big."
        failures = verify_faab_claims(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        assert failures == [], (
            f"expected no failures (no FAAB keyword), "
            f"got {[(f.claim, f.evidence) for f in failures]}"
        )

    def test_waiver_keyword_triggers_check(self, tmp_path):
        """'waiver' keyword also triggers the FAAB check."""
        db_path = self._build_db(tmp_path)
        text = "Christian Watson, claimed off waivers for $45, scored big."
        failures = verify_faab_claims(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        # "waiver" is in context, $45 doesn't match $20.45 → flags
        faab = [f for f in failures if f.category == "FAAB_CLAIM"]
        assert len(faab) == 1

    def test_integration_checks_run_includes_category_8(self, tmp_path):
        """Full pipeline includes FAAB check in checks_run."""
        db_path = self._build_db(tmp_path)
        _insert_matchup(
            sqlite3.connect(db_path), league_id=LEAGUE, season=SEASON,
            week=14, winner_id="F1", loser_id="F2",
            winner_score=120.00, loser_score=90.00,
        )
        sqlite3.connect(db_path).commit()
        text = (
            "--- SHAREABLE RECAP ---\n"
            "Christian Watson scored after a $20 FAAB pickup.\n"
            "--- END SHAREABLE RECAP ---\n"
        )
        result = verify_recap_v1(
            text, db_path=db_path, league_id=LEAGUE, season=SEASON, week=14,
        )
        assert result.checks_run == 8
