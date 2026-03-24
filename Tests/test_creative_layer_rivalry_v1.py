"""Creative Layer Rivalry v1 — Tests.

Unit tests verify safety invariants (silent fallback, EAL veto, etc.).
Integration test calls the real Anthropic API to verify governed prose.
"""
from __future__ import annotations

import os
import pytest

from squadvault.ai.creative_layer_rivalry_v1 import (
    draft_rivalry_narrative_v1,
    _eal_directive_for_rivalry,
    _build_user_prompt,
)
from squadvault.chronicle.matchup_facts_v1 import MatchupFactV1


def _sample_facts() -> list[MatchupFactV1]:
    return [
        MatchupFactV1(
            season=2024, week=1,
            winner_franchise_id="0001", loser_franchise_id="0005",
            winner_name="Alpha Dogs", loser_name="Echo Force",
            winner_score="142.30", loser_score="121.50",
            is_tie=False,
            canonical_event_fingerprint="WEEKLY_MATCHUP_RESULT:70985:2024:W1:0001_0005",
        ),
        MatchupFactV1(
            season=2024, week=3,
            winner_franchise_id="0005", loser_franchise_id="0001",
            winner_name="Echo Force", loser_name="Alpha Dogs",
            winner_score="155.20", loser_score="148.70",
            is_tie=False,
            canonical_event_fingerprint="WEEKLY_MATCHUP_RESULT:70985:2024:W3:0001_0005",
        ),
    ]


class TestEALDirectiveComputation:
    """EAL directive for rivalry chronicles is computed from matchup count."""

    def test_zero_matchups_prefer_silence(self):
        assert _eal_directive_for_rivalry(0) == "AMBIGUITY_PREFER_SILENCE"

    def test_one_matchup_low_restraint(self):
        assert _eal_directive_for_rivalry(1) == "LOW_CONFIDENCE_RESTRAINT"

    def test_moderate_for_small_sample(self):
        assert _eal_directive_for_rivalry(2) == "MODERATE_CONFIDENCE_ONLY"
        assert _eal_directive_for_rivalry(3) == "MODERATE_CONFIDENCE_ONLY"

    def test_moderate_for_larger_sample(self):
        assert _eal_directive_for_rivalry(10) == "MODERATE_CONFIDENCE_ONLY"


class TestSilentFallback:
    """Creative layer must silently return None on all failure modes."""

    def test_no_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = draft_rivalry_narrative_v1(
            matchup_facts=_sample_facts(),
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert result is None

    def test_empty_api_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        result = draft_rivalry_narrative_v1(
            matchup_facts=_sample_facts(),
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert result is None

    def test_ambiguity_prefer_silence_veto(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
        result = draft_rivalry_narrative_v1(
            matchup_facts=_sample_facts(),
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
            eal_directive="AMBIGUITY_PREFER_SILENCE",
        )
        assert result is None

    def test_no_facts_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
        result = draft_rivalry_narrative_v1(
            matchup_facts=[],
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert result is None

    def test_unrecognised_directive_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
        result = draft_rivalry_narrative_v1(
            matchup_facts=_sample_facts(),
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
            eal_directive="UNKNOWN_DIRECTIVE",
        )
        assert result is None

    def test_zero_matchups_auto_silence(self, monkeypatch):
        """Zero matchups auto-computes AMBIGUITY_PREFER_SILENCE."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
        result = draft_rivalry_narrative_v1(
            matchup_facts=[],
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert result is None


class TestPromptConstruction:
    """User prompt is deterministic and includes required facts."""

    def test_prompt_contains_team_names(self):
        prompt = _build_user_prompt(
            facts=_sample_facts(),
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert "Alpha Dogs" in prompt
        assert "Echo Force" in prompt

    def test_prompt_contains_scores(self):
        prompt = _build_user_prompt(
            facts=_sample_facts(),
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert "142.30" in prompt
        assert "155.20" in prompt

    def test_prompt_contains_record(self):
        prompt = _build_user_prompt(
            facts=_sample_facts(),
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert "1-1" in prompt  # 1 win each

    def test_prompt_deterministic(self):
        kwargs = dict(
            facts=_sample_facts(),
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
        )
        assert _build_user_prompt(**kwargs) == _build_user_prompt(**kwargs)


class TestLiveAPI:
    """Integration test: call the real Anthropic API.

    Skipped automatically if ANTHROPIC_API_KEY is not set.
    """

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        reason="ANTHROPIC_API_KEY not set — skipping live API test",
    )
    def test_live_narrative_draft(self):
        """Call the real API and verify the response is reasonable prose."""
        result = draft_rivalry_narrative_v1(
            matchup_facts=_sample_facts(),
            team_a_name="Alpha Dogs",
            team_b_name="Echo Force",
            league_id=70985,
            season=2024,
            eal_directive="MODERATE_CONFIDENCE_ONLY",
        )
        assert result is not None, "Expected narrative prose from live API"
        assert len(result) > 20, f"Narrative too short: {result!r}"
        # Should mention at least one team name
        assert ("Alpha Dogs" in result or "Echo Force" in result), (
            f"Narrative should reference team names: {result!r}"
        )
        # Should not contain headers or meta-commentary
        assert not result.startswith("#"), "Narrative should not start with markdown header"
        assert "here is" not in result.lower(), "Narrative should not contain meta-commentary"
