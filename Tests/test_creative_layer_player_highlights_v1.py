"""Tests for Phase C — player highlights integration in Creative Layer v1.

Verifies:
1. _build_user_prompt() includes PLAYER HIGHLIGHTS block when provided
2. _build_user_prompt() omits the block when empty string or whitespace
3. System prompt contains the player-level voice rule
4. System prompt contains the player score fabrication hard rule
5. draft_narrative_v1() accepts the player_highlights parameter
6. PLAYER HIGHLIGHTS block is positioned between WRITER ROOM and VERIFIED FACTS
"""

from __future__ import annotations

import os
import unittest
import warnings
from unittest.mock import MagicMock, patch

from squadvault.ai.creative_layer_v1 import (
    _SYSTEM_PROMPT,
    _build_user_prompt,
    draft_narrative_v1,
)


_SAMPLE_BULLETS = [
    "Tanner Stark beat Kyle Holloway 142.6-98.3.",
    "Deadpool's Army added Justin Jefferson (free agent).",
]
_PERMITTED_DIRECTIVE = "MODERATE_CONFIDENCE_ONLY"

_SAMPLE_PLAYER_HIGHLIGHTS = (
    "Week 6 top scorer: Jahmyr Gibbs (Paradis' Playmakers) — 40.20 pts\n"
    "Week 6 lowest starter: CeeDee Lamb (Purple Haze) — 3.10 pts\n"
    "\n"
    "Paradis' Playmakers (starters: 192.15, bench: 42.30):\n"
    "  Top: Jahmyr Gibbs — 40.20 pts\n"
    "  Bust: Garrett Wilson — 5.10 pts\n"
)


class TestSystemPromptPlayerRules(unittest.TestCase):
    """System prompt must contain both the voice rule and the hard rule."""

    def test_voice_rule_present(self) -> None:
        self.assertIn(
            "When player-level data is available in the PLAYER HIGHLIGHTS section",
            _SYSTEM_PROMPT,
        )

    def test_voice_rule_mentions_naming_players(self) -> None:
        self.assertIn(
            "Name the players who carried",
            _SYSTEM_PROMPT,
        )

    def test_hard_rule_no_fabrication(self) -> None:
        self.assertIn(
            "NEVER invent player scores or individual performances not present in the",
            _SYSTEM_PROMPT,
        )

    def test_hard_rule_silence_on_missing(self) -> None:
        self.assertIn(
            "If player data is not available for a week, do not",
            _SYSTEM_PROMPT,
        )

    def test_voice_rule_in_voice_section(self) -> None:
        """Voice rule appears before hard rules (voice section, not hard rules section)."""
        voice_idx = _SYSTEM_PROMPT.index("When player-level data is available")
        hard_rules_idx = _SYSTEM_PROMPT.index("Hard rules (non-negotiable):")
        self.assertLess(voice_idx, hard_rules_idx)

    def test_hard_rule_in_hard_rules_section(self) -> None:
        """Fabrication hard rule appears after the 'Hard rules' marker."""
        hard_rules_idx = _SYSTEM_PROMPT.index("Hard rules (non-negotiable):")
        fabrication_idx = _SYSTEM_PROMPT.index(
            "NEVER invent player scores or individual performances"
        )
        self.assertGreater(fabrication_idx, hard_rules_idx)


class TestBuildUserPromptPlayerHighlights(unittest.TestCase):
    """_build_user_prompt includes/omits PLAYER HIGHLIGHTS correctly."""

    def test_includes_block_when_provided(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive=_PERMITTED_DIRECTIVE,
            league_id="L1", season=2024, week_index=6,
            player_highlights=_SAMPLE_PLAYER_HIGHLIGHTS,
        )
        self.assertIn("=== PLAYER HIGHLIGHTS", prompt)
        self.assertIn("Jahmyr Gibbs", prompt)
        self.assertIn("40.20 pts", prompt)

    def test_omits_block_when_empty_string(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive=_PERMITTED_DIRECTIVE,
            league_id="L1", season=2024, week_index=6,
            player_highlights="",
        )
        self.assertNotIn("PLAYER HIGHLIGHTS", prompt)

    def test_omits_block_when_whitespace_only(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive=_PERMITTED_DIRECTIVE,
            league_id="L1", season=2024, week_index=6,
            player_highlights="   \n  \n  ",
        )
        self.assertNotIn("PLAYER HIGHLIGHTS", prompt)

    def test_omits_block_when_not_provided(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive=_PERMITTED_DIRECTIVE,
            league_id="L1", season=2024, week_index=6,
        )
        self.assertNotIn("PLAYER HIGHLIGHTS", prompt)

    def test_block_positioned_before_verified_facts(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive=_PERMITTED_DIRECTIVE,
            league_id="L1", season=2024, week_index=6,
            player_highlights=_SAMPLE_PLAYER_HIGHLIGHTS,
        )
        ph_idx = prompt.index("PLAYER HIGHLIGHTS")
        vf_idx = prompt.index("VERIFIED FACTS")
        self.assertLess(ph_idx, vf_idx)

    def test_block_positioned_after_writer_room_when_both_present(self) -> None:
        prompt = _build_user_prompt(
            facts_bullets=_SAMPLE_BULLETS,
            eal_directive=_PERMITTED_DIRECTIVE,
            league_id="L1", season=2024, week_index=6,
            writer_room_context="Some writer room data",
            player_highlights=_SAMPLE_PLAYER_HIGHLIGHTS,
        )
        wr_idx = prompt.index("WRITER ROOM")
        ph_idx = prompt.index("PLAYER HIGHLIGHTS")
        vf_idx = prompt.index("VERIFIED FACTS")
        self.assertLess(wr_idx, ph_idx)
        self.assertLess(ph_idx, vf_idx)


class TestDraftNarrativeV1AcceptsPlayerHighlights(unittest.TestCase):
    """draft_narrative_v1() accepts and passes through player_highlights."""

    def _mock(self, text: str) -> MagicMock:
        mc = MagicMock(); mc.text = text
        mr = MagicMock(); mr.content = [mc]
        ma = MagicMock(); ma.Anthropic.return_value.messages.create.return_value = mr
        return ma

    def test_accepts_player_highlights_kwarg(self) -> None:
        """draft_narrative_v1 accepts player_highlights without error."""
        ma = self._mock("Great week with player detail.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS,
                    eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                    player_highlights=_SAMPLE_PLAYER_HIGHLIGHTS,
                )
        self.assertEqual(result, "Great week with player detail.")

    def test_player_highlights_in_api_prompt(self) -> None:
        """Player highlights text appears in the prompt sent to the API."""
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS,
                    eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                    player_highlights=_SAMPLE_PLAYER_HIGHLIGHTS,
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        user_content = next(
            (m["content"] for m in kwargs.get("messages", []) if m.get("role") == "user"), ""
        )
        self.assertIn("PLAYER HIGHLIGHTS", user_content)
        self.assertIn("Jahmyr Gibbs", user_content)

    def test_empty_player_highlights_not_in_prompt(self) -> None:
        """Empty player highlights should not inject PLAYER HIGHLIGHTS block."""
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS,
                    eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                    player_highlights="",
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        user_content = next(
            (m["content"] for m in kwargs.get("messages", []) if m.get("role") == "user"), ""
        )
        self.assertNotIn("PLAYER HIGHLIGHTS", user_content)

    def test_defaults_to_empty_when_not_provided(self) -> None:
        """Omitting player_highlights entirely still works (backward compat)."""
        ma = self._mock("Narrative without players.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                result = draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS,
                    eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        self.assertEqual(result, "Narrative without players.")


if __name__ == "__main__":
    unittest.main()
