import unittest

from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    ExclusionReasonCode,
    ExcludedSignal,
    build_selection_fingerprint,
    deterministic_sort_str,
    deterministic_sort_excluded,
)


class TestSelectionSetDeterminism(unittest.TestCase):

    def test_deterministic_sort_str(self):
        values = ["b", "a", "c"]
        self.assertEqual(
            deterministic_sort_str(values),
            ["a", "b", "c"],
        )

    def test_deterministic_sort_excluded(self):
        a = ExcludedSignal("sig_b", ExclusionReasonCode.REDUNDANT)
        b = ExcludedSignal("sig_a", ExclusionReasonCode.OUT_OF_WINDOW)
        c = ExcludedSignal("sig_a", ExclusionReasonCode.LOW_CONFIDENCE)

        sorted_vals = deterministic_sort_excluded([a, b, c])

        self.assertEqual(
            [(e.signal_id, e.reason_code.value) for e in sorted_vals],
            [
                ("sig_a", "LOW_CONFIDENCE"),
                ("sig_a", "OUT_OF_WINDOW"),
                ("sig_b", "REDUNDANT"),
            ],
        )

    def test_selection_fingerprint_stable_across_input_order(self):
        included_1 = ["sig_c", "sig_a", "sig_b"]
        included_2 = ["sig_b", "sig_c", "sig_a"]

        excluded_1 = [
            ExcludedSignal("sig_x", ExclusionReasonCode.REDUNDANT),
            ExcludedSignal("sig_y", ExclusionReasonCode.OUT_OF_WINDOW),
        ]
        excluded_2 = [
            ExcludedSignal("sig_y", ExclusionReasonCode.OUT_OF_WINDOW),
            ExcludedSignal("sig_x", ExclusionReasonCode.REDUNDANT),
        ]

        fp1 = build_selection_fingerprint(
            league_id="L1",
            season=2024,
            week_index=3,
            window_id="W1",
            included_signal_ids=included_1,
            excluded=excluded_1,
        )

        fp2 = build_selection_fingerprint(
            league_id="L1",
            season=2024,
            week_index=3,
            window_id="W1",
            included_signal_ids=included_2,
            excluded=excluded_2,
        )

        self.assertEqual(fp1, fp2)

    def test_selection_fingerprint_changes_on_content_change(self):
        fp1 = build_selection_fingerprint(
            league_id="L1",
            season=2024,
            week_index=3,
            window_id="W1",
            included_signal_ids=["sig_a"],
            excluded=[],
        )

        fp2 = build_selection_fingerprint(
            league_id="L1",
            season=2024,
            week_index=3,
            window_id="W1",
            included_signal_ids=["sig_b"],
            excluded=[],
        )

        self.assertNotEqual(fp1, fp2)


if __name__ == "__main__":
    unittest.main()
