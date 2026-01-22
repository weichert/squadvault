from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import scripts.recap as recap


class TestRecapCliWritingRoomFlag(unittest.TestCase):
    def test_maybe_build_writing_room_noop_when_flag_missing(self) -> None:
        # Should not raise, even though created_at_utc is absent.
        args = SimpleNamespace(
            enable_writing_room=False,
            league_id="70985",
            season=2024,
            week_index=1,
            db=":memory:",
        )
        recap._maybe_build_writing_room_selection_set_v1(args)

    def test_maybe_build_writing_room_requires_created_at(self) -> None:
        # When enabled, created-at must exist.
        args = SimpleNamespace(
            enable_writing_room=True,
            league_id="70985",
            season=2024,
            week_index=1,
            db=":memory:",
            writing_room_out=None,
            created_at_utc=None,
            writing_room_created_at_utc=None,
        )
        with self.assertRaises(SystemExit) as cm:
            recap._maybe_build_writing_room_selection_set_v1(args)
        self.assertEqual(cm.exception.code, 2)

    def test_maybe_build_writing_room_invokes_consumer_when_enabled(self) -> None:
        # Verify it calls the consumer with deterministic args.
        args = SimpleNamespace(
            enable_writing_room=True,
            league_id="70985",
            season=2024,
            week_index=6,
            db=".local_squadvault.sqlite",
            writing_room_out=None,  # triggers deterministic default
            created_at_utc="2026-01-22T00:00:00Z",
            writing_room_created_at_utc=None,
        )

        # Patch in-module reference so we don't actually execute the consumer.
        with patch.object(recap, "writing_room_select_main", autospec=True, return_value=0) as m:
            recap._maybe_build_writing_room_selection_set_v1(args)

        self.assertEqual(m.call_count, 1)
        argv = m.call_args.args[0]  # argv list passed to writing_room_select_main

        self.assertIn("--signals-source", argv)
        self.assertIn("db", argv)

        # Deterministic default output path
        self.assertIn("--out", argv)
        out_idx = argv.index("--out") + 1
        self.assertEqual(
            argv[out_idx],
            "artifacts/writing_room/70985/2024/week_06/selection_set_v1.json",
        )


if __name__ == "__main__":
    unittest.main()
