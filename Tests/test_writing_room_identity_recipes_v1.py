from __future__ import annotations

import unittest

from squadvault.recaps.writing_room.identity_recipes_v1 import (
    compute_sha256_hex_from_payload_v1,
    selection_fingerprint_payload_v1,
    selection_set_id_payload_v1,
)


class TestWritingRoomIdentityRecipesV1(unittest.TestCase):
    def test_selection_set_id_payload_hash_stable(self) -> None:
        p1 = selection_set_id_payload_v1(
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
        )
        p2 = selection_set_id_payload_v1(
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
        )
        self.assertEqual(compute_sha256_hex_from_payload_v1(p1), compute_sha256_hex_from_payload_v1(p2))

    def test_fingerprint_payload_sorts_arrays(self) -> None:
        p = selection_fingerprint_payload_v1(
            included_signal_ids=["b", "a"],
            excluded_signal_ids=["z", "y"],
            excluded_reason_codes=["LOW_CONFIDENCE", "OUT_OF_WINDOW"],
        )
        self.assertEqual(p["included_signal_ids"], ["a", "b"])
        self.assertEqual(p["excluded_signal_ids"], ["y", "z"])
        self.assertEqual(p["excluded_reason_codes"], ["LOW_CONFIDENCE", "OUT_OF_WINDOW"])

    def test_fingerprint_hash_ignores_input_order(self) -> None:
        p1 = selection_fingerprint_payload_v1(
            included_signal_ids=["b", "a"],
            excluded_signal_ids=["z", "y"],
        )
        p2 = selection_fingerprint_payload_v1(
            included_signal_ids=["a", "b"],
            excluded_signal_ids=["y", "z"],
        )
        self.assertEqual(compute_sha256_hex_from_payload_v1(p1), compute_sha256_hex_from_payload_v1(p2))


if __name__ == "__main__":
    unittest.main()
