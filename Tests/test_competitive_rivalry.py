"""Tests for the competitive-rivalry tier in _detect_rivalry_angles.

Covers the new fourth tier: long series (>=15 meetings) where neither
franchise is dominant (>=70%) and the gap is >1 (so it's not "even").
This fills a fabrication vacuum — the model sees 30+ meetings with no
verified H2H record in the prompt and invents one.

Governance: give the model verified data and it cites verified data.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from squadvault.core.recaps.context.league_history_v1 import (
    derive_league_history_v1,
    load_all_matchups,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    _detect_rivalry_angles,
)
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
)

LEAGUE = "TEST_COMP"


def _fresh_db(tmp_path):
    db_path = str(tmp_path / "comp_rivalry.sqlite")
    schema = (
        Path(__file__).resolve().parent.parent
        / "src" / "squadvault" / "core" / "storage" / "schema.sql"
    ).read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)
    con.close()
    return db_path


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score):
    """Insert a matchup as both memory + canonical event."""
    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": False,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"comp_{league_id}_{season}_{week}_{winner_id}_{loser_id}"
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
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


def _build_long_series(tmp_path, *, a_wins: int, b_wins: int,
                        seasons: int = 3):
    """Build a multi-season DB where A and B meet repeatedly.

    Distributes meetings roughly evenly across seasons.
    Also includes filler matchups so season_context sees week_matchups.
    """
    db_path = _fresh_db(tmp_path)
    con = sqlite3.connect(db_path)

    total = a_wins + b_wins
    meetings_placed = 0
    per_season = max(1, total // seasons)

    for s_idx in range(seasons):
        season = 2020 + s_idx
        week = 1

        start = meetings_placed
        end = min(total, start + per_season) if s_idx < seasons - 1 else total
        for m_idx in range(start, end):
            if m_idx < a_wins:
                _insert_matchup(con, league_id=LEAGUE, season=season,
                                week=week, winner_id="A", loser_id="B",
                                winner_score=120, loser_score=100)
            else:
                _insert_matchup(con, league_id=LEAGUE, season=season,
                                week=week, winner_id="B", loser_id="A",
                                winner_score=115, loser_score=105)
            week += 1
            meetings_placed += 1

        # Filler matchup in every season so context can derive
        _insert_matchup(con, league_id=LEAGUE, season=season, week=week,
                        winner_id="C", loser_id="D",
                        winner_score=100, loser_score=80)

    con.close()
    return db_path


class TestCompetitiveRivalryFires:
    """Competitive rivalry tier fires for long non-dominant series."""

    def test_31_meetings_17_14_produces_rivalry_angle(self, tmp_path):
        """The Brandon-vs-Purple-Haze case: 17-14 over 31 meetings."""
        db_path = _build_long_series(tmp_path, a_wins=17, b_wins=14,
                                      seasons=6)
        last_season = 2025
        # A won the last meeting — it's in the final season
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE,
            season=last_season, week_index=1,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        assert history.is_multi_season
        angles = _detect_rivalry_angles(ctx, history, all_matchups)

        rivalry_angles = [a for a in angles if "Long series" in a.headline]
        assert len(rivalry_angles) == 1, (
            f"Expected 1 competitive rivalry, got {len(rivalry_angles)}: "
            f"{[a.headline for a in angles]}"
        )
        angle = rivalry_angles[0]
        assert "14-17" in angle.headline
        assert "31 meetings" in angle.headline
        assert angle.category == "RIVALRY"
        # 31 meetings >= 25 → NOTABLE (strength 2)
        assert angle.strength == 2

    def test_16_meetings_minor_strength(self, tmp_path):
        """15-24 meetings → strength 1 (MINOR)."""
        db_path = _build_long_series(tmp_path, a_wins=10, b_wins=6,
                                      seasons=3)
        last_season = 2022
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE,
            season=last_season, week_index=1,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        rivalry_angles = [a for a in angles if "Long series" in a.headline]
        assert len(rivalry_angles) == 1
        assert rivalry_angles[0].strength == 1  # < 25 meetings → MINOR

    def test_record_string_includes_correct_counts(self, tmp_path):
        """The headline contains the verified W-L record."""
        db_path = _build_long_series(tmp_path, a_wins=10, b_wins=7,
                                      seasons=3)
        last_season = 2022
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE,
            season=last_season, week_index=1,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        rivalry_angles = [a for a in angles if "Long series" in a.headline]
        assert len(rivalry_angles) == 1
        # B won last game; h2h from B's perspective
        assert "7-10" in rivalry_angles[0].headline


class TestCompetitiveRivalryDoesNotFire:
    """Competitive rivalry tier respects existing tier priority."""

    def test_14_meetings_no_angle(self, tmp_path):
        """Below 15 meetings — no competitive angle."""
        db_path = _build_long_series(tmp_path, a_wins=9, b_wins=5,
                                      seasons=3)
        last_season = 2022
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE,
            season=last_season, week_index=1,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        long_angles = [a for a in angles if "Long series" in a.headline]
        assert long_angles == [], (
            f"14 meetings should not produce competitive rivalry: "
            f"{[a.headline for a in angles]}"
        )

    def test_dominance_takes_priority_over_competitive(self, tmp_path):
        """If one side has 70%+, dominance tier fires — not competitive."""
        # 15 wins vs 5 = 75% dominance → dominance tier
        db_path = _build_long_series(tmp_path, a_wins=15, b_wins=5,
                                      seasons=3)
        last_season = 2022
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE,
            season=last_season, week_index=1,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        long_angles = [a for a in angles if "Long series" in a.headline]
        dominance_angles = [a for a in angles if "leads the series" in a.headline]
        assert long_angles == [], "Dominance should take priority"
        assert len(dominance_angles) == 1

    def test_even_takes_priority_over_competitive(self, tmp_path):
        """If gap <= 1 with 15+ meetings, even tier fires — not competitive."""
        # 8-7 over 15 meetings: gap 1 → even rivalry
        db_path = _build_long_series(tmp_path, a_wins=8, b_wins=7,
                                      seasons=3)
        last_season = 2022
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE,
            season=last_season, week_index=1,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        long_angles = [a for a in angles if "Long series" in a.headline]
        even_angles = [a for a in angles if "Even rivalry" in a.headline]
        assert long_angles == [], "Even rivalry should take priority"
        assert len(even_angles) == 1
