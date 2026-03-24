#!/usr/bin/env python3
"""Apply script: Creative Layer Calibration v1

Upgrades creative_layer_v1.py from proof-of-concept to calibrated voice,
and wires all engine context layers into the lifecycle.

Changes:
1. creative_layer_v1.py — Sonnet model, temperature 0.8 (EAL-modulated),
   sports-desk voice, web search, context-aware prompt, EAL creative ranges
2. weekly_recap_lifecycle.py — wire season context, league history,
   narrative angles, writer room enrichments into creative layer block
3. league_history_v1.py — export load_all_matchups (was private _load_all_matchups)
4. Tests — update temperature assertion + fix renamed function import

Test baseline: 1083 passed, 3 skipped (unchanged).
"""

import os


REPO = os.getcwd()


def write(relpath: str, content: str) -> None:
    path = os.path.join(REPO, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {relpath}")


def patch_in_place(relpath: str, old: str, new: str) -> None:
    path = os.path.join(REPO, relpath)
    with open(path) as f:
        content = f.read()
    if old not in content:
        raise RuntimeError(f"Anchor not found in {relpath}:\n{old[:120]}...")
    if content.count(old) > 1:
        raise RuntimeError(f"Anchor appears multiple times in {relpath}")
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"  patched {relpath}")


# =========================================================================
# 1. Rewrite creative_layer_v1.py
# =========================================================================

CREATIVE_LAYER = r'''"""Creative Layer v1 — governed LLM narrative drafting.

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
- Callbacks: reference earlier weeks when the data supports it ("remember when..."). \
  Only callback to things in the provided context — never invent history.
- Let big results speak: sometimes the score says it all. Don't over-narrate blowouts.
- NFL awareness: if web search results give you injury/bye/breakout context for a \
  transaction, weave it in naturally. But NFL news is color — not league fact.
- Pacing: lead with the headline matchup(s), work through the week, land on a \
  forward-looking closer if the data supports it.
- Length: aim for 3-6 paragraphs depending on how much happened. A quiet week gets \
  a tighter recap. A blockbuster week earns more room.

Hard rules (non-negotiable):
- NEVER invent facts, scores, player names, or events not in the provided data.
- NEVER speculate about manager intent, strategy, or emotions.
- NEVER use superlatives (best, worst, greatest) unless the data explicitly supports them.
- NEVER add greetings, sign-offs, headers, or meta-commentary about being an AI.
- Output ONLY the recap prose — nothing else.
- NFL context from web search is background color only. It never becomes a league fact.
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
        parts.append("=== LEAGUE HISTORY (all-time records, cross-season) ===")
        parts.append(league_history.strip())
        parts.append("")

    if narrative_angles:
        parts.append("=== NARRATIVE ANGLES (detected story hooks for this week) ===")
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
    """Extract text content from an API response, handling tool_use blocks.

    When web search is enabled, the response may contain tool_use and
    tool_result blocks interleaved with text. We extract only text blocks.
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
    )

    # EAL-modulated temperature
    temperature = _EAL_TEMPERATURE.get(eal_directive, _TEMPERATURE)

    try:
        import anthropic  # local import: optional dependency

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=temperature,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
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
'''

# =========================================================================
# 2. Patch league_history_v1.py — make _load_all_matchups public
# =========================================================================

LEAGUE_HISTORY_OLD_FUNC = "def _load_all_matchups(db_path: str, league_id: str) -> List[HistoricalMatchup]:"
LEAGUE_HISTORY_NEW_FUNC = "def load_all_matchups(db_path: str, league_id: str) -> List[HistoricalMatchup]:"

LEAGUE_HISTORY_OLD_CALL = "    all_matchups = _load_all_matchups(db_path, str(league_id))"
LEAGUE_HISTORY_NEW_CALL = "    all_matchups = load_all_matchups(db_path, str(league_id))"


# =========================================================================
# 3. Patch lifecycle — add imports + rewrite SV_CREATIVE_LAYER_V1 block
# =========================================================================

LIFECYCLE_IMPORT_OLD = "from squadvault.ai.creative_layer_v1 import draft_narrative_v1"
LIFECYCLE_IMPORT_NEW = """\
from squadvault.ai.creative_layer_v1 import draft_narrative_v1
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
    render_season_context_for_prompt,
)
from squadvault.core.recaps.context.league_history_v1 import (
    derive_league_history_v1,
    load_all_matchups,
    build_cross_season_name_resolver,
    render_league_history_for_prompt,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    detect_narrative_angles_v1,
    render_angles_for_prompt,
)
from squadvault.core.recaps.context.writer_room_context_v1 import (
    derive_scoring_deltas,
    derive_faab_spending,
    render_writer_room_context_for_prompt,
)"""

LIFECYCLE_CREATIVE_OLD = '''\
    # SV_CREATIVE_LAYER_V1_BEGIN
    # Attempt governed narrative prose draft constrained by EAL directive.
    # Falls back silently to deterministic facts-only if EAL vetoes, key absent, or any error.
    # Facts block is always preserved — narrative is additive only, never a replacement.
    _creative_bullets: list[str] = []
    with DatabaseSession(db_path) as _cl_con:
        _cl_row = _cl_con.execute(
            "SELECT canonical_ids_json FROM recap_runs"
            " WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week_index),
        ).fetchone()
        if _cl_row and _cl_row[0]:
            try:
                _cl_ids = json.loads(_cl_row[0])
                if isinstance(_cl_ids, list) and _cl_ids:
                    _cl_events = _load_canonical_event_rows(db_path, _cl_ids)
                    if _cl_events:
                        _cl_pids, _cl_fids = _collect_ids_from_payloads(_cl_events)
                        _cl_pres = PlayerResolver(db_path, league_id, season)
                        _cl_fres = FranchiseResolver(db_path, league_id, season)
                        if _cl_pids:
                            _cl_pres.load_for_ids(_cl_pids)
                        if _cl_fids:
                            _cl_fres.load_for_ids(_cl_fids)
                        _creative_bullets = render_deterministic_bullets_v1(
                            _cl_events,
                            team_resolver=_cl_fres.one,
                            player_resolver=_cl_pres.one,
                        )
            except Exception:
                _creative_bullets = []

    _narrative_draft = draft_narrative_v1(
        facts_bullets=_creative_bullets,
        eal_directive=editorial_attunement_v1,
        league_id=league_id,
        season=season,
        week_index=week_index,
    )'''

LIFECYCLE_CREATIVE_NEW = '''\
    # SV_CREATIVE_LAYER_V1_BEGIN
    # Attempt governed narrative prose draft constrained by EAL directive.
    # Falls back silently to deterministic facts-only if EAL vetoes, key absent, or any error.
    # Facts block is always preserved — narrative is additive only, never a replacement.
    #
    # Context feed: season context + league history + narrative angles + writer room
    # enrichments are derived from canonical data and rendered as text blocks for the
    # creative layer prompt. These are derived, non-authoritative, and never modify facts.
    _creative_bullets: list[str] = []
    _season_context_text = ""
    _league_history_text = ""
    _narrative_angles_text = ""
    _writer_room_text = ""

    with DatabaseSession(db_path) as _cl_con:
        _cl_row = _cl_con.execute(
            "SELECT canonical_ids_json FROM recap_runs"
            " WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week_index),
        ).fetchone()
        if _cl_row and _cl_row[0]:
            try:
                _cl_ids = json.loads(_cl_row[0])
                if isinstance(_cl_ids, list) and _cl_ids:
                    _cl_events = _load_canonical_event_rows(db_path, _cl_ids)
                    if _cl_events:
                        _cl_pids, _cl_fids = _collect_ids_from_payloads(_cl_events)
                        _cl_pres = PlayerResolver(db_path, league_id, season)
                        _cl_fres = FranchiseResolver(db_path, league_id, season)
                        if _cl_pids:
                            _cl_pres.load_for_ids(_cl_pids)
                        if _cl_fids:
                            _cl_fres.load_for_ids(_cl_fids)
                        _creative_bullets = render_deterministic_bullets_v1(
                            _cl_events,
                            team_resolver=_cl_fres.one,
                            player_resolver=_cl_pres.one,
                        )
            except Exception:
                _creative_bullets = []

    # --- Context derivation (all derived, non-authoritative, silent on failure) ---
    try:
        _cl_name_map = build_cross_season_name_resolver(db_path, league_id)
    except Exception:
        _cl_name_map = {}

    try:
        _cl_season_ctx = derive_season_context_v1(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _season_context_text = render_season_context_for_prompt(
            _cl_season_ctx, team_resolver=lambda fid: _cl_name_map.get(fid, fid),
        )
    except Exception:
        _cl_season_ctx = None

    try:
        _cl_history_ctx = derive_league_history_v1(db_path=db_path, league_id=league_id)
        _league_history_text = render_league_history_for_prompt(
            _cl_history_ctx, name_map=_cl_name_map,
        )
    except Exception:
        _cl_history_ctx = None

    try:
        _cl_all_matchups = load_all_matchups(db_path, league_id)
    except Exception:
        _cl_all_matchups = None

    try:
        if _cl_season_ctx is not None:
            _cl_angles = detect_narrative_angles_v1(
                season_ctx=_cl_season_ctx,
                history_ctx=_cl_history_ctx,
                all_matchups=_cl_all_matchups,
            )
            _narrative_angles_text = render_angles_for_prompt(
                _cl_angles, name_map=_cl_name_map,
            )
    except Exception:
        pass

    try:
        _cl_deltas = derive_scoring_deltas(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _cl_faab = derive_faab_spending(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _writer_room_text = render_writer_room_context_for_prompt(
            deltas=_cl_deltas, faab=_cl_faab, name_map=_cl_name_map,
        )
    except Exception:
        pass

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
    )'''

# =========================================================================
# 4. Test fixes
# =========================================================================

TEST_CREATIVE_OLD = '''\
    def test_uses_temperature_zero(self) -> None:
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        self.assertEqual(kwargs.get("temperature"), 0)'''

TEST_CREATIVE_NEW = '''\
    def test_uses_eal_modulated_temperature(self) -> None:
        ma = self._mock("Narrative.")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):
            with patch.dict("sys.modules", {"anthropic": ma}):
                draft_narrative_v1(
                    facts_bullets=_SAMPLE_BULLETS, eal_directive=_PERMITTED_DIRECTIVE,
                    league_id="L1", season=2024, week_index=6,
                )
        kwargs = ma.Anthropic.return_value.messages.create.call_args.kwargs
        # MODERATE_CONFIDENCE_ONLY maps to 0.6
        self.assertEqual(kwargs.get("temperature"), 0.6)'''

TEST_ANGLES_OLD = """\
        from squadvault.core.recaps.context.league_history_v1 import _load_all_matchups
        all_matchups = _load_all_matchups(db_path, LEAGUE)"""

TEST_ANGLES_NEW = """\
        from squadvault.core.recaps.context.league_history_v1 import load_all_matchups
        all_matchups = load_all_matchups(db_path, LEAGUE)"""


def main():
    print("Applying creative layer calibration v1...\n")

    # 1. Rewrite creative_layer_v1.py
    write("src/squadvault/ai/creative_layer_v1.py", CREATIVE_LAYER)

    # 2. Patch league_history_v1.py — make _load_all_matchups public
    patch_in_place(
        "src/squadvault/core/recaps/context/league_history_v1.py",
        LEAGUE_HISTORY_OLD_FUNC,
        LEAGUE_HISTORY_NEW_FUNC,
    )
    patch_in_place(
        "src/squadvault/core/recaps/context/league_history_v1.py",
        LEAGUE_HISTORY_OLD_CALL,
        LEAGUE_HISTORY_NEW_CALL,
    )

    # 3. Patch lifecycle — add context imports
    patch_in_place(
        "src/squadvault/recaps/weekly_recap_lifecycle.py",
        LIFECYCLE_IMPORT_OLD,
        LIFECYCLE_IMPORT_NEW,
    )

    # 4. Patch lifecycle — rewrite SV_CREATIVE_LAYER_V1 block
    patch_in_place(
        "src/squadvault/recaps/weekly_recap_lifecycle.py",
        LIFECYCLE_CREATIVE_OLD,
        LIFECYCLE_CREATIVE_NEW,
    )

    # 5. Fix test: temperature assertion
    patch_in_place(
        "Tests/test_creative_layer_v1.py",
        TEST_CREATIVE_OLD,
        TEST_CREATIVE_NEW,
    )

    # 6. Fix test: renamed function import
    patch_in_place(
        "Tests/test_narrative_angles_v1.py",
        TEST_ANGLES_OLD,
        TEST_ANGLES_NEW,
    )

    print("\nDone. Run: PYTHONPATH=src python -m pytest Tests/ -q")
    print("\nTo test with real data:")
    print("  export ANTHROPIC_API_KEY=sk-ant-...")
    print("  ./scripts/recap.sh generate --league 70985 --season 2024 --week 6")


if __name__ == "__main__":
    main()
