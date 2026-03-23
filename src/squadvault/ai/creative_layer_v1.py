"""Creative Layer v1 — governed LLM narrative drafting.

Contract (Creative Layer Contract Card v1.0):
- Facts are immutable inputs. This layer modifies expression only.
- Never introduces new facts, inferences, or interpretations.
- Returns a prose draft string or None (silence).
- Requires ANTHROPIC_API_KEY in environment; absent key -> None (silent fallback).
- temperature=0 for determinism.
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

_MODEL = "claude-haiku-4-5-20251001"

# EAL directives that permit narrative drafting
_PERMITTED_DIRECTIVES = {
    "HIGH_CONFIDENCE_ALLOWED",
    "MODERATE_CONFIDENCE_ONLY",
    "LOW_CONFIDENCE_RESTRAINT",
}

_SYSTEM_PROMPT = """\
You assist with fantasy football league recap narrative drafting.
You receive verified, deterministic facts about a single week of league activity.
Your only job is to write a brief narrative paragraph based strictly on those facts.

Rules (non-negotiable):
- Write 2-4 sentences only.
- Do not add scores, player names, team names, or events not listed in the facts.
- Do not speculate, infer intent, or make emotional claims not supported by the facts.
- Do not use superlatives (best, worst, greatest) unless a fact explicitly supports them.
- Do not add greetings, sign-offs, headers, or meta-commentary.
- Output only the narrative paragraph — nothing else.
"""

_EAL_GUIDANCE = {
    "HIGH_CONFIDENCE_ALLOWED": (
        "Standard tone permitted. You may write with normal confidence."
    ),
    "MODERATE_CONFIDENCE_ONLY": (
        "Use conservative tone. Avoid strong claims. Stay close to the facts."
    ),
    "LOW_CONFIDENCE_RESTRAINT": (
        "Minimal prose only. Stay as close to the facts as possible. "
        "One or two plain sentences maximum."
    ),
}


def _build_user_prompt(
    *,
    facts_bullets: list[str],
    eal_directive: str,
    league_id: str,
    season: int,
    week_index: int,
) -> str:
    """Build the user-turn prompt. Deterministic given identical inputs."""
    guidance = _EAL_GUIDANCE.get(
        eal_directive,
        "Use conservative tone. Stay close to the facts.",
    )
    facts_block = "\n".join(f"- {b}" for b in facts_bullets) if facts_bullets else "(no facts)"
    return (
        f"League: {league_id} | Season: {season} | Week: {week_index}\n"
        f"EAL directive: {eal_directive} — {guidance}\n\n"
        f"Verified facts for this week:\n{facts_block}\n\n"
        f"Write the narrative paragraph now."
    )


def draft_narrative_v1(
    *,
    facts_bullets: list[str],
    eal_directive: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[str]:
    """Attempt to produce a governed prose narrative draft.

    Returns a narrative string if successful, or None if:
    - EAL directive is AMBIGUITY_PREFER_SILENCE
    - No facts bullets provided
    - ANTHROPIC_API_KEY not set
    - Any API error occurs

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
    )

    try:
        import anthropic  # local import: optional dependency

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=_MODEL,
            max_tokens=512,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = message.content[0].text.strip() if message.content else ""
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
