from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from squadvault.consumers.recap_writing_room_select_v1 import main


class TestWritingRoomConsumerSelectV1(unittest.TestCase):
    def test_runs_and_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            signals_path = d / "signals.json"
            out_path = d / "selection_set_v1.json"

            signals = [
                {"signal_id": "b", "confidence": "A", "lineage_complete": True, "in_window": True},
                {"signal_id": "a", "confidence": "C", "lineage_complete": True, "in_window": True},
            ]
            signals_path.write_text(json.dumps(signals), encoding="utf-8")

            rc = main([
                "--db", str(d / "db.sqlite"),
                "--league-id", "70985",
                "--season", "2024",
                "--week-index", "6",
                "--window-id", "w1",
                "--window-start", "2024-10-13T17:00:00Z",
                "--window-end", "2024-10-20T17:00:00Z",
                "--created-at-utc", "2026-01-22T06:00:00Z",
                "--signals-json", str(signals_path),
                "--out", str(out_path),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(out_path.exists())

            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["included_signal_ids"], ["b"])  # "a" excluded low confidence
            self.assertEqual(len(payload["excluded"]), 1)


if __name__ == "__main__":
    unittest.main()
