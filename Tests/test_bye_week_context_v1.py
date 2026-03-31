"""Tests for Bye Week Context v1 (Dimension 10).

Exercises the 3 bye week detectors (51-53) against synthetic data.
"""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.core.recaps.context.bye_week_context_v1 import (
    _count_starters_on_bye,
    detect_bye_week_impact,
    detect_bye_week_conflict,
    detect_bye_week_angles_v1,
)
from squadvault.ingest.nfl_bye_weeks import (
    parse_nfl_bye_weeks,
    ingest_nfl_bye_weeks_from_mfl,
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


def _insert_bye_week(con, *, league_id, season, nfl_team, bye_week):
    con.execute(
        """INSERT OR REPLACE INTO nfl_bye_weeks
           (league_id, season, nfl_team, bye_week)
           VALUES (?, ?, ?, ?)""",
        (league_id, season, nfl_team, bye_week))


def _insert_player_directory(con, *, league_id, season, player_id, name, position, team):
    con.execute(
        """INSERT OR REPLACE INTO player_directory
           (league_id, season, player_id, name, position, team)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (league_id, season, player_id, name, position, team))


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


# ── Unit tests: count helper ─────────────────────────────────────────


class TestCountStartersOnBye:
    def test_counts_correctly(self):
        starters = {"F1": ["P1", "P2", "P3"]}
        player_teams = {"P1": "KC", "P2": "BUF", "P3": "SF"}
        bye_map = {"KC": 6, "BUF": 6, "SF": 9}
        counts = _count_starters_on_bye(starters, player_teams, bye_map, week=6)
        assert counts["F1"] == 2  # KC and BUF on bye week 6

    def test_no_byes_this_week(self):
        starters = {"F1": ["P1", "P2"]}
        player_teams = {"P1": "KC", "P2": "BUF"}
        bye_map = {"KC": 6, "BUF": 7}
        counts = _count_starters_on_bye(starters, player_teams, bye_map, week=3)
        assert counts == {}

    def test_unknown_player_ignored(self):
        starters = {"F1": ["P1", "P_UNKNOWN"]}
        player_teams = {"P1": "KC"}
        bye_map = {"KC": 6}
        counts = _count_starters_on_bye(starters, player_teams, bye_map, week=6)
        assert counts["F1"] == 1  # only P1 counted


# ── Unit tests: Detector 51 ──────────────────────────────────────────


class TestByeWeekImpact:
    def test_detects_multiple_on_bye(self):
        bye_counts = {"F1": 3, "F2": 1}
        angles = detect_bye_week_impact(bye_counts)
        assert len(angles) == 1
        assert "F1" in angles[0].headline
        assert "3 starters" in angles[0].headline

    def test_single_bye_not_flagged(self):
        bye_counts = {"F1": 1}
        angles = detect_bye_week_impact(bye_counts)
        assert len(angles) == 0

    def test_empty_counts(self):
        angles = detect_bye_week_impact({})
        assert len(angles) == 0


# ── Unit tests: Detector 52 ──────────────────────────────────────────


class TestByeWeekConflict:
    def test_detects_leader(self):
        bye_counts = {"F1": 3, "F2": 2, "F3": 1}
        angles = detect_bye_week_conflict(bye_counts)
        assert len(angles) == 1
        assert "F1" in angles[0].headline
        assert "most in the league" in angles[0].headline

    def test_no_significant_conflicts(self):
        bye_counts = {"F1": 1, "F2": 1}
        angles = detect_bye_week_conflict(bye_counts)
        assert len(angles) == 0


# ── DB integration: full pipeline ────────────────────────────────────


class TestByeWeekPipeline:
    def _build_bye_week_scenario(self, tmp_path):
        """Week 6: KC and BUF on bye. F1 has starters from both teams."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        # Bye weeks
        _insert_bye_week(con, league_id=LEAGUE, season=SEASON, nfl_team="KC", bye_week=6)
        _insert_bye_week(con, league_id=LEAGUE, season=SEASON, nfl_team="BUF", bye_week=6)
        _insert_bye_week(con, league_id=LEAGUE, season=SEASON, nfl_team="SF", bye_week=9)

        # Player directory
        _insert_player_directory(con, league_id=LEAGUE, season=SEASON,
                                  player_id="P1", name="Mahomes", position="QB", team="KC")
        _insert_player_directory(con, league_id=LEAGUE, season=SEASON,
                                  player_id="P2", name="Allen", position="QB", team="BUF")
        _insert_player_directory(con, league_id=LEAGUE, season=SEASON,
                                  player_id="P3", name="Purdy", position="QB", team="SF")
        _insert_player_directory(con, league_id=LEAGUE, season=SEASON,
                                  player_id="P4", name="Hurts", position="QB", team="PHI")

        # Week 6: F1 has KC + BUF starters (both on bye), F2 has SF + PHI (neither on bye)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=6,
                              franchise_id="F1", player_id="P1", score=0.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=6,
                              franchise_id="F1", player_id="P2", score=0.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=6,
                              franchise_id="F2", player_id="P3", score=25.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=6,
                              franchise_id="F2", player_id="P4", score=22.0)

        con.commit()
        con.close()
        return db_path

    def test_pipeline_detects_bye_impact(self, tmp_path):
        """Full pipeline detects bye week impact from DB data."""
        db_path = self._build_bye_week_scenario(tmp_path)
        angles = detect_bye_week_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        impact_angles = [a for a in angles if a.category == "BYE_WEEK_IMPACT"]
        assert len(impact_angles) == 1
        assert "F1" in impact_angles[0].headline
        assert "2" in impact_angles[0].headline

    def test_pipeline_detects_bye_conflict(self, tmp_path):
        """Full pipeline detects bye week conflict leader."""
        db_path = self._build_bye_week_scenario(tmp_path)
        angles = detect_bye_week_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        conflict_angles = [a for a in angles if a.category == "BYE_WEEK_CONFLICT"]
        assert len(conflict_angles) == 1
        assert "F1" in conflict_angles[0].headline

    def test_pipeline_no_bye_data_silence(self, tmp_path):
        """No bye week data = empty result."""
        db_path = _fresh_db(tmp_path)
        angles = detect_bye_week_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6,
        )
        assert angles == []

    def test_pipeline_deterministic(self, tmp_path):
        db_path = self._build_bye_week_scenario(tmp_path)
        a1 = detect_bye_week_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6)
        a2 = detect_bye_week_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=6)
        assert a1 == a2


# ── Ingestion parser tests ───────────────────────────────────────────


# ── Ingestion parser tests ───────────────────────────────────────────


class TestByeWeekIngestionParser:
    def test_parses_mfl_response(self):
        """Parse the exact MFL nflByeWeeks response shape."""
        raw = {"nflByeWeeks": {"year": "2024", "team": [
            {"id": "KCC", "bye_week": "6"},
            {"id": "PHI", "bye_week": "5"},
            {"id": "BUF", "bye_week": "12"},
        ]}}
        entries = parse_nfl_bye_weeks(raw)
        assert len(entries) == 3
        assert ("BUF", 12) in entries
        assert ("KCC", 6) in entries
        assert ("PHI", 5) in entries

    def test_parses_single_team_dict(self):
        """MFL may return a single dict instead of a list for one team."""
        raw = {"nflByeWeeks": {"year": "2024", "team": {"id": "KCC", "bye_week": "6"}}}
        entries = parse_nfl_bye_weeks(raw)
        assert len(entries) == 1
        assert entries[0] == ("KCC", 6)

    def test_skips_malformed_entries(self):
        """Malformed entries are silently skipped."""
        raw = {"nflByeWeeks": {"year": "2024", "team": [
            {"id": "KCC", "bye_week": "6"},
            {"id": "", "bye_week": "7"},       # empty team
            {"id": "BUF", "bye_week": "bad"},  # non-numeric week
            {"id": "PHI"},                      # missing bye_week
        ]}}
        entries = parse_nfl_bye_weeks(raw)
        assert len(entries) == 1
        assert entries[0] == ("KCC", 6)

    def test_empty_response(self):
        raw = {"nflByeWeeks": {"year": "2024", "team": []}}
        assert parse_nfl_bye_weeks(raw) == []

    def test_missing_root(self):
        raw = {"error": "something"}
        assert parse_nfl_bye_weeks(raw) == []


class TestByeWeekIngestionUpsert:
    def test_upserts_to_db(self, tmp_path):
        """Full ingestion pipeline: parse + upsert."""
        db_path = _fresh_db(tmp_path)
        count = ingest_nfl_bye_weeks_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json={"nflByeWeeks": {"year": "2024", "team": [
                {"id": "KCC", "bye_week": "6"},
                {"id": "PHI", "bye_week": "5"},
            ]}},
        )
        assert count == 2

        # Verify data in DB
        con = sqlite3.connect(db_path)
        rows = con.execute(
            "SELECT nfl_team, bye_week FROM nfl_bye_weeks WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchall()
        con.close()
        assert len(rows) == 2
        teams = {r[0]: r[1] for r in rows}
        assert teams["KCC"] == 6
        assert teams["PHI"] == 5

    def test_idempotent_upsert(self, tmp_path):
        """Re-ingesting the same season produces no duplicates."""
        db_path = _fresh_db(tmp_path)
        raw = {"nflByeWeeks": {"year": "2024", "team": [
            {"id": "KCC", "bye_week": "6"},
        ]}}
        ingest_nfl_bye_weeks_from_mfl(db_path=db_path, league_id=LEAGUE,
                                       season=SEASON, raw_json=raw)
        ingest_nfl_bye_weeks_from_mfl(db_path=db_path, league_id=LEAGUE,
                                       season=SEASON, raw_json=raw)
        con = sqlite3.connect(db_path)
        count = con.execute(
            "SELECT COUNT(*) FROM nfl_bye_weeks WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchone()[0]
        con.close()
        assert count == 1

    def test_empty_data_returns_zero(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        count = ingest_nfl_bye_weeks_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json={"nflByeWeeks": {"year": "2024", "team": []}},
        )
        assert count == 0
