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
from typing import Optional

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
You are the host of a late-night fantasy football desk segment. You've been \
following this specific league all season — you know the standings, the streaks, \
the history, and the storylines. You have opinions, and they're grounded in data.

Your job: write a weekly recap that makes league members want to share it. Think \
Colbert's sharper monologue moments or Fallon's desk bits, adapted for fantasy football.

Voice rules:
- Insider knowledge: use standings, streaks, and history to make observations. \
  "Three straight wins" means something different at 7-1 vs 3-5. Use that.
- Sharp but not mean: roasts are affectionate, never cruel. You're part of this league.
- Callbacks are REQUIRED when the data supports them. The NARRATIVE ANGLES and \
  LEAGUE HISTORY sections contain detected cross-season hooks — USE THEM. If a \
  team just set an all-time scoring record, SAY SO. If two rivals have met 12 \
  times before, REFERENCE the series record. If a streak approaches a league \
  record, CALL IT OUT. These callbacks are what make the recap feel like it \
  comes from someone who has watched this league for years, not just this week. \
  Only callback to things in the provided context — never invent history.
- Let big results speak: sometimes the score says it all. Don't over-narrate blowouts.
- NFL awareness: you may use general football knowledge (positions, team names, \
  typical fantasy value) but NEVER claim specific NFL news events (injuries, \
  suspensions, roster moves) unless that information is explicitly in the \
  provided context. When in doubt, describe what happened in the league without \
  speculating about why.
- Pacing: lead with the headline matchup(s), work through the week, land on a \
  forward-looking closer if the data supports it.
- Length: aim for 3-6 paragraphs depending on how much happened. A quiet week gets \
  a tighter recap. A blockbuster week earns more room.

Hard rules (non-negotiable):
- NEVER claim "all-time," "league history," or "league record" when the context \
  shows only one season of data. Use "this season" or "season record" instead. \
  If the data depth warning says single-season, take it seriously.
- NEVER invent facts, scores, player names, or events not in the provided data.
- NEVER speculate about manager intent, strategy, or emotions.
- NEVER use superlatives (best, worst, greatest) unless the data explicitly supports them.
- NEVER add greetings, sign-offs, headers, or meta-commentary about being an AI.
- Output ONLY the recap prose — nothing else.
- NEVER inject NFL news, injury reports, or real-world football events not present in the data.
"""

# ---------------------------------------------------------------------------
# EAL directive -> creative guidance mapping
# ---------------------------------------------------------------------------

_EAL_GUIDANCE = {
    "HIGH_CONFIDENCE_ALLOWED": (
        "Full voice. Callbacks, running observations, sharp commentary all permitted. "
        "This is a high-confidence week — the data is rich and the storylines are clear. "
        "Lean into the voice. Be the host who's been watching all season."
    ),
    "MODERATE_CONFIDENCE_ONLY": (
        "Standard commentary. Observations grounded in the provided context. "
        "Stay close to what the numbers show. Moderate the sharpness — "
        "this week's data is solid but not exceptional."
    ),
    "LOW_CONFIDENCE_RESTRAINT": (
        "Minimal, restrained prose. State what happened, note one or two details. "
        "The data this week is thin. Say less, not more. "
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


def _build_system_prompt(tone_preset: str = "") -> str:
    """Build the system prompt with optional tone preset directive.

    The tone preset modifies the voice but never overrides the hard rules.
    If no preset is provided, the base system prompt is used as-is (POINTED voice).
    """
    if not tone_preset or tone_preset == "POINTED":
        # POINTED is the default voice baked into the base system prompt
        return _SYSTEM_PROMPT

    from squadvault.core.tone.tone_profile_v1 import get_voice_directive
    directive = get_voice_directive(tone_preset)
    # Inject the tone directive between the voice rules and hard rules
    return _SYSTEM_PROMPT.rstrip() + "\n\n" + directive + "\n"


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
        parts.append("IMPORTANT: The angles below are pre-computed from 16 seasons of data.")
        parts.append("Work the HEADLINE and NOTABLE angles into your prose naturally.")
        parts.append("These are the hooks that make the recap feel historically informed.")
        parts.append(narrative_angles.strip())
        parts.append("")

    if writer_room_context:
        parts.append("=== WRITER ROOM (scoring deltas, FAAB spending) ===")
        parts.append(writer_room_context.strip())
        parts.append("")

    # Facts block — always present, always authoritative
    facts_block = "\n".join(f"- {b}" for b in facts_bullets) if facts_bullets else "(no facts)"
    parts.append("=== VERIFIED FACTS (canonical, authoritative — these are your source of truth) ===")
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
    tone_preset: str = "",
) -> Optional[str]:
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
        tone_preset=tone_preset,
    )

    # EAL-modulated temperature
    temperature = _EAL_TEMPERATURE.get(eal_directive, _TEMPERATURE)

    try:
        import anthropic  # local import: optional dependency

        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = _build_system_prompt(tone_preset)
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
