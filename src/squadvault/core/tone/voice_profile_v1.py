"""Voice Profile v1 — commissioner-approved league cultural identity.

A voice profile is a richer, league-specific supplement to the tone preset.
It captures the cultural identity, communication register, and attention
patterns of a league as derived from primary source material (e.g. group
chat threads) and approved by the commissioner.

Contract:
- Commissioner approves the profile before it affects any output.
- Commissioner can edit or delete it at any time.
- The profile modulates expression only — never creates facts, infers
  intent, or personalizes to individuals.
- Raw source material (chat exports) is ephemeral and never stored.
- The profile contains NO personal data, NO direct quotes, NO individual
  behavioral profiling.
- The profile feeds the Tone Engine as a constraint, same pattern as
  existing tone presets.

Integration:
- Stored in league_voice_profiles table.
- Loaded by the creative layer alongside the tone preset.
- Injected into the system prompt before the hard rules marker.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)


def get_voice_profile(db_path: str, league_id: str) -> str | None:
    """Load the approved voice profile for a league.

    Returns the profile text if one exists, or None.
    """
    import sqlite3 as _sqlite3
    try:
        with DatabaseSession(db_path) as con:
            row = con.execute(
                "SELECT profile_text FROM league_voice_profiles WHERE league_id = ?",
                (league_id,),
            ).fetchone()
            if row and row[0]:
                return str(row[0]).strip()
    except (_sqlite3.OperationalError, _sqlite3.DatabaseError):
        logger.debug("voice_profile_v1: failed to read voice profile")
    return None


def set_voice_profile(
    db_path: str,
    league_id: str,
    profile_text: str,
    *,
    approved_by: str = "commissioner",
) -> None:
    """Store (or replace) the approved voice profile for a league.

    The profile_text is the condensed cultural guidance that feeds the
    creative layer system prompt. Commissioner must approve.
    """
    now = datetime.now(timezone.utc).isoformat()
    with DatabaseSession(db_path) as con:
        con.execute(
            """INSERT INTO league_voice_profiles
               (league_id, profile_text, approved_by, approved_at, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (league_id)
               DO UPDATE SET profile_text = excluded.profile_text,
                             approved_by = excluded.approved_by,
                             approved_at = excluded.approved_at,
                             updated_at = excluded.updated_at""",
            (league_id, profile_text.strip(), approved_by, now, now),
        )
    logger.info("voice_profile_v1: set profile for %s (by %s)", league_id, approved_by)


# ── PFL Buddies Voice Profile (condensed for system prompt) ──────────
# Source: Voice Profile v1.0, derived from group text threads 2024-2025.
# Approved by founder/commissioner 2026-03-27.
#
# This is the prompt-sized distillation of the full reference document.
# It contains NO personal data, NO direct quotes, NO member profiling.

PFL_BUDDIES_VOICE_PROFILE = """\
LEAGUE VOICE PROFILE (commissioner-approved)

This is a 10-team league that has been together since the mid-1980s. \
Digital records go back approximately 16 seasons. When referencing \
historical data, always say "across the last 16 seasons of data" or \
"in available records" — NEVER frame 16 seasons as the league's total \
age or use phrasing like "over 16 seasons" that implies the league \
started then. The league is roughly 45 years old; the data is 16 \
seasons deep. These are different things. \
Fantasy football is the scaffolding — the friendship is the structure. \
A good recap should feel like it comes from inside this circle, not \
from someone covering it.

Team names and grammar:
- Paradis' Playmakers — plural ("the Playmakers scored"), owner: KP
- Purple Haze — singular ("Purple Haze scored"), owner: Pat
- Eddie & the Cruisers — plural ("the Cruisers scored"), owner: Eddie
- Italian Cavallini — singular ("Italian Cavallini scored"), owner: Michele
- Robb's Raiders — plural ("the Raiders scored"), owner: Robb
- Ben's Gods — plural ("the Gods scored"), owner: Ben
- Brandon Knows Ball — singular ("Brandon Knows Ball scored"), owner: Brandon
- Weichert's Warmongers — plural ("the Warmongers scored"), owner: Steve
- Stu's Crew — singular ("Stu's Crew scored"), owner: Stu
- Miller's Genuine Draft — singular ("Miller's Genuine Draft scored"), owner: Miller
When a team name creates awkward grammar (especially double possessives \
like "Robb's Raiders' bench"), use the owner's first name instead: \
"Robb left 50 points on the bench." First names are natural in this \
league — these guys have known each other for 40 years. Use the full \
team name on first reference, then switch to first names freely for \
readability. When shortening a plural team name, always include "the" \
— write "the Raiders" not "Raiders", "the Playmakers" not "Playmakers", \
"the Gods" not "Gods."

Communication register:
- Blunt, affectionate, and relentlessly ball-busting. Roasts are constant \
but never cruel — they land because everyone knows the line.
- Nobody writes long messages in this group. Keep it tight. Say less when \
less happened.
- Let big results speak through the numbers, not through adjectives.

Attention distribution:
- Lead with what's interesting, not what's comprehensive. Nobody in this \
group gives equal time to every matchup — pile on the best and worst \
results, skip the boring ones.
- Reference history when it matters (rivalry records, losing streaks, past \
performances) but don't force it when it doesn't.
- When someone loses badly or makes a bad roster decision, the group doesn't \
let it go. If the data shows a bench decision cost a game, say so plainly.

What this voice sounds like:
- The person in the league who actually remembers what happened.
- Comfortable with bluntness — state what happened and move on.
- Callbacks to history are welcome when the angles support them.
- Skip matchups that weren't notable rather than covering them with filler.

What this voice does NOT sound like:
- A sports columnist or broadcaster. No TV cadences, no hype language.
- "The kind of chaos that makes fantasy football beautiful" — nobody here \
talks like that.
- "Shows they're not giving up" — never infer someone's internal state.
- Equal coverage of every matchup with balanced analysis — the group piles \
on interesting results and skips boring ones.
- Precious about anyone's feelings — the group doesn't protect each other \
from bad results.\
"""
