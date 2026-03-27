"""Governed Tone Presets v1 — commissioner-configurable voice for the creative layer.

Contract:
- Tone is governed, not improvised (Core Engine spec).
- Presets are a bounded set — no free-text injection into prompts.
- Commissioner controls the preset; changes are logged.
- Default is POINTED (current voice) if no profile is set.
- Tone modifies expression only — never creates, suppresses, or reorders facts.
- EAL restraint is independent: tone does not override EAL directives.

Presets:
- TRASH_TALK: sharp roasts, call-outs, group-chat energy
- POINTED: insider observations, affectionate roasting (default)
- BALANCED: warm and fair, highlights everyone
- FRIENDLY: encouraging, celebratory, safe for co-workers/family
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)

# The default preset if no profile is set for a league
DEFAULT_PRESET = "POINTED"

# Bounded set of valid presets
VALID_PRESETS = frozenset({"TRASH_TALK", "POINTED", "BALANCED", "FRIENDLY"})

# ── Voice directives (injected into the creative layer system prompt) ──

VOICE_DIRECTIVES = {
    "TRASH_TALK": """\
TONE PRESET: TRASH TALK
This league expects heat. Roasts are sharp, direct, and personal (to the team, \
never the person). Call out bad performances without mercy. Mock questionable \
roster moves. If someone lost badly, they should feel it in the recap. Winners \
get credit, losers get roasted. Think group chat energy after a blowout — the \
kind of trash talk that makes the loser fire back with a waiver claim. \
Keep it fun, not cruel — everyone is here because they love this league.""",

    "POINTED": """\
TONE PRESET: POINTED
Sharp insider observations with affectionate roasting. You're the late-night \
desk host — you have opinions and they're grounded in data. Roasts are warm, \
never cruel. You notice the details others miss. The tone says: "I've been \
watching this league all season and I have thoughts." Sarcasm is permitted \
when earned by the data.""",

    "BALANCED": """\
TONE PRESET: BALANCED
Warm, fair, and informative. Give every team their moment in the recap. \
Highlight strong performances without diminishing anyone. Observations are \
grounded and even-handed. Light humor is fine but keep it gentle. The tone \
says: "Everyone had a week worth talking about." Good for leagues where \
members have varying comfort with ribbing.""",

    "FRIENDLY": """\
TONE PRESET: FRIENDLY
Encouraging and celebratory. Notice effort and participation. Frame losses \
constructively ("tough week, but the roster moves show they're not giving up"). \
Celebrate wins warmly. Avoid sarcasm, roasting, or anything that could sting. \
The tone says: "This league is fun and everyone is part of it." Perfect for \
co-worker leagues, family leagues, or leagues with newer members.""",
}


def get_tone_preset(db_path: str, league_id: str) -> str:
    """Read the current tone preset for a league. Returns DEFAULT_PRESET if unset."""
    import sqlite3 as _sqlite3
    try:
        with DatabaseSession(db_path) as con:
            row = con.execute(
                "SELECT tone_preset FROM league_tone_profiles WHERE league_id = ?",
                (league_id,),
            ).fetchone()
            if row and row[0] in VALID_PRESETS:
                return str(row[0])
    except (_sqlite3.OperationalError, _sqlite3.DatabaseError):
        logger.debug("tone_profile_v1: failed to read tone profile, using default")
    return DEFAULT_PRESET


def set_tone_preset(
    db_path: str,
    league_id: str,
    preset: str,
    *,
    set_by: str = "commissioner",
    notes: Optional[str] = None,
) -> str:
    """Set (or update) the tone preset for a league.

    Returns the preset that was set.
    Raises ValueError if the preset is not in VALID_PRESETS.
    """
    preset = preset.upper().strip()
    if preset not in VALID_PRESETS:
        raise ValueError(
            f"Invalid tone preset: {preset!r}. "
            f"Valid presets: {', '.join(sorted(VALID_PRESETS))}"
        )
    now = datetime.now(timezone.utc).isoformat()
    with DatabaseSession(db_path) as con:
        con.execute(
            """INSERT INTO league_tone_profiles
               (league_id, tone_preset, set_by, notes, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (league_id)
               DO UPDATE SET tone_preset = excluded.tone_preset,
                             set_by = excluded.set_by,
                             notes = excluded.notes,
                             created_at = excluded.created_at""",
            (league_id, preset, set_by, notes, now),
        )
    logger.info("tone_profile_v1: set %s -> %s (by %s)", league_id, preset, set_by)
    return preset


def get_voice_directive(preset: str) -> str:
    """Return the voice directive text for a given preset.

    Falls back to POINTED if the preset is unknown.
    """
    return VOICE_DIRECTIVES.get(preset, VOICE_DIRECTIVES[DEFAULT_PRESET])
