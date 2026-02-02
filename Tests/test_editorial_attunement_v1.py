from __future__ import annotations

import unittest

from squadvault.core_engine.editorial_attunement_v1 import (
    EALMeta,
    evaluate_editorial_attunement_v1,
    EAL_AMBIGUITY_PREFER_SILENCE,
    EAL_LOW_CONFIDENCE_RESTRAINT,
    EAL_MODERATE_CONFIDENCE_ONLY,
)


class TestEditorialAttunementV1(unittest.TestCase):
    def test_missing_selection_set_prefers_silence(self) -> None:
        meta = EALMeta(has_selection_set=False, has_window=True, included_count=None)
        self.assertEqual(evaluate_editorial_attunement_v1(meta), EAL_AMBIGUITY_PREFER_SILENCE)

    def test_missing_window_prefers_silence(self) -> None:
        meta = EALMeta(has_selection_set=True, has_window=False, included_count=10)
        self.assertEqual(evaluate_editorial_attunement_v1(meta), EAL_AMBIGUITY_PREFER_SILENCE)

    def test_zero_included_prefers_silence(self) -> None:
        meta = EALMeta(has_selection_set=True, has_window=True, included_count=0)
        self.assertEqual(evaluate_editorial_attunement_v1(meta), EAL_AMBIGUITY_PREFER_SILENCE)

    def test_low_included_is_restrained(self) -> None:
        meta = EALMeta(has_selection_set=True, has_window=True, included_count=2)
        self.assertEqual(evaluate_editorial_attunement_v1(meta), EAL_LOW_CONFIDENCE_RESTRAINT)

    def test_normal_included_is_moderate(self) -> None:
        meta = EALMeta(has_selection_set=True, has_window=True, included_count=5)
        self.assertEqual(evaluate_editorial_attunement_v1(meta), EAL_MODERATE_CONFIDENCE_ONLY)

    def test_determinism(self) -> None:
        meta = EALMeta(has_selection_set=True, has_window=True, included_count=5)
        a = evaluate_editorial_attunement_v1(meta)
        b = evaluate_editorial_attunement_v1(meta)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
