from __future__ import annotations

import unittest

from squadvault.recaps.writing_room.intake_v1 import IntakeContextV1, build_selection_set_v1
from squadvault.recaps.writing_room.selection_set_schema_v1 import ExclusionReasonCode, WithheldReasonCode
from squadvault.recaps.writing_room.signal_adapter_v1 import DictSignalAdapter


class TestWritingRoomIntakeV1(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = DictSignalAdapter()
        self.ctx = IntakeContextV1(
            league_id="70985",
            season=2024,
            week_index=6,
            window_id="w1",
            window_start="2024-10-13T17:00:00Z",
            window_end="2024-10-20T17:00:00Z",
        )

    def test_includes_sorted_by_signal_id(self) -> None:
        signals = [
            {"signal_id": "b", "confidence": "A", "lineage_complete": True, "in_window": True},
            {"signal_id": "a", "confidence": "A", "lineage_complete": True, "in_window": True},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        self.assertEqual(d["included_signal_ids"], ["a", "b"])

    def test_excludes_out_of_window(self) -> None:
        signals = [
            {"signal_id": "a", "confidence": "A", "lineage_complete": True, "in_window": False},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        self.assertEqual(d["included_signal_ids"], [])
        self.assertEqual(d["excluded"][0]["reason_code"], ExclusionReasonCode.OUT_OF_WINDOW.value)

    def test_excludes_low_confidence(self) -> None:
        signals = [
            {"signal_id": "a", "confidence": "C", "lineage_complete": True, "in_window": True},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        self.assertEqual(d["excluded"][0]["reason_code"], ExclusionReasonCode.LOW_CONFIDENCE.value)

    def test_excludes_insufficient_context(self) -> None:
        signals = [
            {"signal_id": "a", "confidence": "A", "lineage_complete": False, "in_window": True},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        self.assertEqual(d["excluded"][0]["reason_code"], ExclusionReasonCode.INSUFFICIENT_CONTEXT.value)

    def test_excludes_sensitive(self) -> None:
        signals = [
            {"signal_id": "a", "confidence": "A", "lineage_complete": True, "in_window": True, "sensitive": True},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        self.assertEqual(d["excluded"][0]["reason_code"], ExclusionReasonCode.SENSITIVITY_GUARDRAIL.value)

    def test_redundancy_keeps_first_by_sorted_signal_id(self) -> None:
        signals = [
            {"signal_id": "b", "confidence": "A", "lineage_complete": True, "in_window": True, "redundancy_key": "rk1"},
            {"signal_id": "a", "confidence": "A", "lineage_complete": True, "in_window": True, "redundancy_key": "rk1"},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        # deterministic winner = "a"
        self.assertEqual(d["included_signal_ids"], ["a"])
        self.assertEqual(d["excluded"][0]["signal_id"], "b")
        self.assertEqual(d["excluded"][0]["reason_code"], ExclusionReasonCode.REDUNDANT.value)

    def test_withheld_when_no_eligible(self) -> None:
        signals = [
            {"signal_id": "a", "confidence": "C", "lineage_complete": True, "in_window": True},
        ]
        ss = build_selection_set_v1(
            signals,
            adapter=self.adapter,
            ctx=self.ctx,
            selection_set_id="ss1",
            created_at_utc="2026-01-22T06:00:00Z",
            selection_fingerprint="fp1",
        )
        d = ss.to_canonical_dict()
        self.assertTrue(d["withheld"])
        self.assertEqual(d["withheld_reason"], WithheldReasonCode.NO_ELIGIBLE_SIGNALS.value)


if __name__ == "__main__":
    unittest.main()
