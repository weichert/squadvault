"""Tests for writer room context guardrails.

Verifies that:
- System prompt references WRITER ROOM for stats verification
- Roster activity derivation was retired (fabrication risk)
"""
from __future__ import annotations


class TestRosterActivityRetired:
    """Roster activity derivation was removed to prevent aggregate fabrication."""

    def test_roster_activity_class_removed(self):
        """RosterActivity should no longer be importable from writer_room_context_v1."""
        from squadvault.core.recaps.context import writer_room_context_v1 as mod
        assert not hasattr(mod, "RosterActivity"), (
            "RosterActivity should have been removed — aggregate counts "
            "fed to the LLM were a fabrication vector."
        )

    def test_derive_roster_activity_removed(self):
        """derive_roster_activity should no longer be importable."""
        from squadvault.core.recaps.context import writer_room_context_v1 as mod
        assert not hasattr(mod, "derive_roster_activity"), (
            "derive_roster_activity should have been removed."
        )

    def test_render_no_roster_activity_param(self):
        """render_writer_room_context_for_prompt should not accept roster_activity."""
        import inspect

        from squadvault.core.recaps.context.writer_room_context_v1 import (
            render_writer_room_context_for_prompt,
        )
        sig = inspect.signature(render_writer_room_context_for_prompt)
        assert "roster_activity" not in sig.parameters, (
            "roster_activity parameter should have been removed from "
            "render_writer_room_context_for_prompt."
        )


class TestStatsGuardrail:
    """System prompt should forbid aggregate roster count fabrication."""

    def test_guardrail_present(self):
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "Do NOT claim" in _SYSTEM_PROMPT or "do not claim" in _SYSTEM_PROMPT.lower()
