"""Tests for Season Context Derivation v1.

Uses synthetic matchup data to verify standings, streaks, scoring context,
and prompt rendering. No fixture DB dependency — these tests are self-contained.
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

from squadvault.core.recaps.context.season_context_v1 import (
    MatchupResult,
    SeasonContextV1,
    TeamRecord,
    _compute_records,
    _parse_matchup,
    _season_milestones,
    _week_scoring_highlights,
    derive_season_context_v1,
    render_season_context_for_prompt,
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


def _insert_matchup(
    con: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week: int,
    winner_id: str,
    loser_id: str,
    winner_score: float,
    loser_score: float,
    is_tie: bool = False,
    occurred_at: str = None,
):
    """Insert a WEEKLY_MATCHUP_RESULT into memory_events + canonical_events."""
    if occurred_at is None:
        occurred_at = f"2024-10-{week:02d}T12:00:00Z"

    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": is_tie,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"matchup_{league_id}_{season}_{week}_{winner_id}_{loser_id}"

    # Insert into memory_events
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_MATCHUP_RESULT",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert into canonical_events
    fingerprint = f"fp_{ext_id}"
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_MATCHUP_RESULT",
         fingerprint, me_id, 100, occurred_at, occurred_at),
    )


def _seed_three_week_season(con: sqlite3.Connection, league_id: str = LEAGUE, season: int = SEASON):
    """Seed a small league: 4 teams, 3 weeks of matchups.

    Week 1: A beats B 120-100, C beats D 95-90
    Week 2: A beats C 110-105, D beats B 88-85
    Week 3: B beats A 130-125, C beats D 100-80

    After 3 weeks:
      A: 2-1, PF: 355, PA: 305, streak: L1
      B: 1-2, PF: 315, PA: 318, streak: W1
      C: 2-1, PF: 300, PA: 280, streak: W1
      D: 1-2, PF: 258, PA: 283, streak: L1
    """
    games = [
        # week, winner, loser, w_score, l_score
        (1, "A", "B", 120.0, 100.0),
        (1, "C", "D", 95.0, 90.0),
        (2, "A", "C", 110.0, 105.0),
        (2, "D", "B", 88.0, 85.0),
        (3, "B", "A", 130.0, 125.0),
        (3, "C", "D", 100.0, 80.0),
    ]
    for w, winner, loser, ws, ls in games:
        _insert_matchup(
            con, league_id=league_id, season=season, week=w,
            winner_id=winner, loser_id=loser,
            winner_score=ws, loser_score=ls,
        )
    con.commit()


# ── Unit tests: parsing ──────────────────────────────────────────────


class TestParseMatchup:
    def test_valid_payload(self):
        p = json.dumps({
            "week": 6,
            "winner_franchise_id": "0001",
            "loser_franchise_id": "0002",
            "winner_score": "120.50",
            "loser_score": "100.30",
            "is_tie": False,
        })
        m = _parse_matchup(p, fallback_week=1)
        assert m is not None
        assert m.week == 6
        assert m.winner_id == "0001"
        assert m.loser_id == "0002"
        assert m.winner_score == 120.50
        assert m.loser_score == 100.30
        assert m.is_tie is False
        assert m.margin == 20.20

    def test_tie(self):
        p = json.dumps({
            "week": 3,
            "winner_franchise_id": "A",
            "loser_franchise_id": "B",
            "winner_score": "100.00",
            "loser_score": "100.00",
            "is_tie": True,
        })
        m = _parse_matchup(p, fallback_week=1)
        assert m.is_tie is True
        assert m.margin == 0.0

    def test_missing_winner_returns_none(self):
        p = json.dumps({"loser_franchise_id": "B", "winner_score": "100", "loser_score": "90"})
        assert _parse_matchup(p, fallback_week=1) is None

    def test_malformed_json_returns_none(self):
        assert _parse_matchup("not json", fallback_week=1) is None

    def test_empty_payload_returns_none(self):
        assert _parse_matchup("{}", fallback_week=1) is None

    def test_fallback_week_used_when_missing(self):
        p = json.dumps({
            "winner_franchise_id": "A",
            "loser_franchise_id": "B",
            "winner_score": "100",
            "loser_score": "90",
        })
        m = _parse_matchup(p, fallback_week=7)
        assert m.week == 7


# ── Unit tests: records ──────────────────────────────────────────────


class TestComputeRecords:
    def _matchups(self):
        return [
            MatchupResult(week=1, winner_id="A", loser_id="B", winner_score=120, loser_score=100, is_tie=False, margin=20),
            MatchupResult(week=1, winner_id="C", loser_id="D", winner_score=95, loser_score=90, is_tie=False, margin=5),
            MatchupResult(week=2, winner_id="A", loser_id="C", winner_score=110, loser_score=105, is_tie=False, margin=5),
            MatchupResult(week=2, winner_id="D", loser_id="B", winner_score=88, loser_score=85, is_tie=False, margin=3),
            MatchupResult(week=3, winner_id="B", loser_id="A", winner_score=130, loser_score=125, is_tie=False, margin=5),
            MatchupResult(week=3, winner_id="C", loser_id="D", winner_score=100, loser_score=80, is_tie=False, margin=20),
        ]

    def test_records_through_week_3(self):
        records = _compute_records(self._matchups(), through_week=3)
        assert records["A"].wins == 2
        assert records["A"].losses == 1
        assert records["A"].current_streak == -1  # lost last game
        assert records["B"].wins == 1
        assert records["B"].losses == 2
        assert records["B"].current_streak == 1  # won last game
        assert records["C"].wins == 2
        assert records["C"].losses == 1
        assert records["C"].current_streak == 1
        assert records["D"].wins == 1
        assert records["D"].losses == 2
        assert records["D"].current_streak == -1

    def test_records_through_week_1(self):
        records = _compute_records(self._matchups(), through_week=1)
        assert records["A"].wins == 1
        assert records["A"].losses == 0
        assert records["A"].current_streak == 1
        assert records["B"].wins == 0
        assert records["B"].losses == 1

    def test_points_for_against(self):
        records = _compute_records(self._matchups(), through_week=3)
        # A: scored 120+110+125=355, allowed 100+105+130=335
        assert records["A"].points_for == 355.0
        assert records["A"].points_against == 335.0

    def test_win_streak_accumulation(self):
        matchups = [
            MatchupResult(week=1, winner_id="A", loser_id="B", winner_score=100, loser_score=90, is_tie=False, margin=10),
            MatchupResult(week=2, winner_id="A", loser_id="C", winner_score=100, loser_score=90, is_tie=False, margin=10),
            MatchupResult(week=3, winner_id="A", loser_id="D", winner_score=100, loser_score=90, is_tie=False, margin=10),
        ]
        records = _compute_records(matchups, through_week=3)
        assert records["A"].current_streak == 3  # 3-game win streak

    def test_tie_resets_streak(self):
        matchups = [
            MatchupResult(week=1, winner_id="A", loser_id="B", winner_score=100, loser_score=90, is_tie=False, margin=10),
            MatchupResult(week=2, winner_id="A", loser_id="B", winner_score=95, loser_score=95, is_tie=True, margin=0),
        ]
        records = _compute_records(matchups, through_week=2)
        assert records["A"].current_streak == 0
        assert records["A"].ties == 1


# ── Unit tests: week highlights ──────────────────────────────────────


class TestWeekHighlights:
    def test_basic_highlights(self):
        matchups = [
            MatchupResult(week=3, winner_id="B", loser_id="A", winner_score=130, loser_score=125, is_tie=False, margin=5),
            MatchupResult(week=3, winner_id="C", loser_id="D", winner_score=100, loser_score=80, is_tie=False, margin=20),
        ]
        high, low, closest, blowout = _week_scoring_highlights(matchups)

        assert high == ("B", 130.0)  # B scored 130
        assert low == ("D", 80.0)    # D scored 80
        assert closest == ("B", "A", 5.0)
        assert blowout == ("C", "D", 20.0)

    def test_empty_week(self):
        high, low, closest, blowout = _week_scoring_highlights([])
        assert high is None
        assert low is None
        assert closest is None
        assert blowout is None


# ── Unit tests: season milestones ────────────────────────────────────


class TestSeasonMilestones:
    def test_season_high_low(self):
        matchups = [
            MatchupResult(week=1, winner_id="A", loser_id="B", winner_score=120, loser_score=100, is_tie=False, margin=20),
            MatchupResult(week=2, winner_id="A", loser_id="C", winner_score=145, loser_score=90, is_tie=False, margin=55),
        ]
        high, low, avg = _season_milestones(matchups, through_week=2)
        assert high.score == 145.0
        assert high.franchise_id == "A"
        assert high.week == 2
        assert low.score == 90.0
        assert low.franchise_id == "C"
        assert avg is not None


# ── Integration tests: full derivation ───────────────────────────────


class TestDeriveSeasonContext:
    def test_three_week_season(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_three_week_season(con)
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=3
        )

        assert ctx.has_matchup_data
        assert ctx.has_this_week_data
        assert ctx.through_week == 3
        assert ctx.matchups_this_week == 2
        assert ctx.total_matchups_through_week == 6

        # Standings: A and C both 2-1, A has higher PF
        assert len(ctx.standings) == 4
        assert ctx.standings[0].franchise_id == "A"  # 2-1, PF 355
        assert ctx.standings[1].franchise_id == "C"  # 2-1, PF 300
        assert ctx.standings[0].wins == 2
        assert ctx.standings[0].current_streak == -1

        # Season high: B scored 130 in week 3... but A scored 125 in week 3.
        # Actually let me check: A: 120(w1)+110(w2)+125(w3), B: 100+85+130
        # Season high individual score: B at 130 in week 3
        assert ctx.season_high is not None
        assert ctx.season_high.score == 130.0
        assert ctx.season_high.franchise_id == "B"

    def test_no_matchup_data(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        assert not ctx.has_matchup_data
        assert ctx.standings == ()

    def test_week_before_data(self, tmp_path):
        """Asking for week 0 when data starts at week 1."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_three_week_season(con)
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=0
        )
        assert not ctx.has_this_week_data
        assert ctx.standings == ()

    def test_partial_season(self, tmp_path):
        """Context through week 1 only."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_three_week_season(con)
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        assert ctx.through_week == 1
        assert ctx.matchups_this_week == 2
        assert ctx.total_matchups_through_week == 2
        # After week 1: A is 1-0, C is 1-0, B is 0-1, D is 0-1
        assert ctx.standings[0].wins == 1
        assert ctx.standings[0].losses == 0

    def test_deterministic(self, tmp_path):
        """Same inputs produce identical output."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_three_week_season(con)
        con.close()

        ctx1 = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=3
        )
        ctx2 = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=3
        )
        assert ctx1 == ctx2


# ── Integration tests: prompt rendering ──────────────────────────────


class TestPromptRendering:
    def test_renders_standings(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_three_week_season(con)
        con.close()

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=3
        )
        text = render_season_context_for_prompt(ctx)

        assert "Season standings through Week 3:" in text
        assert "2-1" in text
        assert "1-2" in text
        assert "Week 3 results:" in text
        assert "High scorer:" in text
        assert "Season high:" in text

    def test_renders_with_name_resolver(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_three_week_season(con)
        con.close()

        names = {"A": "Gopher Boys", "B": "Hoosier Daddy", "C": "Team Elway", "D": "Rodgers' Rascals"}

        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=3
        )
        text = render_season_context_for_prompt(ctx, team_resolver=lambda fid: names.get(fid, fid))

        assert "Gopher Boys" in text
        assert "Hoosier Daddy" in text

    def test_empty_context_renders_cleanly(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        text = render_season_context_for_prompt(ctx)
        assert "No matchup data" in text
