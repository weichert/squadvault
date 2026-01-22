from __future__ import annotations

import sys
import types
import unittest

from squadvault.recaps.writing_room.window_resolver_v1 import resolve_weekly_window_v1


class FakeWindow:
    def __init__(self) -> None:
        self.mode = "LOCK_TO_LOCK"
        self.window_start = "2024-10-13T17:00:00Z"
        self.window_end = "2024-10-20T17:00:00Z"


class TestWritingRoomWindowResolverV1(unittest.TestCase):
    def test_resolves_and_hashes_window_id(self) -> None:
        # Monkeypatch module path used by resolver import
        fake_selector_mod = types.SimpleNamespace(window_for_week_index=lambda *a, **k: FakeWindow())
        sys.modules["squadvault.core.recaps.selection.weekly_windows_v1"] = fake_selector_mod  # type: ignore[assignment]

        w = resolve_weekly_window_v1(
            db_path=":memory:",
            league_id="70985",
            season=2024,
            week_index=6,
        )

        self.assertEqual(w.mode, "LOCK_TO_LOCK")
        self.assertEqual(w.window_start, "2024-10-13T17:00:00Z")
        self.assertEqual(w.window_end, "2024-10-20T17:00:00Z")
        self.assertEqual(len(w.window_id), 64)


if __name__ == "__main__":
    unittest.main()
