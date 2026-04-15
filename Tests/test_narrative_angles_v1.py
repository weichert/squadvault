"""Tests for Narrative Angle Detection v1.

Exercises each angle detector against synthetic league data
to verify upsets, streaks, scoring anomalies, margin stories,
records, and rivalry angles are detected correctly.
"""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.core.recaps.context.league_history_v1 import (
    derive_league_history_v1,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    _detect_margin_stories,
    _detect_scoring_anomalies,
    _detect_streaks,
    _detect_upsets,
    detect_narrative_angles_v1,
)
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "test_league"
SEASON = 2024


def _fresh_db(tmp_path, name="test.sqlite"):
    """Create a fresh DB from schema.sql."""
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score, is_tie=False):
    """Insert a WEEKLY_MATCHUP_RESULT into memory + canonical events."""
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": is_tie,
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


def _build_upset_scenario(tmp_path):
    """6-team league, 6 weeks. Team F (worst) beats Team A (best) in week 6."""
    db_path = _fresh_db(tmp_path)
    con = sqlite3.connect(db_path)

    # Weeks 1-5: A dominates, F loses everything
    games = [
        # A goes 5-0
        (1, "A", "B", 120, 100), (2, "A", "C", 115, 95),
        (3, "A", "D", 125, 90), (4, "A", "E", 110, 105),
        (5, "A", "F", 130, 70),
        # F goes 0-5 (F is the loser in each)
        (1, "E", "F", 110, 60), (2, "D", "F", 100, 65),
        (3, "C", "F", 95, 70), (4, "B", "F", 108, 72),
        # Fill in other matchups
        (1, "C", "D", 95, 90), (2, "B", "E", 100, 98),
        (3, "B", "E", 102, 97), (4, "C", "D", 98, 88),
        (5, "B", "C", 100, 95), (5, "D", "E", 92, 88),
    ]
    for w, winner, loser, ws, ls in games:
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                        winner_id=winner, loser_id=loser,
                        winner_score=ws, loser_score=ls)

    # Week 6: THE UPSET — F beats A
    _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=6,
                    winner_id="F", loser_id="A", winner_score=135, loser_score=125)
    _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=6,
                    winner_id="B", loser_id="C", winner_score=100, loser_score=90)
    _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=6,
                    winner_id="D", loser_id="E", winner_score=95, loser_score=88)
    con.commit()
    con.close()
    return db_path


# ── Upset detection ──────────────────────────────────────────────────


class TestUpsetDetection:
    def test_detects_major_upset(self, tmp_path):
        """Bottom team beating #1 should be a headline upset."""
        db_path = _build_upset_scenario(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6
        )
        upsets = _detect_upsets(ctx)
        # F beating A should register as an upset
        upset_fids = [(a.franchise_ids) for a in upsets]
        assert any("F" in fids and "A" in fids for fids in upset_fids), \
            f"Expected F vs A upset, got: {upsets}"

    def test_no_upsets_when_favorites_win(self, tmp_path):
        """When higher-ranked teams win, no upsets detected."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Simple 2-week league where favorites always win
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="A", loser_id="B", winner_score=120, loser_score=100)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=2,
                        winner_id="A", loser_id="B", winner_score=115, loser_score=95)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=2
        )
        upsets = _detect_upsets(ctx)
        assert len(upsets) == 0


# ── Streak detection ─────────────────────────────────────────────────


class TestStreakDetection:
    def test_detects_win_streak(self, tmp_path):
        """A team winning 4+ straight should be flagged."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 5):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="A", loser_id="B",
                            winner_score=100 + w, loser_score=90)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )
        streaks = _detect_streaks(ctx)
        win_streaks = [a for a in streaks if a.category == "STREAK" and "win" in a.headline.lower()]
        assert len(win_streaks) >= 1
        assert any("A" in a.franchise_ids for a in win_streaks)

    def test_detects_losing_streak(self, tmp_path):
        """A team losing 4+ straight should be flagged."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 5):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="A", loser_id="B",
                            winner_score=100 + w, loser_score=90)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )
        streaks = _detect_streaks(ctx)
        loss_streaks = [a for a in streaks if "losing" in a.headline.lower() or "lost" in a.headline.lower()]
        assert len(loss_streaks) >= 1
        assert any("B" in a.franchise_ids for a in loss_streaks)

    def test_losing_streak_detail_says_extended(self, tmp_path):
        """Detail for a losing streak must say 'extended, not snapped'.

        Data-layer fix: the model receives the explicit conclusion rather
        than being asked to derive snap vs. extend from matchup results.
        """
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 5):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="A", loser_id="B",
                            winner_score=100 + w, loser_score=90)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )
        streaks = _detect_streaks(ctx)
        loss_streaks = [a for a in streaks if "B" in a.franchise_ids and "los" in a.headline.lower()]
        assert len(loss_streaks) == 1
        detail = loss_streaks[0].detail
        assert "Lost to A" in detail
        assert "extended, not snapped" in detail

    def test_win_streak_detail_says_continues(self, tmp_path):
        """Detail for a win streak must say 'continues'."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 5):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="A", loser_id="B",
                            winner_score=100 + w, loser_score=90)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )
        streaks = _detect_streaks(ctx)
        win_streaks = [a for a in streaks if "A" in a.franchise_ids and "win" in a.headline.lower()]
        assert len(win_streaks) == 1
        detail = win_streaks[0].detail
        assert "Beat B" in detail
        assert "continues" in detail


# ── Scoring anomaly detection ────────────────────────────────────────


class TestScoringAnomalies:
    def test_detects_high_score(self, tmp_path):
        """A score 50%+ above average should be a headline anomaly."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Weeks 1-3: average around 100
        for w in range(1, 4):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="A", loser_id="B",
                            winner_score=105, loser_score=95)
        # Week 4: A explodes for 160 (60% above 100 avg)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=4,
                        winner_id="A", loser_id="B",
                        winner_score=160, loser_score=90)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )
        anomalies = _detect_scoring_anomalies(ctx)
        high_anomalies = [a for a in anomalies if "160" in a.headline]
        assert len(high_anomalies) >= 1

    def test_no_anomalies_normal_week(self, tmp_path):
        """Scores within normal range should produce no anomalies."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        for w in range(1, 5):
            _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                            winner_id="A", loser_id="B",
                            winner_score=102, loser_score=98)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )
        anomalies = _detect_scoring_anomalies(ctx)
        assert len(anomalies) == 0


# ── Margin stories ───────────────────────────────────────────────────


class TestMarginStories:
    def test_detects_blowout(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="A", loser_id="B",
                        winner_score=150, loser_score=80)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        margins = _detect_margin_stories(ctx)
        blowouts = [a for a in margins if a.category == "BLOWOUT"]
        assert len(blowouts) >= 1
        assert blowouts[0].strength >= 3

    def test_detects_nail_biter(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="A", loser_id="B",
                        winner_score=100.5, loser_score=99.3)
        con.commit()
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        margins = _detect_margin_stories(ctx)
        nail_biters = [a for a in margins if a.category == "NAIL_BITER"]
        assert len(nail_biters) >= 1


# ── Full detection pipeline ──────────────────────────────────────────


class TestFullDetection:
    def test_integrates_all_detectors(self, tmp_path):
        """Full pipeline produces angles from a rich scenario."""
        db_path = _build_upset_scenario(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        from squadvault.core.recaps.context.league_history_v1 import load_all_matchups
        all_matchups = load_all_matchups(db_path, LEAGUE)

        result = detect_narrative_angles_v1(
            season_ctx=ctx,
            history_ctx=history,
            all_matchups=all_matchups,
        )

        assert result.has_angles
        assert len(result.angles) >= 1
        # Should be sorted by strength desc
        strengths = [a.strength for a in result.angles]
        assert strengths == sorted(strengths, reverse=True)

    def test_deterministic(self, tmp_path):
        """Same inputs produce same angles."""
        db_path = _build_upset_scenario(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6
        )

        r1 = detect_narrative_angles_v1(season_ctx=ctx)
        r2 = detect_narrative_angles_v1(season_ctx=ctx)
        assert r1 == r2

    def test_empty_week(self, tmp_path):
        """No matchup data produces no angles."""
        db_path = _fresh_db(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        result = detect_narrative_angles_v1(season_ctx=ctx)
        assert not result.has_angles

    def test_without_history(self, tmp_path):
        """Works fine without history context (single season)."""
        db_path = _build_upset_scenario(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6
        )
        result = detect_narrative_angles_v1(season_ctx=ctx, history_ctx=None)
        assert result.has_angles
