"""Creative Layer v1 — Rivalry Chronicle narrative drafting.

Contract (Creative Layer Contract Card v1.0):
- Facts are immutable inputs. This layer modifies expression only.
- Never introduces new facts, inferences, or interpretations.
- Returns a prose draft string or None (silence).
- Requires ANTHROPIC_API_KEY in environment; absent key -> None (silent fallback).
- temperature=0 for determinism.
- AMBIGUITY_PREFER_SILENCE -> None (silence preferred, no API call made).
- Any API error -> None (silent fallback to deterministic facts-only text).

Rivalry Chronicle-specific:
- Light connective prose only (per contract card: "narrative restraint")
- Historical callbacks only if supported by facts
- No emotional attribution or motivation inference
- No superlatives, rankings, or trend claims

Human approval is a hard gate for all canonical artifacts. This layer
produces drafts only and has no authority over publication.
"""

from __future__ import annotations

import logging
import os
import warnings
from typing import Optional, Sequence

from squadvault.chronicle.matchup_facts_v1 import MatchupFactV1
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
You assist with fantasy football rivalry chronicle narrative drafting.
You receive verified head-to-head matchup results between two teams.
Your only job is to write brief connective prose summarizing their competitive history.

Rules (non-negotiable):
- Write 2-5 sentences only.
- Base every claim strictly on the matchup facts provided.
- Do not add scores, names, or events not listed in the facts.
- Do not speculate, infer strategy, attribute emotion, or claim motivation.
- Do not use superlatives (best, worst, greatest, dominant) unless the record supports them factually.
- Do not claim trends, momentum, or predictions.
- Do not add greetings, sign-offs, headers, or meta-commentary.
- If the record is sparse (1-2 matchups), keep it to 1-2 sentences.
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
        "Minimal prose only. One or two plain sentences. "
        "Stay as close to the matchup results as possible."
    ),
}


def _eal_directive_for_rivalry(matchup_count: int) -> str:
    """Compute EAL directive for rivalry chronicle based on matchup count.

    Rivalry chronicles use a conservative default: the narrative layer
    is optional and should practice restraint.
    """
    if matchup_count == 0:
        return EAL_AMBIGUITY_PREFER_SILENCE
    if matchup_count == 1:
        return "LOW_CONFIDENCE_RESTRAINT"
    if matchup_count <= 3:
        return "MODERATE_CONFIDENCE_ONLY"
    return "MODERATE_CONFIDENCE_ONLY"


def _build_user_prompt(
    *,
    facts: Sequence[MatchupFactV1],
    eal_directive: str,
    team_a_name: str,
    team_b_name: str,
    league_id: int,
    season: int,
) -> str:
    """Build the user-turn prompt. Deterministic given identical inputs."""
    guidance = _EAL_GUIDANCE.get(
        eal_directive,
        "Use conservative tone. Stay close to the facts.",
    )

    facts_lines = []
    for f in facts:
        if f.is_tie:
            facts_lines.append(
                f"- Season {f.season}, Week {f.week}: "
                f"{f.winner_name} tied {f.loser_name} {f.winner_score}-{f.loser_score}"
            )
        else:
            facts_lines.append(
                f"- Season {f.season}, Week {f.week}: "
                f"{f.winner_name} defeated {f.loser_name} {f.winner_score}-{f.loser_score}"
            )

    facts_block = "\n".join(facts_lines) if facts_lines else "(no matchups)"

    # Compute simple record for context
    a_wins = sum(1 for f in facts if not f.is_tie and f.winner_name == team_a_name)
    b_wins = sum(1 for f in facts if not f.is_tie and f.winner_name == team_b_name)
    ties = sum(1 for f in facts if f.is_tie)
    record_line = f"Overall record: {team_a_name} {a_wins}-{b_wins}"
    if ties:
        record_line += f"-{ties}"
    record_line += f" {team_b_name}"

    return (
        f"League: {league_id} | Season: {season}\n"
        f"Rivalry: {team_a_name} vs {team_b_name}\n"
        f"EAL directive: {eal_directive} — {guidance}\n\n"
        f"Head-to-head matchup results:\n{facts_block}\n\n"
        f"{record_line}\n\n"
        f"Write the rivalry chronicle narrative paragraph now."
    )


def draft_rivalry_narrative_v1(
    *,
    matchup_facts: Sequence[MatchupFactV1],
    team_a_name: str,
    team_b_name: str,
    league_id: int,
    season: int,
    eal_directive: str | None = None,
) -> Optional[str]:
    """Attempt to produce governed narrative prose for a rivalry chronicle.

    Returns a narrative string if successful, or None if:
    - EAL directive is AMBIGUITY_PREFER_SILENCE
    - No matchup facts provided
    - ANTHROPIC_API_KEY not set
    - Any API error occurs

    Callers must treat None as 'use facts-only output.'
    This function never raises — all failures return None.
    """
    # Auto-compute EAL directive if not provided
    if eal_directive is None:
        eal_directive = _eal_directive_for_rivalry(len(matchup_facts))

    # EAL veto: silence preferred
    if eal_directive == EAL_AMBIGUITY_PREFER_SILENCE:
        logger.debug(
            "creative_layer_rivalry_v1: EAL directive is AMBIGUITY_PREFER_SILENCE — "
            "skipping LLM call (silence preferred)."
        )
        return None

    # Unrecognised directive: conservative veto
    if eal_directive not in _PERMITTED_DIRECTIVES:
        logger.warning(
            "creative_layer_rivalry_v1: unrecognised EAL directive %r — "
            "skipping LLM call (conservative fallback).",
            eal_directive,
        )
        return None

    # No facts: nothing to narrate
    if not matchup_facts:
        logger.debug(
            "creative_layer_rivalry_v1: no matchup facts provided — skipping LLM call."
        )
        return None

    # No API key: silent fallback
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        warnings.warn(
            "creative_layer_rivalry_v1: ANTHROPIC_API_KEY not set — "
            "falling back to facts-only output.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

    user_prompt = _build_user_prompt(
        facts=matchup_facts,
        eal_directive=eal_directive,
        team_a_name=team_a_name,
        team_b_name=team_b_name,
        league_id=league_id,
        season=season,
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

        block = message.content[0] if message.content else None
        text = block.text.strip() if block and hasattr(block, "text") else ""
        if not text:
            logger.warning(
                "creative_layer_rivalry_v1: API returned empty content — "
                "falling back to facts-only output."
            )
            return None

        return text

    except ImportError:
        warnings.warn(
            "creative_layer_rivalry_v1: anthropic package not installed — "
            "falling back to facts-only output.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "creative_layer_rivalry_v1: API call failed (%s) — "
            "falling back to facts-only output.",
            exc,
        )
        return None
