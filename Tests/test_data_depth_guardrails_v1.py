"""Tests for data depth guardrails — single-season overclaim suppression.

Verifies that narrative angles, league history rendering, and the creative
layer prompt correctly suppress "all-time" and "league record" claims
when only a single season of data is ingested.

Governance: Creativity must never compensate for missing context.
"""

import sqlite3
from pathlib import Path


from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
)
from squadvault.core.recaps.context.league_history_v1 import (
    derive_league_history_v1,
    load_all_matchups,
    render_league_history_for_prompt,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    _detect_streak_records,
    _detect_season_records,
    _detect_rivalry_angles,
    detect_narrative_angles_v1,
)

LEAGUE = "TEST_DEPTH"
SEASON = 2024


def _fresh_db(tmp_path):
    db_path = str(tmp_path / "depth.sqlite")
    schema = (Path(__file__).resolve().parent.parent / "src" / "squadvault"
              / "core" / "storage" / "schema.sql").read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)
    con.close()
    return db_path


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score):
    import json
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
    ext_id = f"depth_{league_id}_{season}_{week}_{winner_id}_{loser_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_MATCHUP_RESULT",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    fp = f"fp_{ext_id}"
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_MATCHUP_RESULT",
         fp, me_id, 100, occurred_at, occurred_at),
    )
    con.commit()


def _build_single_season_with_streak(tmp_path):
    """Single season, 6 weeks. Team A wins all 6 (creates a streak 'record')."""
    db_path = _fresh_db(tmp_path)
    con = sqlite3.connect(db_path)
    games = [
        (1, "A", "B", 120, 100), (2, "A", "C", 115, 95),
        (3, "A", "D", 125, 90), (4, "A", "E", 110, 105),
        (5, "A", "F", 130, 70), (6, "A", "B", 135, 110),
        (1, "C", "D", 95, 90), (2, "B", "D", 100, 85),
        (3, "B", "E", 102, 97), (4, "C", "F", 98, 72),
        (5, "B", "C", 100, 95), (6, "C", "D", 95, 88),
        (1, "E", "F", 88, 70), (2, "E", "F", 90, 65),
        (3, "C", "F", 95, 60), (4, "B", "D", 108, 88),
        (5, "D", "E", 92, 88), (6, "E", "F", 95, 70),
    ]
    for w, winner, loser, ws, ls in games:
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                        winner_id=winner, loser_id=loser,
                        winner_score=ws, loser_score=ls)
    con.close()
    return db_path


def _build_multi_season(tmp_path):
    """Two seasons of data — enough for real cross-season claims."""
    db_path = _fresh_db(tmp_path)
    con = sqlite3.connect(db_path)
    for season in (2023, 2024):
        games = [
            (1, "A", "B", 120, 100), (2, "A", "C", 115, 95),
            (3, "A", "D", 125, 90), (1, "C", "D", 95, 90),
            (2, "B", "D", 100, 85), (3, "B", "C", 102, 97),
        ]
        for w, winner, loser, ws, ls in games:
            _insert_matchup(con, league_id=LEAGUE, season=season, week=w,
                            winner_id=winner, loser_id=loser,
                            winner_score=ws, loser_score=ls)
    con.close()
    return db_path


# ── Streak record suppression ────────────────────────────────────────


class TestStreakRecordSuppression:
    """_detect_streak_records must suppress when single-season."""

    def test_single_season_suppresses_streak_records(self, tmp_path):
        """With one season, no streak 'league record' angles should appear."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        assert not history.is_multi_season
        # A has a 6-game win streak — but with single season, this is suppressed
        angles = _detect_streak_records(ctx, history)
        assert angles == [], (
            f"Single-season streak record angles should be empty, got: "
            f"{[a.headline for a in angles]}"
        )

    def test_multi_season_allows_streak_records(self, tmp_path):
        """With multiple seasons, streak records are allowed."""
        db_path = _build_multi_season(tmp_path)
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        assert history.is_multi_season


# ── Scoring record suppression ───────────────────────────────────────


class TestScoringRecordDepth:
    """_detect_season_records must not promote to ALL-TIME on single season."""

    def test_single_season_no_alltime_headline(self, tmp_path):
        """With one season, no angle headline should contain 'ALL-TIME'."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        assert not history.is_multi_season
        angles = _detect_season_records(ctx, history)
        for a in angles:
            assert "ALL-TIME" not in a.headline, (
                f"Single-season data should never produce ALL-TIME headlines: "
                f"{a.headline}"
            )


# ── Rivalry suppression ──────────────────────────────────────────────


class TestRivalrySuppression:
    """_detect_rivalry_angles must suppress on single-season data."""

    def test_single_season_no_rivalry_angles(self, tmp_path):
        """With one season, rivalry angles should be suppressed entirely."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        assert not history.is_multi_season
        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        assert angles == [], (
            f"Single-season rivalry angles should be empty, got: "
            f"{[a.headline for a in angles]}"
        )


# ── Full pipeline integration ────────────────────────────────────────


class TestFullPipelineDepthGuards:
    """End-to-end: single-season detect_narrative_angles_v1 has no overclaims."""

    def test_no_alltime_in_single_season_angles(self, tmp_path):
        """Full pipeline with single season produces no 'all-time' angles."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        result = detect_narrative_angles_v1(
            season_ctx=ctx, history_ctx=history, all_matchups=all_matchups,
        )

        for a in result.angles:
            assert "all-time" not in a.headline.lower(), (
                f"Single-season angle has 'all-time' overclaim: {a.headline}"
            )
            assert "league record" not in a.headline.lower(), (
                f"Single-season angle has 'league record' overclaim: {a.headline}"
            )


# ── Render guardrails ────────────────────────────────────────────────


class TestRenderDepthCaveat:
    """render_league_history_for_prompt must warn on single-season data."""

    def test_single_season_includes_depth_warning(self, tmp_path):
        db_path = _build_single_season_with_streak(tmp_path)
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        rendered = render_league_history_for_prompt(history)

        assert "DATA DEPTH WARNING" in rendered, (
            "Single-season render must include DATA DEPTH WARNING"
        )
        assert "All-time" not in rendered, (
            f"Single-season render should not contain 'All-time': {rendered}"
        )

    def test_multi_season_no_depth_warning(self, tmp_path):
        db_path = _build_multi_season(tmp_path)
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        rendered = render_league_history_for_prompt(history)

        assert "DATA DEPTH WARNING" not in rendered, (
            "Multi-season render should NOT include DATA DEPTH WARNING"
        )
        assert "All-time" in rendered, (
            "Multi-season render should contain 'All-time'"
        )
