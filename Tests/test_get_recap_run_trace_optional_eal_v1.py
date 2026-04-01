from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from squadvault.recaps.weekly_recap_lifecycle import _get_recap_run_trace


class TestGetRecapRunTraceOptionalEALV1(unittest.TestCase):
    def _mk_db(self) -> str:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        db = Path(td.name) / "t.sqlite"
        con = sqlite3.connect(str(db))
        try:
            con.execute(
                """CREATE TABLE recap_runs (
                    league_id TEXT,
                    season INTEGER,
                    week_index INTEGER,
                    selection_fingerprint TEXT,
                    window_start TEXT,
                    window_end TEXT
                )"""
            )
            con.execute(
                "INSERT INTO recap_runs VALUES (?,?,?,?,?,?)",
                ("L1", 2024, 6, "fp", "ws", "we"),
            )
            con.commit()
        finally:
            con.close()
        return str(db)

    def test_default(self):
        db = self._mk_db()
        fp, ws, we = _get_recap_run_trace(db, "L1", 2024, 6)
        self.assertEqual(fp, "fp")
        self.assertEqual(ws, "ws")
        self.assertEqual(we, "we")


if __name__ == "__main__":
    unittest.main()
