from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from squadvault.recaps.writing_room.signal_extractors_v1 import CanonicalEventsSignalExtractorV1


class TestWritingRoomSignalExtractorsV1(unittest.TestCase):
    def test_extracts_minimal_dict_signals(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.sqlite"
            con = sqlite3.connect(str(db))
            try:
                con.execute(
                    """
                    CREATE TABLE canonical_events (
                        id INTEGER PRIMARY KEY,
                        league_id TEXT NOT NULL,
                        season INTEGER NOT NULL,
                        occurred_at TEXT NOT NULL,
                        event_type TEXT NOT NULL
                    )
                    """
                )
                con.execute(
                    "INSERT INTO canonical_events (id, league_id, season, occurred_at, event_type) VALUES (?,?,?,?,?)",
                    (1, "70985", 2024, "2024-10-13T17:00:00Z", "TRANSACTION_FREE_AGENT"),
                )
                con.execute(
                    "INSERT INTO canonical_events (id, league_id, season, occurred_at, event_type) VALUES (?,?,?,?,?)",
                    (2, "70985", 2024, "2024-10-13T17:05:00Z", "TRANSACTION_TRADE"),
                )
                con.commit()
            finally:
                con.close()

            ex = CanonicalEventsSignalExtractorV1()
            signals = ex.extract_signals(
                db_path=str(db),
                league_id="70985",
                season=2024,
                window_start="2024-10-13T17:00:00Z",
                window_end="2024-10-20T17:00:00Z",
            )

            self.assertEqual(len(signals), 2)
            for s in signals:
                # Required adapter keys
                self.assertIn("signal_id", s)
                self.assertIn("confidence", s)
                self.assertIn("lineage_complete", s)
                self.assertIn("in_window", s)

            self.assertEqual(signals[0]["signal_id"], "ce:1")
            self.assertEqual(signals[1]["signal_id"], "ce:2")


if __name__ == "__main__":
    unittest.main()
