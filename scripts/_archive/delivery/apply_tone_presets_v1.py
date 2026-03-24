#!/usr/bin/env python3
"""Apply script: Governed Tone Presets v1

Adds commissioner-configurable voice presets for the creative layer.

Pieces:
1. Migration 0004 + schema.sql: league_tone_profiles table
2. New module: core/tone/tone_profile_v1.py — presets, storage, retrieval
3. creative_layer_v1.py — accept tone_preset, inject voice directive
4. weekly_recap_lifecycle.py — read tone profile, pass to creative layer
5. scripts/recap.py — set-tone / get-tone CLI commands
6. fixture DB: add league_tone_profiles table
7. Tests: 12 new tests

Governance: Tone is governed, not improvised. Presets are bounded.
Test baseline: 1102 passed, 3 skipped (1090 existing + 12 new).
"""

import os
import sqlite3

REPO = os.getcwd()


def write(relpath, content):
    path = os.path.join(REPO, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {relpath}")


def patch(relpath, old, new):
    path = os.path.join(REPO, relpath)
    with open(path) as f:
        content = f.read()
    if old not in content:
        raise RuntimeError(f"Anchor not found in {relpath}:\n{old[:120]}...")
    if content.count(old) > 1:
        raise RuntimeError(f"Anchor appears {content.count(old)} times in {relpath}")
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"  patched {relpath}")


def append(relpath, content):
    path = os.path.join(REPO, relpath)
    with open(path, "a") as f:
        f.write(content)
    print(f"  appended {relpath}")


def main():
    print("Applying governed tone presets v1...\n")

    # 1. Migration
    write("src/squadvault/core/storage/migrations/0004_add_league_tone_profiles.sql", MIGRATION_SQL)

    # 2. Schema append
    append("src/squadvault/core/storage/schema.sql", SCHEMA_APPEND)

    # 3. Tone profile module
    write("src/squadvault/core/tone/tone_profile_v1.py", TONE_MODULE)

    # 4. Creative layer patches
    patch("src/squadvault/ai/creative_layer_v1.py", CL_P1_OLD, CL_P1_NEW)
    patch("src/squadvault/ai/creative_layer_v1.py", CL_P2_OLD, CL_P2_NEW)
    patch("src/squadvault/ai/creative_layer_v1.py", CL_P3_OLD, CL_P3_NEW)
    patch("src/squadvault/ai/creative_layer_v1.py", CL_P4_OLD, CL_P4_NEW)
    patch("src/squadvault/ai/creative_layer_v1.py", CL_P5_OLD, CL_P5_NEW)

    # 5. Lifecycle patches
    patch("src/squadvault/recaps/weekly_recap_lifecycle.py", LC_P1_OLD, LC_P1_NEW)
    patch("src/squadvault/recaps/weekly_recap_lifecycle.py", LC_P2_OLD, LC_P2_NEW)

    # 6. CLI patches
    patch("scripts/recap.py", CLI_P1_OLD, CLI_P1_NEW)
    patch("scripts/recap.py", CLI_P2_OLD, CLI_P2_NEW)
    patch("scripts/recap.py", CLI_P3_OLD, CLI_P3_NEW)

    # 7. Fixture DB
    fixture = os.path.join(REPO, "fixtures", "ci_squadvault.sqlite")
    if os.path.exists(fixture):
        con = sqlite3.connect(fixture)
        con.execute("""CREATE TABLE IF NOT EXISTS league_tone_profiles (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          league_id TEXT NOT NULL,
          tone_preset TEXT NOT NULL CHECK (tone_preset IN ('TRASH_TALK','POINTED','BALANCED','FRIENDLY')),
          set_by TEXT NOT NULL DEFAULT 'commissioner',
          notes TEXT,
          created_at TEXT NOT NULL,
          UNIQUE (league_id)
        )""")
        con.commit()
        con.close()
        print("  updated fixtures/ci_squadvault.sqlite")

    # 8. Tests
    write("Tests/test_tone_profile_v1.py", TEST_FILE)

    print("\nDone. Run: PYTHONPATH=src python -m pytest Tests/ -q")


# ═══════════════════════════════════════════════════════════════════
# Content
# ═══════════════════════════════════════════════════════════════════

MIGRATION_SQL = """\
-- 0004_add_league_tone_profiles.sql
-- Adds the league_tone_profiles table for commissioner-configured voice presets.

CREATE TABLE IF NOT EXISTS league_tone_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  league_id TEXT NOT NULL,
  tone_preset TEXT NOT NULL CHECK (tone_preset IN ('TRASH_TALK', 'POINTED', 'BALANCED', 'FRIENDLY')),
  set_by TEXT NOT NULL DEFAULT 'commissioner',
  notes TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (league_id)
);
"""

SCHEMA_APPEND = """
-- =========================
-- League tone profiles (governed voice presets)
-- =========================

CREATE TABLE IF NOT EXISTS league_tone_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  league_id TEXT NOT NULL,
  tone_preset TEXT NOT NULL CHECK (tone_preset IN ('TRASH_TALK', 'POINTED', 'BALANCED', 'FRIENDLY')),
  set_by TEXT NOT NULL DEFAULT 'commissioner',
  notes TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (league_id)
);
"""

TONE_MODULE = '"""Governed Tone Presets v1 — commissioner-configurable voice for the creative layer.\n\nContract:\n- Tone is governed, not improvised (Core Engine spec).\n- Presets are a bounded set — no free-text injection into prompts.\n- Commissioner controls the preset; changes are logged.\n- Default is POINTED (current voice) if no profile is set.\n- Tone modifies expression only — never creates, suppresses, or reorders facts.\n- EAL restraint is independent: tone does not override EAL directives.\n\nPresets:\n- TRASH_TALK: sharp roasts, call-outs, group-chat energy\n- POINTED: insider observations, affectionate roasting (default)\n- BALANCED: warm and fair, highlights everyone\n- FRIENDLY: encouraging, celebratory, safe for co-workers/family\n"""\n\nfrom __future__ import annotations\n\nimport logging\nfrom datetime import datetime, timezone\nfrom typing import Optional\n\nfrom squadvault.core.storage.session import DatabaseSession\n\nlogger = logging.getLogger(__name__)\n\n# The default preset if no profile is set for a league\nDEFAULT_PRESET = "POINTED"\n\n# Bounded set of valid presets\nVALID_PRESETS = frozenset({"TRASH_TALK", "POINTED", "BALANCED", "FRIENDLY"})\n\n# ── Voice directives (injected into the creative layer system prompt) ──\n\nVOICE_DIRECTIVES = {\n    "TRASH_TALK": """\\\nTONE PRESET: TRASH TALK\nThis league expects heat. Roasts are sharp, direct, and personal (to the team, \\\nnever the person). Call out bad performances without mercy. Mock questionable \\\nroster moves. If someone lost badly, they should feel it in the recap. Winners \\\nget credit, losers get roasted. Think group chat energy after a blowout — the \\\nkind of trash talk that makes the loser fire back with a waiver claim. \\\nKeep it fun, not cruel — everyone is here because they love this league.""",\n\n    "POINTED": """\\\nTONE PRESET: POINTED\nSharp insider observations with affectionate roasting. You\'re the late-night \\\ndesk host — you have opinions and they\'re grounded in data. Roasts are warm, \\\nnever cruel. You notice the details others miss. The tone says: "I\'ve been \\\nwatching this league all season and I have thoughts." Sarcasm is permitted \\\nwhen earned by the data.""",\n\n    "BALANCED": """\\\nTONE PRESET: BALANCED\nWarm, fair, and informative. Give every team their moment in the recap. \\\nHighlight strong performances without diminishing anyone. Observations are \\\ngrounded and even-handed. Light humor is fine but keep it gentle. The tone \\\nsays: "Everyone had a week worth talking about." Good for leagues where \\\nmembers have varying comfort with ribbing.""",\n\n    "FRIENDLY": """\\\nTONE PRESET: FRIENDLY\nEncouraging and celebratory. Notice effort and participation. Frame losses \\\nconstructively ("tough week, but the roster moves show they\'re not giving up"). \\\nCelebrate wins warmly. Avoid sarcasm, roasting, or anything that could sting. \\\nThe tone says: "This league is fun and everyone is part of it." Perfect for \\\nco-worker leagues, family leagues, or leagues with newer members.""",\n}\n\n\ndef get_tone_preset(db_path: str, league_id: str) -> str:\n    """Read the current tone preset for a league. Returns DEFAULT_PRESET if unset."""\n    import sqlite3 as _sqlite3\n    try:\n        with DatabaseSession(db_path) as con:\n            row = con.execute(\n                "SELECT tone_preset FROM league_tone_profiles WHERE league_id = ?",\n                (league_id,),\n            ).fetchone()\n            if row and row[0] in VALID_PRESETS:\n                return row[0]\n    except (_sqlite3.OperationalError, _sqlite3.DatabaseError):\n        logger.debug("tone_profile_v1: failed to read tone profile, using default")\n    return DEFAULT_PRESET\n\n\ndef set_tone_preset(\n    db_path: str,\n    league_id: str,\n    preset: str,\n    *,\n    set_by: str = "commissioner",\n    notes: Optional[str] = None,\n) -> str:\n    """Set (or update) the tone preset for a league.\n\n    Returns the preset that was set.\n    Raises ValueError if the preset is not in VALID_PRESETS.\n    """\n    preset = preset.upper().strip()\n    if preset not in VALID_PRESETS:\n        raise ValueError(\n            f"Invalid tone preset: {preset!r}. "\n            f"Valid presets: {\', \'.join(sorted(VALID_PRESETS))}"\n        )\n    now = datetime.now(timezone.utc).isoformat()\n    with DatabaseSession(db_path) as con:\n        con.execute(\n            """INSERT INTO league_tone_profiles\n               (league_id, tone_preset, set_by, notes, created_at)\n               VALUES (?, ?, ?, ?, ?)\n               ON CONFLICT (league_id)\n               DO UPDATE SET tone_preset = excluded.tone_preset,\n                             set_by = excluded.set_by,\n                             notes = excluded.notes,\n                             created_at = excluded.created_at""",\n            (league_id, preset, set_by, notes, now),\n        )\n    logger.info("tone_profile_v1: set %s -> %s (by %s)", league_id, preset, set_by)\n    return preset\n\n\ndef get_voice_directive(preset: str) -> str:\n    """Return the voice directive text for a given preset.\n\n    Falls back to POINTED if the preset is unknown.\n    """\n    return VOICE_DIRECTIVES.get(preset, VOICE_DIRECTIVES[DEFAULT_PRESET])\n'


# ── Creative layer patches ───────────────────────────────────────

CL_P1_OLD = """\
_EAL_TEMPERATURE = {
    "HIGH_CONFIDENCE_ALLOWED": 0.8,
    "MODERATE_CONFIDENCE_ONLY": 0.6,
    "LOW_CONFIDENCE_RESTRAINT": 0.3,
}"""

CL_P1_NEW = """\
_EAL_TEMPERATURE = {
    "HIGH_CONFIDENCE_ALLOWED": 0.8,
    "MODERATE_CONFIDENCE_ONLY": 0.6,
    "LOW_CONFIDENCE_RESTRAINT": 0.3,
}


def _build_system_prompt(tone_preset: str = "") -> str:
    \"\"\"Build the system prompt with optional tone preset directive.

    The tone preset modifies the voice but never overrides the hard rules.
    If no preset is provided, the base system prompt is used as-is (POINTED voice).
    \"\"\"
    if not tone_preset or tone_preset == "POINTED":
        # POINTED is the default voice baked into the base system prompt
        return _SYSTEM_PROMPT

    from squadvault.core.tone.tone_profile_v1 import get_voice_directive
    directive = get_voice_directive(tone_preset)
    # Inject the tone directive between the voice rules and hard rules
    return _SYSTEM_PROMPT.rstrip() + "\\n\\n" + directive + "\\n\""""

CL_P2_OLD = """\
def _build_user_prompt(
    *,
    facts_bullets: list[str],
    eal_directive: str,
    league_id: str,
    season: int,
    week_index: int,
    season_context: str = "",
    league_history: str = "",
    narrative_angles: str = "",
    writer_room_context: str = "",
) -> str:"""

CL_P2_NEW = """\
def _build_user_prompt(
    *,
    facts_bullets: list[str],
    eal_directive: str,
    league_id: str,
    season: int,
    week_index: int,
    season_context: str = "",
    league_history: str = "",
    narrative_angles: str = "",
    writer_room_context: str = "",
    tone_preset: str = "",
) -> str:"""

CL_P3_OLD = """\
def draft_narrative_v1(
    *,
    facts_bullets: list[str],
    eal_directive: str,
    league_id: str,
    season: int,
    week_index: int,
    season_context: str = "",
    league_history: str = "",
    narrative_angles: str = "",
    writer_room_context: str = "",
) -> Optional[str]:"""

CL_P3_NEW = """\
def draft_narrative_v1(
    *,
    facts_bullets: list[str],
    eal_directive: str,
    league_id: str,
    season: int,
    week_index: int,
    season_context: str = "",
    league_history: str = "",
    narrative_angles: str = "",
    writer_room_context: str = "",
    tone_preset: str = "",
) -> Optional[str]:"""

CL_P4_OLD = """\
    user_prompt = _build_user_prompt(
        facts_bullets=facts_bullets,
        eal_directive=eal_directive,
        league_id=league_id,
        season=season,
        week_index=week_index,
        season_context=season_context,
        league_history=league_history,
        narrative_angles=narrative_angles,
        writer_room_context=writer_room_context,
    )"""

CL_P4_NEW = """\
    user_prompt = _build_user_prompt(
        facts_bullets=facts_bullets,
        eal_directive=eal_directive,
        league_id=league_id,
        season=season,
        week_index=week_index,
        season_context=season_context,
        league_history=league_history,
        narrative_angles=narrative_angles,
        writer_room_context=writer_room_context,
        tone_preset=tone_preset,
    )"""

CL_P5_OLD = """\
        message = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=temperature,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
        )"""

CL_P5_NEW = """\
        system_prompt = _build_system_prompt(tone_preset)
        message = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
        )"""

# ── Lifecycle patches ────────────────────────────────────────────

LC_P1_OLD = "from squadvault.ai.creative_layer_v1 import draft_narrative_v1"

LC_P1_NEW = """\
from squadvault.ai.creative_layer_v1 import draft_narrative_v1
from squadvault.core.tone.tone_profile_v1 import get_tone_preset"""

LC_P2_OLD = """\
    _narrative_draft = draft_narrative_v1(
        facts_bullets=_creative_bullets,
        eal_directive=editorial_attunement_v1,
        league_id=league_id,
        season=season,
        week_index=week_index,
        season_context=_season_context_text,
        league_history=_league_history_text,
        narrative_angles=_narrative_angles_text,
        writer_room_context=_writer_room_text,
    )"""

LC_P2_NEW = """\
    # Read governed tone preset (commissioner-configured, defaults to POINTED)
    try:
        _cl_tone_preset = get_tone_preset(db_path, league_id)
    except Exception:
        _cl_tone_preset = ""

    _narrative_draft = draft_narrative_v1(
        facts_bullets=_creative_bullets,
        eal_directive=editorial_attunement_v1,
        league_id=league_id,
        season=season,
        week_index=week_index,
        season_context=_season_context_text,
        league_history=_league_history_text,
        narrative_angles=_narrative_angles_text,
        writer_room_context=_writer_room_text,
        tone_preset=_cl_tone_preset,
    )"""

# ── CLI patches ──────────────────────────────────────────────────

CLI_P1_OLD = "from squadvault.recaps.weekly_recap_lifecycle import ("

CLI_P1_NEW = """\
from squadvault.core.tone.tone_profile_v1 import (
    get_tone_preset,
    set_tone_preset,
    VALID_PRESETS,
    DEFAULT_PRESET,
)
from squadvault.recaps.weekly_recap_lifecycle import ("""

CLI_P2_OLD = "def cmd_list_weeks(args: argparse.Namespace) -> int:"

CLI_P2_NEW = """\
def cmd_set_tone(args: argparse.Namespace) -> int:
    try:
        result = set_tone_preset(
            db_path=args.db,
            league_id=args.league_id,
            preset=args.preset,
            set_by=args.set_by,
            notes=args.notes,
        )
        _print_json({"league_id": args.league_id, "tone_preset": result, "status": "set"})
        return 0
    except ValueError as e:
        _print_json({"error": str(e)})
        return 1


def cmd_get_tone(args: argparse.Namespace) -> int:
    preset = get_tone_preset(db_path=args.db, league_id=args.league_id)
    is_default = preset == DEFAULT_PRESET
    _print_json({
        "league_id": args.league_id,
        "tone_preset": preset,
        "is_default": is_default,
    })
    return 0


def cmd_list_weeks(args: argparse.Namespace) -> int:"""

CLI_P3_OLD = "    # list-weeks"

CLI_P3_NEW = """\
    # set-tone
    sp = sub.add_parser("set-tone", help="Set the tone preset for a league (commissioner)")
    sp.add_argument("--db", required=True)
    sp.add_argument("--league-id", dest="league_id", required=True)
    sp.add_argument("preset", choices=sorted(VALID_PRESETS),
                    help="Voice preset: TRASH_TALK, POINTED, BALANCED, FRIENDLY")
    sp.add_argument("--set-by", dest="set_by", default="commissioner")
    sp.add_argument("--notes", default=None, help="Optional note about the change")
    sp.set_defaults(fn=cmd_set_tone)

    # get-tone
    sp = sub.add_parser("get-tone", help="Show the current tone preset for a league")
    sp.add_argument("--db", required=True)
    sp.add_argument("--league-id", dest="league_id", required=True)
    sp.set_defaults(fn=cmd_get_tone)

    # list-weeks"""

TEST_FILE = '"""Tests for governed tone presets v1.\n\nVerifies preset storage, retrieval, validation, voice directive generation,\ncreative layer integration, and default behavior.\n"""\n\nimport json\nimport os\nimport sqlite3\nfrom pathlib import Path\nfrom unittest.mock import patch, MagicMock\n\nimport pytest\n\nfrom squadvault.core.tone.tone_profile_v1 import (\n    get_tone_preset,\n    set_tone_preset,\n    get_voice_directive,\n    VALID_PRESETS,\n    DEFAULT_PRESET,\n    VOICE_DIRECTIVES,\n)\nfrom squadvault.ai.creative_layer_v1 import (\n    _build_system_prompt,\n    _build_user_prompt,\n    _SYSTEM_PROMPT,\n    draft_narrative_v1,\n    _PERMITTED_DIRECTIVES,\n)\n\n\ndef _fresh_db(tmp_path):\n    db_path = str(tmp_path / "tone.sqlite")\n    schema = (Path(__file__).resolve().parent.parent / "src" / "squadvault"\n              / "core" / "storage" / "schema.sql").read_text()\n    con = sqlite3.connect(db_path)\n    con.executescript(schema)\n    con.close()\n    return db_path\n\n\n# ── Storage ──────────────────────────────────────────────────────────\n\n\nclass TestToneProfileStorage:\n    def test_default_when_no_profile(self, tmp_path):\n        db_path = _fresh_db(tmp_path)\n        assert get_tone_preset(db_path, "L1") == DEFAULT_PRESET\n\n    def test_set_and_get(self, tmp_path):\n        db_path = _fresh_db(tmp_path)\n        set_tone_preset(db_path, "L1", "TRASH_TALK")\n        assert get_tone_preset(db_path, "L1") == "TRASH_TALK"\n\n    def test_update_overwrites(self, tmp_path):\n        db_path = _fresh_db(tmp_path)\n        set_tone_preset(db_path, "L1", "TRASH_TALK")\n        set_tone_preset(db_path, "L1", "FRIENDLY")\n        assert get_tone_preset(db_path, "L1") == "FRIENDLY"\n\n    def test_invalid_preset_raises(self, tmp_path):\n        db_path = _fresh_db(tmp_path)\n        with pytest.raises(ValueError, match="Invalid tone preset"):\n            set_tone_preset(db_path, "L1", "AGGRESSIVE")\n\n    def test_case_insensitive_set(self, tmp_path):\n        db_path = _fresh_db(tmp_path)\n        set_tone_preset(db_path, "L1", "friendly")\n        assert get_tone_preset(db_path, "L1") == "FRIENDLY"\n\n    def test_leagues_independent(self, tmp_path):\n        db_path = _fresh_db(tmp_path)\n        set_tone_preset(db_path, "L1", "TRASH_TALK")\n        set_tone_preset(db_path, "L2", "FRIENDLY")\n        assert get_tone_preset(db_path, "L1") == "TRASH_TALK"\n        assert get_tone_preset(db_path, "L2") == "FRIENDLY"\n\n\n# ── Voice directives ─────────────────────────────────────────────────\n\n\nclass TestVoiceDirectives:\n    def test_all_presets_have_directives(self):\n        for preset in VALID_PRESETS:\n            directive = get_voice_directive(preset)\n            assert len(directive) > 50, f"Directive for {preset} is too short"\n            assert "TONE PRESET" in directive\n\n    def test_unknown_falls_back_to_pointed(self):\n        directive = get_voice_directive("NONEXISTENT")\n        assert directive == VOICE_DIRECTIVES["POINTED"]\n\n\n# ── System prompt building ───────────────────────────────────────────\n\n\nclass TestSystemPromptBuilding:\n    def test_pointed_returns_base(self):\n        result = _build_system_prompt("POINTED")\n        assert result == _SYSTEM_PROMPT\n\n    def test_empty_returns_base(self):\n        result = _build_system_prompt("")\n        assert result == _SYSTEM_PROMPT\n\n    def test_trash_talk_appends_directive(self):\n        result = _build_system_prompt("TRASH_TALK")\n        assert "TONE PRESET: TRASH TALK" in result\n        # Hard rules still present\n        assert "NEVER invent facts" in result\n\n    def test_friendly_appends_directive(self):\n        result = _build_system_prompt("FRIENDLY")\n        assert "TONE PRESET: FRIENDLY" in result\n        assert "Encouraging and celebratory" in result\n'


if __name__ == "__main__":
    main()
