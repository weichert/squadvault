"""Tests for Voice Profile v1 — commissioner-approved cultural guidance."""
from __future__ import annotations

import os
import sqlite3

from squadvault.core.tone.voice_profile_v1 import (
    PFL_BUDDIES_VOICE_PROFILE,
    get_voice_profile,
    set_voice_profile,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "test_league"


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


class TestVoiceProfileStorage:
    def test_no_profile_returns_none(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        assert get_voice_profile(db_path, LEAGUE) is None

    def test_set_and_get(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_voice_profile(db_path, LEAGUE, "Test profile text")
        result = get_voice_profile(db_path, LEAGUE)
        assert result == "Test profile text"

    def test_update_replaces(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_voice_profile(db_path, LEAGUE, "Version 1")
        set_voice_profile(db_path, LEAGUE, "Version 2")
        assert get_voice_profile(db_path, LEAGUE) == "Version 2"

        # Verify only one row
        con = sqlite3.connect(db_path)
        count = con.execute(
            "SELECT COUNT(*) FROM league_voice_profiles WHERE league_id=?",
            (LEAGUE,),
        ).fetchone()[0]
        con.close()
        assert count == 1

    def test_strips_whitespace(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_voice_profile(db_path, LEAGUE, "  padded text  \n")
        assert get_voice_profile(db_path, LEAGUE) == "padded text"

    def test_different_leagues_independent(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_voice_profile(db_path, "league_a", "Profile A")
        set_voice_profile(db_path, "league_b", "Profile B")
        assert get_voice_profile(db_path, "league_a") == "Profile A"
        assert get_voice_profile(db_path, "league_b") == "Profile B"


class TestPflBuddiesProfile:
    def test_profile_is_nonempty(self):
        assert len(PFL_BUDDIES_VOICE_PROFILE) > 100

    def test_profile_contains_key_guidance(self):
        assert "blunt" in PFL_BUDDIES_VOICE_PROFILE.lower()
        assert "interesting" in PFL_BUDDIES_VOICE_PROFILE.lower()
        assert "broadcaster" in PFL_BUDDIES_VOICE_PROFILE.lower()

    def test_profile_contains_no_personal_data(self):
        # Per Voice Profile v1.0 Section 7 prohibitions
        profile_lower = PFL_BUDDIES_VOICE_PROFILE.lower()
        assert "chemo" not in profile_lower
        assert "divorce" not in profile_lower
        assert "political" not in profile_lower

    def test_profile_stores_and_loads(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        set_voice_profile(db_path, "70985", PFL_BUDDIES_VOICE_PROFILE)
        loaded = get_voice_profile(db_path, "70985")
        assert loaded == PFL_BUDDIES_VOICE_PROFILE.strip()


class TestVoiceProfileIntegration:
    def test_system_prompt_includes_profile(self):
        """Voice profile is injected into the system prompt."""
        from squadvault.ai.creative_layer_v1 import _build_system_prompt
        prompt = _build_system_prompt(voice_profile="TEST VOICE PROFILE")
        assert "TEST VOICE PROFILE" in prompt
        # Hard rules still present and after the profile
        assert "Hard rules (non-negotiable):" in prompt
        profile_pos = prompt.index("TEST VOICE PROFILE")
        rules_pos = prompt.index("Hard rules (non-negotiable):")
        assert profile_pos < rules_pos

    def test_system_prompt_with_both_tone_and_profile(self):
        from squadvault.ai.creative_layer_v1 import _build_system_prompt
        prompt = _build_system_prompt(
            tone_preset="TRASH_TALK",
            voice_profile="CUSTOM LEAGUE VOICE",
        )
        assert "TRASH TALK" in prompt
        assert "CUSTOM LEAGUE VOICE" in prompt
        assert "Hard rules (non-negotiable):" in prompt

    def test_system_prompt_no_profile_unchanged(self):
        from squadvault.ai.creative_layer_v1 import _build_system_prompt
        base = _build_system_prompt()
        no_profile = _build_system_prompt(voice_profile="")
        assert base == no_profile
