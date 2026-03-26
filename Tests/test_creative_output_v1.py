"""Tests for creative layer output improvements.

Fix 1: SHAREABLE RECAP delimiter is present and parseable
Fix 2: Narrative angles instruction is in the prompt
Fix 3: Web search tool is NOT in the API call
"""
from __future__ import annotations

import inspect
import os

import pytest


class TestShareableDelimiter:
    """The rendered_text should use parseable SHAREABLE RECAP delimiters."""

    def test_delimiter_constant_in_lifecycle(self):
        """The lifecycle must use the --- SHAREABLE RECAP --- delimiter."""
        import squadvault.recaps.weekly_recap_lifecycle as lc
        source = inspect.getsource(lc)
        assert "--- SHAREABLE RECAP ---" in source
        assert "--- END SHAREABLE RECAP ---" in source

    def test_old_delimiter_not_used(self):
        """The old narrative draft delimiter should not be used for new artifacts."""
        import squadvault.recaps.weekly_recap_lifecycle as lc
        source = inspect.getsource(lc)
        assert "Narrative Draft (AI-assisted" not in source


class TestHistoricalCallbacks:
    """The system prompt should demand historical callbacks."""

    def test_callbacks_required_in_prompt(self):
        """System prompt must instruct callbacks as REQUIRED."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "Callbacks are REQUIRED" in _SYSTEM_PROMPT

    def test_angles_instruction_in_user_prompt(self):
        """User prompt builder must instruct the model to USE narrative angles."""
        from squadvault.ai.creative_layer_v1 import _build_user_prompt
        prompt = _build_user_prompt(
            facts_bullets=["test"],
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            league_id="70985",
            season=2024,
            week_index=1,
            narrative_angles="[HEADLINE] Test angle",
            seasons_count=16,
        )
        assert "USE THESE" in prompt
        assert "16 seasons" in prompt

    def test_single_season_angles_instruction(self):
        """Single-season data should not claim multi-season depth."""
        from squadvault.ai.creative_layer_v1 import _build_user_prompt
        prompt = _build_user_prompt(
            facts_bullets=["test"],
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            league_id="70985",
            season=2024,
            week_index=1,
            narrative_angles="[HEADLINE] Test angle",
            seasons_count=1,
        )
        assert "this season" in prompt.lower()
        assert "16 seasons" not in prompt

    def test_zero_seasons_angles_instruction(self):
        """Unknown seasons count should not claim specific depth."""
        from squadvault.ai.creative_layer_v1 import _build_user_prompt
        prompt = _build_user_prompt(
            facts_bullets=["test"],
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            league_id="70985",
            season=2024,
            week_index=1,
            narrative_angles="[HEADLINE] Test angle",
            seasons_count=0,
        )
        assert "available league data" in prompt
        assert "16 seasons" not in prompt


class TestNoWebSearch:
    """The creative layer must NOT use web search tools."""

    def test_no_web_search_in_api_call(self):
        """The API call source must not contain web_search tool config."""
        from squadvault.ai import creative_layer_v1 as cl
        source = inspect.getsource(cl.draft_narrative_v1)
        assert "web_search" not in source

    def test_no_nfl_web_search_in_system_prompt(self):
        """System prompt must not reference web search results."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "web search" not in _SYSTEM_PROMPT.lower()

    def test_nfl_guardrail_present(self):
        """System prompt must restrict NFL claims to provided context only."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "NEVER inject NFL news" in _SYSTEM_PROMPT

    def test_no_fabricated_counts_guardrail(self):
        """System prompt must prohibit fabricating counts and statistics."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "NEVER fabricate counts" in _SYSTEM_PROMPT


class TestReadSubcommand:
    """The read subcommand should be registered in recap.py."""

    def test_subcommand_exists(self):
        import importlib.util
        recap_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "recap.py"
        )
        spec = importlib.util.spec_from_file_location("recap_cli", recap_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        parser = mod.build_parser()
        args = parser.parse_args([
            "read",
            "--db", "/tmp/test.db",
            "--league-id", "70985",
            "--season", "2024",
            "--week-index", "1",
        ])
        assert args.cmd == "read"
        assert hasattr(args, "fn")
