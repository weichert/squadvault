"""Tests for Scoring Rules ingestion and Detector 54 (Dimension 11)."""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.core.recaps.context.league_rules_context_v1 import (
    detect_scoring_rules_angles_v1,
)
from squadvault.ingest.scoring_rules import (
    ingest_scoring_rules_from_mfl,
    parse_scoring_rules,
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


# MFL rules response matching PFL Buddies format
PFL_RULES_RESPONSE = {
    "rules": {
        "positionRules": [{
            "positions": "QB|RB|WR|TE|K|Def",
            "rule": [
                {"event": {"$t": "#P"}, "points": {"$t": "*6"}, "range": {"$t": "0-10"}},
                {"event": {"$t": "PY"}, "points": {"$t": "*.05"}, "range": {"$t": "-50-999"}},
                {"event": {"$t": "IN"}, "points": {"$t": "*-2"}, "range": {"$t": "0-10"}},
                {"event": {"$t": "#R"}, "points": {"$t": "*6"}, "range": {"$t": "0-10"}},
                {"event": {"$t": "RY"}, "points": {"$t": "*.1"}, "range": {"$t": "-50-999"}},
                {"event": {"$t": "#C"}, "points": {"$t": "*6"}, "range": {"$t": "0-10"}},
                {"event": {"$t": "CY"}, "points": {"$t": "*.1"}, "range": {"$t": "-50-999"}},
                {"event": {"$t": "CC"}, "points": {"$t": "*.5"}, "range": {"$t": "0-99"}},
            ],
        }],
    },
}


# ── Parser tests ─────────────────────────────────────────────────────


class TestScoringRulesParser:
    def test_parses_pfl_buddies_rules(self):
        result = parse_scoring_rules(PFL_RULES_RESPONSE)
        rules = result["key_rules"]
        assert rules["passing_td_pts"] == 6.0
        assert rules["passing_yd_pts"] == 0.05
        assert rules["rushing_td_pts"] == 6.0
        assert rules["rushing_yd_pts"] == 0.1
        assert rules["receiving_td_pts"] == 6.0
        assert rules["reception_pts"] == 0.5
        assert rules["interception_pts"] == -2.0

    def test_detects_deviations_from_standard(self):
        result = parse_scoring_rules(PFL_RULES_RESPONSE)
        deviations = result["deviations"]
        # 6pt passing TD vs standard 4
        assert "passing_td_pts" in deviations
        # 0.5 PPR vs standard 0
        assert "reception_pts" in deviations
        # 0.05/yd vs standard 0.04/yd
        assert "passing_yd_pts" in deviations

    def test_empty_response(self):
        result = parse_scoring_rules({"error": "not found"})
        assert result["key_rules"] == {}

    def test_missing_rules_key(self):
        result = parse_scoring_rules({"rules": {}})
        assert result["key_rules"] == {}


# ── Ingestion tests ──────────────────────────────────────────────────


class TestScoringRulesIngestion:
    def test_upserts_to_db(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        count = ingest_scoring_rules_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json=PFL_RULES_RESPONSE,
        )
        assert count == 1

        con = sqlite3.connect(db_path)
        row = con.execute(
            "SELECT rules_json FROM league_scoring_rules WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchone()
        con.close()
        assert row is not None
        parsed = json.loads(row[0])
        assert parsed["key_rules"]["passing_td_pts"] == 6.0

    def test_idempotent(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        ingest_scoring_rules_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json=PFL_RULES_RESPONSE)
        ingest_scoring_rules_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json=PFL_RULES_RESPONSE)
        con = sqlite3.connect(db_path)
        count = con.execute(
            "SELECT COUNT(*) FROM league_scoring_rules WHERE league_id=?", (LEAGUE,)
        ).fetchone()[0]
        con.close()
        assert count == 1


# ── Detector 54 tests ────────────────────────────────────────────────


def _insert_player_score(con, *, league_id, season, week, franchise_id,
                          player_id, score):
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = json.dumps({
        "week": week, "franchise_id": franchise_id, "player_id": player_id,
        "score": score, "is_starter": True, "should_start": True,
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


class TestScoringStructureContext:
    def test_detects_on_week_1(self, tmp_path):
        """Detector fires on week 1 with rules data."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        # Store rules
        ingest_scoring_rules_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json=PFL_RULES_RESPONSE)

        # Add player directory and scores for positional distribution
        con.execute(
            "INSERT INTO player_directory (league_id, season, player_id, name, position) VALUES (?,?,?,?,?)",
            (LEAGUE, SEASON, "P1", "QB1", "QB"))
        con.execute(
            "INSERT INTO player_directory (league_id, season, player_id, name, position) VALUES (?,?,?,?,?)",
            (LEAGUE, SEASON, "P2", "RB1", "RB"))
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P1", score=35.0)
        _insert_player_score(con, league_id=LEAGUE, season=SEASON, week=1,
                              franchise_id="F1", player_id="P2", score=15.0)
        con.commit()
        con.close()

        angles = detect_scoring_rules_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1)
        assert len(angles) >= 1
        categories = {a.category for a in angles}
        assert "SCORING_STRUCTURE_CONTEXT" in categories
        # Should mention 6pt passing TD
        assert any("6 points per passing TD" in a.headline for a in angles)

    def test_silent_on_non_week_1(self, tmp_path):
        """Detector is silent on weeks other than 1."""
        db_path = _fresh_db(tmp_path)
        ingest_scoring_rules_from_mfl(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            raw_json=PFL_RULES_RESPONSE)
        angles = detect_scoring_rules_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=5)
        assert angles == []

    def test_silent_without_rules_data(self, tmp_path):
        """No rules data = silence."""
        db_path = _fresh_db(tmp_path)
        angles = detect_scoring_rules_angles_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week=1)
        assert angles == []
