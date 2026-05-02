"""Tests for governed tone presets v1.

Verifies preset storage, retrieval, validation, voice directive generation,
creative layer integration, and default behavior.
"""

import sqlite3
from pathlib import Path

import pytest

from squadvault.ai.creative_layer_v1 import (
    _SYSTEM_PROMPT,
    _build_system_prompt,
)
from squadvault.core.tone.tone_profile_v1 import (
    DEFAULT_PRESET,
    VALID_PRESETS,
    VOICE_DIRECTIVES,
    get_tone_preset,
    get_voice_directive,
    set_tone_preset,
)


def _fresh_db(tmp_path):
    db_path = str(tmp_path / "tone.sqlite")
    schema = (Path(__file__).resolve().parent.parent / "src" / "squadvault"
              / "core" / "storage" / "schema.sql").read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)
    con.close()
    return db_path


# ── Storage ──────────────────────────────────────────────────────────


class TestToneProfileStorage:
    def test_default_when_no_profile(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        assert get_tone_preset(db_path, "L1") == DEFAULT_PRESET

    def test_set_and_get(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_tone_preset(db_path, "L1", "TRASH_TALK")
        assert get_tone_preset(db_path, "L1") == "TRASH_TALK"

    def test_update_overwrites(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_tone_preset(db_path, "L1", "TRASH_TALK")
        set_tone_preset(db_path, "L1", "FRIENDLY")
        assert get_tone_preset(db_path, "L1") == "FRIENDLY"

    def test_invalid_preset_raises(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        with pytest.raises(ValueError, match="Invalid tone preset"):
            set_tone_preset(db_path, "L1", "AGGRESSIVE")

    def test_case_insensitive_set(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_tone_preset(db_path, "L1", "friendly")
        assert get_tone_preset(db_path, "L1") == "FRIENDLY"

    def test_leagues_independent(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_tone_preset(db_path, "L1", "TRASH_TALK")
        set_tone_preset(db_path, "L2", "FRIENDLY")
        assert get_tone_preset(db_path, "L1") == "TRASH_TALK"
        assert get_tone_preset(db_path, "L2") == "FRIENDLY"


# ── Voice directives ─────────────────────────────────────────────────


class TestVoiceDirectives:
    def test_all_presets_have_directives(self):
        for preset in VALID_PRESETS:
            directive = get_voice_directive(preset)
            assert len(directive) > 50, f"Directive for {preset} is too short"
            assert "TONE PRESET" in directive

    def test_unknown_falls_back_to_pointed(self):
        directive = get_voice_directive("NONEXISTENT")
        assert directive == VOICE_DIRECTIVES["POINTED"]


# ── System prompt building ───────────────────────────────────────────


class TestSystemPromptBuilding:
    def test_pointed_returns_base(self):
        result = _build_system_prompt("POINTED")
        assert result == _SYSTEM_PROMPT

    def test_empty_returns_base(self):
        result = _build_system_prompt("")
        assert result == _SYSTEM_PROMPT

    def test_trash_talk_appends_directive(self):
        result = _build_system_prompt("TRASH_TALK")
        assert "TONE PRESET: TRASH TALK" in result
        # Hard rules still present
        assert "NEVER invent facts" in result

    def test_friendly_appends_directive(self):
        result = _build_system_prompt("FRIENDLY")
        assert "TONE PRESET: FRIENDLY" in result
        assert "Encouraging and celebratory" in result

    def test_hard_rules_after_tone_directive(self):
        """Hard rules must always be last in the system prompt."""
        result = _build_system_prompt("TRASH_TALK")
        tone_pos = result.index("TONE PRESET: TRASH TALK")
        hard_pos = result.index("Hard rules (non-negotiable):")
        assert tone_pos < hard_pos, (
            "Tone directive must appear before hard rules — "
            "models give higher weight to recency"
        )

    def test_hard_rules_last_for_all_presets(self):
        """Every non-POINTED preset puts hard rules after tone."""
        for preset in ("TRASH_TALK", "BALANCED", "FRIENDLY"):
            result = _build_system_prompt(preset)
            tone_marker = f"TONE PRESET: {preset.replace('_', ' ')}"
            assert result.index(tone_marker) < result.index("Hard rules"), (
                f"Preset {preset}: tone should precede hard rules"
            )
