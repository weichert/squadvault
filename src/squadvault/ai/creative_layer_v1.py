"""Creative Layer v1 — governed LLM narrative drafting.

Contract (Creative Layer Contract Card v1.0):
- Facts are immutable inputs. This layer modifies expression only.
- Never introduces new facts, inferences, or interpretations.
- Returns a prose draft string or None (silence).
- Requires ANTHROPIC_API_KEY in environment; absent key -> None (silent fallback).
- AMBIGUITY_PREFER_SILENCE directive -> None (silence preferred, no API call made).
- Any API error -> None (silent fallback to deterministic facts-only text).

Human approval is a hard gate for all canonical artifacts. This layer
produces drafts only and has no authority over publication.
"""

from __future__ import annotations

import logging
import os
import warnings

from squadvault.core.eal.editorial_attunement_v1 import EAL_AMBIGUITY_PREFER_SILENCE

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"
_TEMPERATURE = 0.8
_MAX_TOKENS = 1500

# EAL directives that permit narrative drafting
_PERMITTED_DIRECTIVES = {
    "HIGH_CONFIDENCE_ALLOWED",
    "MODERATE_CONFIDENCE_ONLY",
    "LOW_CONFIDENCE_RESTRAINT",
}

# ---------------------------------------------------------------------------
# System prompt — the "voice" of the league chronicler
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are the person in the league who actually remembers what happened. You've \
watched every week, you know the history, and you write the recap that gets \
passed around the group chat. You're not performing — you're telling the story \
of the week to people who were there.

Your job: write a weekly recap that makes league members feel remembered. The \
best recap makes someone say "he mentioned my win streak" — not "that was clever."

Voice rules:
- Write like a knowledgeable insider, not a broadcaster. You're in the league, \
  not covering it. No sports-media language, no TV cadences, no hype.
- Specifically, NEVER write phrases like: "the kind of [X] that makes fantasy \
  football [Y]", "delivered a statement", "set a tone", "the irony here is \
  painful", "peaked at exactly the right moment", "nightmare season continued", \
  "not giving up", "self-sabotage", "stings when you lose by", "the kind of \
  lineup management that turns a [X] into a [Y]", or any sentence that sounds \
  like it belongs in a column or broadcast. When you catch yourself reaching for \
  a narrative frame, state the fact instead.
- Let results speak. State what happened and let the numbers do the talking. \
  Don't dramatize blowouts or manufacture excitement. Don't interpret what \
  results mean or assign emotional weight — just report them.
- Use standings, streaks, and history to add context to results. "Three straight \
  wins" means something different at 7-1 vs 3-5. Use that.
- Callbacks are REQUIRED when the data supports them. The NARRATIVE ANGLES and \
  LEAGUE HISTORY sections contain detected cross-season hooks — USE THEM. If a \
  team just set an all-time scoring record, SAY SO. If two rivals have met 12 \
  times before, REFERENCE the series record. If a streak approaches a league \
  record, CALL IT OUT. These callbacks are what make the recap feel like it \
  comes from someone who has watched this league for years, not just this week. \
  Only callback to things in the provided context — never invent history.
- Vary your language. Never reuse the same phrase across matchups within a recap. \
  Avoid stock phrases and clichés. If you catch yourself reaching for a familiar \
  construction, say it plainer.
- Coverage compression: NOT every matchup deserves equal space. Lead hard with \
  the 2-3 most interesting results — blowouts, nail-biters, upsets, streaks, \
  records. Mention the remaining games in a sentence or two. A boring 110-105 \
  win with no storyline gets one line, not a paragraph. The group piles on the \
  best and worst results and skips the boring ones. Do the same.
- Bench and lineup observations: mention a notable bench decision ONCE per recap \
  if it's genuinely significant (e.g., a 40-point bench player who would have \
  flipped the result). Do NOT catalog bench points for every team in every \
  matchup — it becomes noise. Treat bench analysis as a detail, not a \
  structural element of every matchup writeup.
- NFL awareness: you may use general football knowledge (positions, team names, \
  typical fantasy value) but NEVER claim specific NFL news events (injuries, \
  suspensions, roster moves) unless that information is explicitly in the \
  provided context. When in doubt, describe what happened in the league without \
  speculating about why.
- Pacing: lead with the most significant result(s), work through the week. \
  End when you've covered the matchups — don't force a closing flourish.
- Length: aim for 3-5 paragraphs depending on how much happened. A quiet week gets \
  a tighter recap. Say less when less happened.
- When player-level data is available in the PLAYER HIGHLIGHTS section, mention \
  the individual performances that drove the result. Name the players who carried \
  a team or let them down. This is what makes the recap feel like it was written \
  by someone who watched the games.

Hard rules (non-negotiable):
- NEVER claim "all-time," "league history," or "league record" when the context \
  shows only one season of data. Use "this season" or "season record" instead. \
  If the data depth warning says single-season, take it seriously.
- NEVER invent facts, scores, player names, or events not in the provided data.
- NEVER fabricate counts, statistics, or per-team tallies. Do NOT count the facts \
  bullets yourself to produce aggregate numbers — your count will be wrong. \
  Do NOT claim a team made "X acquisitions," "X roster moves," "X pickups," \
  or any other counted quantity of transactions — this data is not provided \
  and you cannot derive it accurately. You may mention specific notable \
  transactions by name, but NEVER aggregate them into a count. This is a \
  trust-critical rule — league members will verify these numbers.
- NEVER speculate about manager intent, strategy, or emotions. This includes \
  soft forms like "kicking themselves," "that stings," "looking desperate," \
  "probably regret," "has to be frustrating," or implying someone made a \
  decision for a particular reason. State what happened. Do not interpret \
  what it felt like.
- NEVER use superlatives (best, worst, greatest) unless the data explicitly supports them.
- NEVER add greetings, sign-offs, headers, or meta-commentary about being an AI.
- NEVER attribute franchise history from before the current owner's tenure to \
  the current team name. The FRANCHISE TENURE section shows when each team name \
  started. For records that predate the current owner, say "this franchise" or \
  "this roster slot" — not the current team name.
- Output ONLY the recap prose — nothing else.
- NEVER inject NFL news, injury reports, or real-world football events not present in the data.
- When the SEASON CONTEXT says "WEEK TYPE: PLAYOFF", this is a PLAYOFF week. \
  Do NOT reference it as regular season. Do NOT discuss eliminated teams' records \
  as if they are still playing. Do NOT say "regular season title" — say \
  "championship" or the appropriate playoff round. Teams not in this week's \
  matchups have been eliminated. Focus only on the teams playing.
- NEVER invent player scores or individual performances not present in the \
  PLAYER HIGHLIGHTS data. If player data is not available for a week, do not \
  fabricate it.
- NEVER use the phrase "the kind of chaos that makes fantasy football beautiful" \
  or any variation of it. This phrase is permanently banned.
- NEVER attribute a NARRATIVE ANGLE to a franchise other than the one named in \
  the angle. Each angle has a [RE: franchise] tag identifying which team it \
  applies to. If an angle says "[RE: Eddie & the Cruisers] Eddie is 15-9 in \
  close games," that stat belongs to Eddie ONLY — do not apply it to Ben, Pat, \
  or any other team, even if that other team also played a close game this week.\
"""

# ---------------------------------------------------------------------------
# EAL directive -> creative guidance mapping
# ---------------------------------------------------------------------------

_EAL_GUIDANCE = {
    "HIGH_CONFIDENCE_ALLOWED": (
        "Full voice. Callbacks, historical context, and running observations all permitted. "
        "This is a high-confidence week — the data is rich and the storylines are clear. "
        "Write like you've been watching this league for years."
    ),
    "MODERATE_CONFIDENCE_ONLY": (
        "Standard commentary. Observations grounded in the provided context. "
        "Stay close to what the numbers show. Moderate the ambition — "
        "this week's data is solid but not exceptional."
    ),
    "LOW_CONFIDENCE_RESTRAINT": (
        "Minimal, restrained prose. State what happened, note one or two details. "
        "The data this week is thin. Say less, not more. "
        "Skip callbacks and historical references — just cover what happened. "
        "Two to three short paragraphs maximum."
    ),
}

# ---------------------------------------------------------------------------
# EAL -> temperature mapping (tighter constraint = lower temperature)
# ---------------------------------------------------------------------------

_EAL_TEMPERATURE = {
    "HIGH_CONFIDENCE_ALLOWED": 0.8,
    "MODERATE_CONFIDENCE_ONLY": 0.6,
    "LOW_CONFIDENCE_RESTRAINT": 0.3,
}


def _build_system_prompt(tone_preset: str = "", voice_profile: str = "") -> str:
    """Build the system prompt with optional tone preset and voice profile.

    The tone preset modifies the voice but never overrides the hard rules.
    The voice profile adds league-specific cultural guidance (commissioner-approved).
    Both are injected before hard rules — hard rules are always last to maximize
    compliance (models give higher weight to recency).
    """
    directives: list[str] = []

    # Tone preset directive (unless default POINTED)
    if tone_preset and tone_preset != "POINTED":
        from squadvault.core.tone.tone_profile_v1 import get_voice_directive
        directives.append(get_voice_directive(tone_preset))

    # Voice profile (commissioner-approved cultural guidance)
    if voice_profile:
        directives.append(voice_profile.strip())

    if not directives:
        return _SYSTEM_PROMPT

    combined = "\n\n".join(directives)
    _hr_marker = "\nHard rules (non-negotiable):"
    if _hr_marker in _SYSTEM_PROMPT:
        _voice, _hard = _SYSTEM_PROMPT.split(_hr_marker, 1)
        return _voice.rstrip() + "\n\n" + combined + _hr_marker + _hard
    return _SYSTEM_PROMPT.rstrip() + "\n\n" + combined + "\n"


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
    player_highlights: str = "",
    tone_preset: str = "",
    seasons_count: int = 0,
) -> str:
    """Build the user-turn prompt with full context feed.

    Deterministic given identical inputs (modulo context blocks which are
    themselves deterministic from the engine).
    """
    guidance = _EAL_GUIDANCE.get(
        eal_directive,
        "Use conservative tone. Stay close to the facts.",
    )

    parts: list[str] = []
    parts.append(f"League: {league_id} | Season: {season} | Week {week_index}")
    parts.append(f"EAL directive: {eal_directive} — {guidance}")
    parts.append("")

    # Context blocks — the engine's full feed
    if season_context:
        parts.append("=== SEASON CONTEXT (standings, streaks, scoring) ===")
        parts.append(season_context.strip())
        parts.append("")

    if league_history:
        parts.append("=== LEAGUE HISTORY (all-time records, cross-season — REFERENCE THIS) ===")
        parts.append("Use this data for context: all-time records, scoring records, streaks.")
        parts.append("When a score approaches a league record or a team's record is notable, mention it.")
        parts.append(league_history.strip())
        parts.append("")

    if narrative_angles:
        parts.append("=== NARRATIVE ANGLES (detected story hooks — USE THESE) ===")
        if seasons_count > 1:
            parts.append(f"IMPORTANT: The angles below are pre-computed from {seasons_count} seasons of data.")
        elif seasons_count == 1:
            parts.append("IMPORTANT: The angles below are pre-computed from this season's data only.")
        else:
            parts.append("IMPORTANT: The angles below are pre-computed from available league data.")
        parts.append("Work the HEADLINE and NOTABLE angles into your prose naturally.")
        parts.append("These are the hooks that make the recap feel historically informed.")
        parts.append(narrative_angles.strip())
        parts.append("")

    if writer_room_context:
        parts.append("=== WRITER ROOM (scoring deltas, FAAB spending) ===")
        parts.append(writer_room_context.strip())
        parts.append("")

    # Player highlights block — between WRITER ROOM and VERIFIED FACTS
    if player_highlights and player_highlights.strip():
        parts.append("=== PLAYER HIGHLIGHTS (individual player performances — USE THESE) ===")
        parts.append(player_highlights.strip())
        parts.append("")

    # Facts block — always present, always authoritative
    facts_block = "\n".join(f"- {b}" for b in facts_bullets) if facts_bullets else "(no facts)"
    parts.append("=== VERIFIED FACTS (canonical, authoritative — these are your source of truth) ===")
    parts.append(
        "WARNING: Do NOT count these bullets to produce aggregate numbers. "
        "Do NOT say a team made 'X moves' or 'Y acquisitions' — your count WILL be wrong. "
        "You may mention specific transactions by name but NEVER aggregate them into a count."
    )
    parts.append(facts_block)
    parts.append("")
    parts.append("Write the recap now.")

    return "\n".join(parts)


def _extract_text_from_response(message) -> str:
    """Extract text content from an API response.

    Returns the first text block from the response content.
    """
    if not message.content:
        return ""
    texts = []
    for block in message.content:
        if hasattr(block, "text") and block.text:
            texts.append(block.text.strip())
    return "\n\n".join(texts)


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
    player_highlights: str = "",
    tone_preset: str = "",
    voice_profile: str = "",
    seasons_count: int = 0,
) -> str | None:
    """Attempt to produce a governed prose narrative draft.

    Returns a narrative string if successful, or None if:
    - EAL directive is AMBIGUITY_PREFER_SILENCE
    - No facts bullets provided
    - ANTHROPIC_API_KEY not set
    - Any API error occurs

    Context parameters (all optional, additive):
    - season_context: rendered season standings/streaks/scoring text
    - league_history: rendered cross-season longitudinal context text
    - narrative_angles: rendered detected story hooks text
    - writer_room_context: rendered scoring deltas + FAAB spending text
    - player_highlights: rendered per-franchise player scoring context text

    Callers must treat None as 'use deterministic facts-only output.'
    This function never raises — all failures return None.
    """
    # EAL veto: silence preferred
    if eal_directive == EAL_AMBIGUITY_PREFER_SILENCE:
        logger.debug(
            "creative_layer_v1: EAL directive is AMBIGUITY_PREFER_SILENCE — "
            "skipping LLM call (silence preferred)."
        )
        return None

    # Unrecognised directive: conservative veto
    if eal_directive not in _PERMITTED_DIRECTIVES:
        logger.warning(
            "creative_layer_v1: unrecognised EAL directive %r — "
            "skipping LLM call (conservative fallback).",
            eal_directive,
        )
        return None

    # No facts: nothing to narrate
    if not facts_bullets:
        logger.debug(
            "creative_layer_v1: no facts bullets provided — skipping LLM call."
        )
        return None

    # No API key: silent fallback
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        warnings.warn(
            "creative_layer_v1: ANTHROPIC_API_KEY not set — "
            "falling back to deterministic facts-only output.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

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
        player_highlights=player_highlights,
        tone_preset=tone_preset,
        seasons_count=seasons_count,
    )

    # EAL-modulated temperature
    temperature = _EAL_TEMPERATURE.get(eal_directive, _TEMPERATURE)

    try:
        import anthropic  # local import: optional dependency

        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = _build_system_prompt(tone_preset, voice_profile=voice_profile)
        # SV_NO_WEB_SEARCH: Web search removed to prevent unverified NFL
        # commentary from being injected into league recaps. The creative
        # layer must work only with league-sourced data. Per governance:
        # silence over fabrication. Web search may be re-added later with
        # proper attribution and verification guardrails.
        message = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = _extract_text_from_response(message)
        if not text:
            logger.warning(
                "creative_layer_v1: API returned empty content — "
                "falling back to deterministic facts-only output."
            )
            return None

        return text

    except ImportError:
        warnings.warn(
            "creative_layer_v1: anthropic package not installed — "
            "falling back to deterministic facts-only output.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "creative_layer_v1: API call failed (%s) — "
            "falling back to deterministic facts-only output.",
            exc,
        )
        return None
