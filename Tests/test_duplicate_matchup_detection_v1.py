"""Tests for duplicate matchup week detection in preflight."""

from __future__ import annotations

import json
import os
import sqlite3
import unittest
from pathlib import Path

from squadvault.recaps.dng_reasons import DNGReason
from squadvault.recaps.preflight import (
    PreflightVerdictType,
    check_duplicate_matchup_week,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)

LEAGUE = "TEST"


def _fresh_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_matchup(
    con: sqlite3.Connection, *, league_id: str, season: int, week: int,
    winner_id: str, loser_id: str, winner_score: float, loser_score: float,
) -> None:
    occurred_at = f"{season}-12-{week:02d}T12:00:00Z"
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


class TestDuplicateMatchupWeek(unittest.TestCase):
    """Tests for check_duplicate_matchup_week."""

    def test_detects_identical_matchups(self, tmp_path=None):
        """Weeks with identical matchups should trigger DNG."""
        import tempfile
        tmp = tempfile.mkdtemp()
        db_path = _fresh_db(Path(tmp))
        con = sqlite3.connect(db_path)

        # Week 17: championship
        _insert_matchup(con, league_id=LEAGUE, season=2025, week=17,
                        winner_id="F1", loser_id="F2",
                        winner_score=139.40, loser_score=118.65)
        # Week 18: identical duplicate
        _insert_matchup(con, league_id=LEAGUE, season=2025, week=18,
                        winner_id="F1", loser_id="F2",
                        winner_score=139.40, loser_score=118.65)
        con.commit()
        con.close()

        result = check_duplicate_matchup_week(db_path, LEAGUE, 2025, 18)
        self.assertIsNotNone(result)
        self.assertEqual(result.verdict, PreflightVerdictType.DO_NOT_GENERATE)
        self.assertEqual(result.reason_code, DNGReason.DNG_DUPLICATE_MATCHUP_WEEK)
        self.assertEqual(result.evidence["prior_week"], 17)

    def test_different_matchups_pass(self):
        """Weeks with different matchups should return None (OK)."""
        import tempfile
        tmp = tempfile.mkdtemp()
        db_path = _fresh_db(Path(tmp))
        con = sqlite3.connect(db_path)

        # Week 16: semifinal
        _insert_matchup(con, league_id=LEAGUE, season=2025, week=16,
                        winner_id="F1", loser_id="F3",
                        winner_score=162.20, loser_score=111.25)
        # Week 17: championship (different teams)
        _insert_matchup(con, league_id=LEAGUE, season=2025, week=17,
                        winner_id="F1", loser_id="F2",
                        winner_score=139.40, loser_score=118.65)
        con.commit()
        con.close()

        result = check_duplicate_matchup_week(db_path, LEAGUE, 2025, 17)
        self.assertIsNone(result)

    def test_same_teams_different_scores_pass(self):
        """Same teams but different scores = real game, not duplicate."""
        import tempfile
        tmp = tempfile.mkdtemp()
        db_path = _fresh_db(Path(tmp))
        con = sqlite3.connect(db_path)

        _insert_matchup(con, league_id=LEAGUE, season=2025, week=16,
                        winner_id="F1", loser_id="F2",
                        winner_score=130.00, loser_score=110.00)
        _insert_matchup(con, league_id=LEAGUE, season=2025, week=17,
                        winner_id="F1", loser_id="F2",
                        winner_score=139.40, loser_score=118.65)
        con.commit()
        con.close()

        result = check_duplicate_matchup_week(db_path, LEAGUE, 2025, 17)
        self.assertIsNone(result)

    def test_week_1_skipped(self):
        """Week 1 has no prior week — should always return None."""
        import tempfile
        tmp = tempfile.mkdtemp()
        db_path = _fresh_db(Path(tmp))

        result = check_duplicate_matchup_week(db_path, LEAGUE, 2025, 1)
        self.assertIsNone(result)

    def test_no_matchups_in_either_week(self):
        """Weeks with no matchup results should return None."""
        import tempfile
        tmp = tempfile.mkdtemp()
        db_path = _fresh_db(Path(tmp))

        result = check_duplicate_matchup_week(db_path, LEAGUE, 2025, 5)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
