from __future__ import annotations

import sqlite3
import tempfile
import types
import sys
import unittest
from pathlib import Path

from squadvault.consumers.recap_writing_room_select_v1 import main


class TestWritingRoomConsumerSelectV1DbAutowindow(unittest.TestCase):
    def test_dbmode_autowindow_resolves_window_before_extracting(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            db_path = d / "t.sqlite"
            out_path = d / "selection_set_v1.json"

            con = sqlite3.connect(str(db_path))
            try:
                con.execute(
                    """
                    CREATE TABLE canonical_events (
                        id INTEGER PRIMARY KEY,
                        league_id TEXT NOT NULL,
                        season INTEGER NOT NULL,
                        event_type TEXT NOT NULL,
                        action_fingerprint TEXT NOT NULL DEFAULT '',
                        best_memory_event_id INTEGER NOT NULL DEFAULT 0,
                        best_score INTEGER NOT NULL DEFAULT 0,
                        selection_version INTEGER NOT NULL DEFAULT 1,
                        updated_at TEXT NOT NULL DEFAULT '',
                        occurred_at TEXT
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

            # Monkeypatch the resolver import path used by the consumer.
            fake_resolver_mod = types.SimpleNamespace(
                resolve_weekly_window_v1=lambda **kwargs: types.SimpleNamespace(
                    window_id="w_fake",
                    window_start="2024-10-13T17:00:00Z",
                    window_end="2024-10-20T17:00:00Z",
                    mode="LOCK_TO_LOCK",
                )
            )
            sys.modules["squadvault.recaps.writing_room.window_resolver_v1"] = fake_resolver_mod  # type: ignore[assignment]

            rc = main([
                "--db", str(db_path),
                "--league-id", "70985",
                "--season", "2024",
                "--week-index", "6",
                "--created-at-utc", "2026-01-22T06:00:00Z",
                "--signals-source", "db",
                "--out", str(out_path),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(out_path.exists())

            payload = out_path.read_text(encoding="utf-8")
            self.assertIn('"ce:1"', payload)
            self.assertIn('"ce:2"', payload)


if __name__ == "__main__":
    unittest.main()
