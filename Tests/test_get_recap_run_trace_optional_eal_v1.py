from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from squadvault.recaps.weekly_recap_lifecycle import _get_recap_run_trace


class TestGetRecapRunTraceOptionalEALV1(unittest.TestCase):
    def _mk_db(self, with_eal: bool) -> str:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        db = Path(td.name) / "t.sqlite"
        con = sqlite3.connect(str(db))
        try:
            cols = [
                "league_id TEXT",
                "season INTEGER",
                "week_index INTEGER",
                "selection_fingerprint TEXT",
                "window_start TEXT",
                "window_end TEXT",
            ]
            if with_eal:
                cols.append("editorial_attunement_v1 TEXT")
            con.execute(f"CREATE TABLE recap_runs ({', '.join(cols)})")
            if with_eal:
                con.execute(
                    "INSERT INTO recap_runs VALUES (?,?,?,?,?,?,?)",
                    ("L1", 2024, 6, "fp", "ws", "we", "MODERATE_CONFIDENCE_ONLY"),
                )
            else:
                con.execute(
                    "INSERT INTO recap_runs VALUES (?,?,?,?,?,?)",
                    ("L1", 2024, 6, "fp", "ws", "we"),
                )
            con.commit()
        finally:
            con.close()
        return str(db)

    def test_default(self):
        db = self._mk_db(True)
        fp, ws, we = _get_recap_run_trace(db, "L1", 2024, 6)
        self.assertEqual(fp, "fp")

    def test_optional_eal(self):
        db = self._mk_db(True)
        fp, ws, we, eal = _get_recap_run_trace(db, "L1", 2024, 6, include_editorial=True)
        self.assertEqual(eal, "MODERATE_CONFIDENCE_ONLY")

    def test_missing_column(self):
        db = self._mk_db(False)
        fp, ws, we, eal = _get_recap_run_trace(db, "L1", 2024, 6, include_editorial=True)
        self.assertIsNone(eal)


if __name__ == "__main__":
    unittest.main()
