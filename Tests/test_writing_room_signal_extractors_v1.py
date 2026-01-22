from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from squadvault.recaps.writing_room.signal_extractors_v1 import (
    CanonicalEventsSignalExtractorV1,
)


class TestWritingRoomSignalExtractorsV1(unittest.TestCase):
    def test_extracts_minimal_dict_signals_and_redundancy_keys(self) -> None:
        """
        Verifies extractor behavior (not intake behavior):

        - Emits minimal dict signals required downstream
        - Uses half-open window semantics correctly (>= start, < end)
        - Produces identical redundancy_key for rows that share action_fingerprint
        """
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
                        event_type TEXT NOT NULL,
                        action_fingerprint TEXT
                    )
                    """
                )

                league_id = "70985"
                season = 2024
                ts = "2024-10-27T17:00:00Z"
                window_end = "2024-10-27T17:00:01Z"  # half-open window end must be > start
                event_type = "TRANSACTION_LOCK_ALL_PLAYERS"
                afp = "afp_same"

                # Two rows in-window with the same action_fingerprint.
                con.execute(
                    """
                    INSERT INTO canonical_events (league_id, season, occurred_at, event_type, action_fingerprint)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (league_id, season, ts, event_type, afp),
                )
                con.execute(
                    """
                    INSERT INTO canonical_events (league_id, season, occurred_at, event_type, action_fingerprint)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (league_id, season, ts, event_type, afp),
                )
                con.commit()

                extractor = CanonicalEventsSignalExtractorV1()
                signals = extractor.extract_signals(
                    db_path=str(db),
                    league_id=league_id,
                    season=season,
                    window_start=ts,
                    window_end=window_end,
                )

                self.assertIsInstance(signals, list)
                self.assertEqual(len(signals), 2, "Extractor emits one signal per canonical_event row")

                # Minimal required keys for downstream adapters / intake gating.
                for sig in signals:
                    self.assertIsInstance(sig, dict)
                    for k in ("signal_id", "confidence", "lineage_complete", "in_window", "sensitive", "ambiguous"):
                        self.assertIn(k, sig)
                    self.assertEqual(sig["confidence"], "A")
                    self.assertTrue(sig["lineage_complete"])
                    self.assertTrue(sig["in_window"])
                    self.assertFalse(sig["sensitive"])
                    self.assertFalse(sig["ambiguous"])

                # Redundancy key should exist and be identical given same action_fingerprint.
                self.assertIn("redundancy_key", signals[0])
                self.assertIn("redundancy_key", signals[1])
                self.assertEqual(signals[0]["redundancy_key"], signals[1]["redundancy_key"])
                self.assertTrue(signals[0]["redundancy_key"])


            finally:
                con.close()
if __name__ == "__main__":
    unittest.main()
