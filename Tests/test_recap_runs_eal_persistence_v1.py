from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from squadvault.recaps.weekly_recap_lifecycle import _persist_editorial_attunement_v1_to_recap_runs


class TestRecapRunsEALPersistenceV1(unittest.TestCase):
    def test_adds_column_and_persists_value(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.sqlite"
            con = sqlite3.connect(str(db))
            try:
                con.execute(
                    """
                    CREATE TABLE recap_runs (
                      league_id TEXT NOT NULL,
                      season INTEGER NOT NULL,
                      week_index INTEGER NOT NULL,
                      selection_fingerprint TEXT NOT NULL,
                      window_start TEXT,
                      window_end TEXT
                    );
                    """
                )
                con.execute(
                    "INSERT INTO recap_runs (league_id, season, week_index, selection_fingerprint, window_start, window_end) VALUES (?,?,?,?,?,?)",
                    ("L1", 2024, 6, "fp", "ws", "we"),
                )
                con.commit()
            finally:
                con.close()

            _persist_editorial_attunement_v1_to_recap_runs(
                db_path=str(db),
                league_id="L1",
                season=2024,
                week_index=6,
                directive="MODERATE_CONFIDENCE_ONLY",
            )

            con = sqlite3.connect(str(db))
            try:
                cols = {r[1] for r in con.execute("PRAGMA table_info(recap_runs)").fetchall()}
                assert "editorial_attunement_v1" in cols

                row = con.execute(
                    "SELECT editorial_attunement_v1 FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
                    ("L1", 2024, 6),
                ).fetchone()
                assert row and row[0] == "MODERATE_CONFIDENCE_ONLY"
            finally:
                con.close()


if __name__ == "__main__":
    unittest.main()
