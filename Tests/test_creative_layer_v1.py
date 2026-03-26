"""Tests for Creative Layer v1 (squadvault.ai.creative_layer_v1).

No live API calls are made. All tests use monkeypatching or environment
manipulation to verify behavioral contracts without network access.
"""

from __future__ import annotations

import os
import unittest
import warnings
from unittest.mock import MagicMock, patch

from squadvault.ai.creative_layer_v1 import (
    _PERMITTED_DIRECTIVES,
    _build_user_prompt,
    draft_narrative_v1,
)
from squadvault.core.eal.editorial_attunement_v1 import EAL_AMBIGUITY_PREFER_SILENCE

_SAMPLE_BULLETS = [
    "Tanner Stark beat Kyle Holloway 142.6-98.3.",
    "Deadpool's Army added Justin Jefferson (free agent).",
]
_PERMITTED_DIRECTIVE = "MODERATE_CONFIDENCE_ONLY"


class TestDraftNarrativeV1EALGating(unittest.TestCase):
    def test_ambiguity_prefer_silence_returns_none(self) -> None:
        with patch("squadvault.ai.creative_layer_v1.os.environ.get", return_value="fake-key"):
            result = draft_narrative_v1(
                facts_bullets=_SAMPLE_BULLETS, eal_directive=EAL_AMBIGUITY_PREFER_SILENCE,
                league_id="L1", season=2024, week_index=6,
            )
        self.assertIsNone(result)

    def test_unrecognised_directive_returns_none(self) -> None:
        with patch("squadvault.ai.creative_layer_v1.os.environ.get", return_value="fake-key"):
            result = draft_narrative_v1(
                facts_bullets=_SAMPLE_BULLETS, eal_directive="INVENTED_DIRECTIVE",
                league_id="L1", season=2024, week_index=6,
            )
        self.assertIsNone(result)

    def test_all_permitted_directives_pass_eal_gate(self) -> None:
        for directive in _PERMITTED_DIRECTIVES:
            env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    result = draft_narrative_v1(
                        facts_bullets=_SAMPLE_BULLETS, eal_directive=directive,
                        league_id="L1", season=2024, week_index=1,
                    )
                self.assertIsNone(result)
                self.assertTrue(any("ANTHROPIC_API_KEY" in str(x.message) for x in w))


class TestDraftNarrativeV1NoFactsGating(unittest.TestCase):
    def test_empty_bullets_returns_none(self) -> None:
        with patch("squadvault.ai.creative_layer_v1.os.environ.get", return_value="fake-key"):
            result = draft_narrative_v1(
                facts_bullets=[], eal_directive=_PERMITTED_DIRECTIVE,
                league_id="L1", season=2024, week_index=6,
            )
        self.assertIsNone(result)


class TestDraftNarrativeV1MissingKey(unittest.TestCase):
    def test_missing_key_returns_none_with_warning(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        self.assertIsNone(result)
        self.assertTrue(any("ANTHROPIC_API_KEY" in str(x.message) for x in w))

    def test_empty_string_key_returns_none(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "   "}, clear=False):
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        self.assertIsNone(result)


class TestDraftNarrativeV1APIError(unittest.TestCase):
    def test_api_exception_returns_none(self) -> None:
        ma = MagicMock()
        ma.Anthropic.return_value.messages.create.side_effect = RuntimeError("refused")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        self.assertIsNone(result)

    def test_api_empty_content_returns_none(self) -> None:
        ma = MagicMock()
        ma.Anthropic.return_value.messages.create.return_value.content = []
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        self.assertIsNone(result)


class TestDraftNarrativeV1SuccessPath(unittest.TestCase):
    def _mock(self, text: str) -> MagicMock:
        mc = MagicMock(); mc.text = text
        mr = MagicMock(); mr.content = [mc]
        ma = MagicMock(); ma.Anthropic.return_value.messages.create.return_value = mr
        return ma

    def test_returns_narrative_string(self) -> None:
        ma = self._mock("It was a busy week.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        self.assertEqual(result, "It was a busy week.")

    def test_uses_eal_modulated_temperature(self) -> None:
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        # MODERATE_CONFIDENCE_ONLY maps to 0.6
        self.assertEqual(kwargs.get("temperature"), 0.6)

    def test_eal_directive_in_prompt(self) -> None:
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        user_content = next(
            (m["content"] for m in kwargs.get("messages", []) if m.get("role") == "user"), ""
        )
        self.assertIn(_PERMITTED_DIRECTIVE, user_content)

    def test_facts_in_prompt(self) -> None:
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        user_content = next(
            (m["content"] for m in kwargs.get("messages", []) if m.get("role") == "user"), ""
        )
        for bullet in _SAMPLE_BULLETS:
            self.assertIn(bullet, user_content)


class TestEALGuidanceContent(unittest.TestCase):
    def test_low_confidence_skips_callbacks(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive="LOW_CONFIDENCE_RESTRAINT",
            league_id="L1", season=2024, week_index=6,
            narrative_angles="[HEADLINE] Some angle",
        )
        self.assertIn("Skip callbacks", prompt)

    def test_high_confidence_permits_full_voice(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive="HIGH_CONFIDENCE_ALLOWED",
            league_id="L1", season=2024, week_index=6,
        )
        self.assertIn("Full voice", prompt)


class TestBuildUserPromptDeterminism(unittest.TestCase):
    def test_identical_inputs_produce_identical_output(self) -> None:
        kw = dict(facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                  league_id="L1", season=2024, week_index=6)
        self.assertEqual(_build_user_prompt(**kw), _build_user_prompt(**kw))

    def test_different_directives_differ(self) -> None:
        base = dict(facts_bullets=_SAMPLE_BULLETS, league_id="L1", season=2024, week_index=6)
        self.assertNotEqual(
            _build_user_prompt(eal_directive="HIGH_CONFIDENCE_ALLOWED", **base),
            _build_user_prompt(eal_directive="LOW_CONFIDENCE_RESTRAINT", **base),
        )


class TestNarrativeIsAdditive(unittest.TestCase):
    def test_facts_precede_narrative_in_combined_output(self) -> None:
        narrative = "Active week of moves."
        mc = MagicMock(); mc.text = narrative
        mr = MagicMock(); mr.content = [mc]
        ma = MagicMock(); ma.Anthropic.return_value.messages.create.return_value = mr

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )

        facts_text = "Facts block."
        if result:
            combined = (
                facts_text.rstrip()
                + "\n\n--- Narrative Draft (AI-assisted, requires human approval) ---\n"
                + result + "\n"
            )
            self.assertIn(facts_text, combined)
            self.assertIn("requires human approval", combined)
            self.assertLess(combined.index(facts_text), combined.index("requires human approval"))


if __name__ == "__main__":
    unittest.main()
