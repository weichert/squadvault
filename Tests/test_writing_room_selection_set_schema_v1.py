from __future__ import annotations

import unittest

from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    ExcludedSignal,
    ExclusionReasonCode,
    ReasonDetailKV,
    SelectionSetV1,
    WithheldReasonCode,
    sha256_of_canonical_json,
)


class TestWritingRoomSelectionSetSchemaV1(unittest.TestCase):
    def test_withheld_requires_reason(self) -> None:
        s = SelectionSetV1(
            selection_set_id="ss1",
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
            window_start="2024-10-13T17:00:00Z",
            window_end="2024-10-20T17:00:00Z",
            withheld=True,
            withheld_reason=None,
        )
        with self.assertRaises(ValueError):
            _ = s.to_canonical_dict()

    def test_canonical_sorting_included_and_excluded_details(self) -> None:
        s = SelectionSetV1(
            selection_set_id="ss1",
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
            window_start="2024-10-13T17:00:00Z",
            window_end="2024-10-20T17:00:00Z",
            included_signal_ids=["b", "a", "c"],
            excluded=[
                ExcludedSignal(
                    signal_id="z",
                    reason_code=ExclusionReasonCode.LOW_CONFIDENCE,
                    details=[
                        ReasonDetailKV(k="b", v="2"),
                        ReasonDetailKV(k="a", v="1"),
                    ],
                ),
                ExcludedSignal(
                    signal_id="a",
                    reason_code=ExclusionReasonCode.OUT_OF_WINDOW,
                    details=None,
                ),
            ],
        )

        d = s.to_canonical_dict()

        # included_signal_ids must be lexicographically sorted
        self.assertEqual(d["included_signal_ids"], ["a", "b", "c"])

        # excluded must be sorted by (signal_id, reason_code)
        self.assertEqual(d["excluded"][0]["signal_id"], "a")
        self.assertEqual(d["excluded"][0]["reason_code"], ExclusionReasonCode.OUT_OF_WINDOW.value)
        self.assertEqual(d["excluded"][1]["signal_id"], "z")

        # details must be sorted by (k, v)
        self.assertEqual(d["excluded"][1]["details"], [{"k": "a", "v": "1"}, {"k": "b", "v": "2"}])

    def test_sha256_of_canonical_json_is_stable(self) -> None:
        # Same logical content, different input ordering => same canonical hash.
        a = SelectionSetV1(
            selection_set_id="ss1",
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
            window_start="2024-10-13T17:00:00Z",
            window_end="2024-10-20T17:00:00Z",
            included_signal_ids=["b", "a"],
            excluded=[],
        ).to_canonical_dict()

        b = SelectionSetV1(
            selection_set_id="ss1",
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
            window_start="2024-10-13T17:00:00Z",
            window_end="2024-10-20T17:00:00Z",
            included_signal_ids=["a", "b"],
            excluded=[],
        ).to_canonical_dict()

        self.assertEqual(sha256_of_canonical_json(a), sha256_of_canonical_json(b))

    def test_withheld_serializes_reason(self) -> None:
        s = SelectionSetV1(
            selection_set_id="ss1",
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
            window_start="2024-10-13T17:00:00Z",
            window_end="2024-10-20T17:00:00Z",
            withheld=True,
            withheld_reason=WithheldReasonCode.NO_ELIGIBLE_SIGNALS,
        )
        d = s.to_canonical_dict()
        self.assertTrue(d["withheld"])
        self.assertEqual(d["withheld_reason"], WithheldReasonCode.NO_ELIGIBLE_SIGNALS.value)


if __name__ == "__main__":
    unittest.main()
