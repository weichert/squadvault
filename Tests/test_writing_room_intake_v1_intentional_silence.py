import unittest

from squadvault.recaps.writing_room.intake_v1 import IntakeContextV1, build_selection_set_v1
from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    ExclusionReasonCode,
    WithheldReasonCode,
)


class _AdapterStub:
    """Minimal adapter for Writing Room Intake tests."""

    def signal_id(self, sig):
        return sig["signal_id"]

    def is_in_window(self, sig, **kwargs):
        return True

    def confidence(self, sig):
        return sig.get("confidence", "A")

    def is_lineage_complete(self, sig):
        return sig.get("lineage_complete", True)

    def is_sensitive(self, sig):
        return sig.get("sensitive", False)

    def redundancy_key(self, sig):
        return sig.get("redundancy_key")


class TestWritingRoomIntakeV1_IntentionalSilence(unittest.TestCase):
    def setUp(self):
        self.ctx = IntakeContextV1(
            league_id="L1",
            season=2025,
            week_index=1,
            window_id="W1",
            window_start="2025-09-01T00:00:00Z",
            window_end="2025-09-08T00:00:00Z",
        )
        self.adapter = _AdapterStub()

    def test_excludes_intentionally_silent_event_types_when_event_type_metadata_present(self):
        signals = [
            {"signal_id": "a", "event_type": "TRANSACTION_LOCK_ALL_PLAYERS", "confidence": "A"},
            {"signal_id": "b", "event_type": "SOME_OTHER_EVENT", "confidence": "A"},
            {"signal_id": "c", "event_type": "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS", "confidence": "A"},
        ]

        ss = build_selection_set_v1(
    selection_set_id="TEST_SELECTION_SET_ID",
    created_at_utc="2025-01-01T00:00:00Z",
    selection_fingerprint="TEST_FINGERPRINT",
    signals=signals,
    adapter=self.adapter,
    ctx=self.ctx,
)

        self.assertEqual(ss.included_signal_ids, ["b"])

        excluded_by_id = {e.signal_id: e for e in ss.excluded}
        self.assertIn("a", excluded_by_id)
        self.assertIn("c", excluded_by_id)

        self.assertEqual(excluded_by_id["a"].reason_code, ExclusionReasonCode.INTENTIONAL_SILENCE)
        self.assertEqual(excluded_by_id["c"].reason_code, ExclusionReasonCode.INTENTIONAL_SILENCE)

        # sanity: not withheld
        self.assertFalse(getattr(ss, "withheld", False))

    def test_withholds_when_only_intentionally_silent_signals_exist(self):
        signals = [
            {"signal_id": "a", "event_type": "TRANSACTION_LOCK_ALL_PLAYERS", "confidence": "A"},
            {"signal_id": "b", "event_type": "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS", "confidence": "A"},
        ]

        ss = build_selection_set_v1(
    selection_set_id="TEST_SELECTION_SET_ID",
    created_at_utc="2025-01-01T00:00:00Z",
    selection_fingerprint="TEST_FINGERPRINT",
    signals=signals,
    adapter=self.adapter,
    ctx=self.ctx,
)

        self.assertEqual(ss.included_signal_ids, [])
        self.assertTrue(ss.withheld)
        self.assertEqual(ss.withheld_reason, WithheldReasonCode.NO_ELIGIBLE_SIGNALS)

        self.assertEqual(len(ss.excluded), 2)
        self.assertTrue(all(e.reason_code == ExclusionReasonCode.INTENTIONAL_SILENCE for e in ss.excluded))


if __name__ == "__main__":
    unittest.main()
