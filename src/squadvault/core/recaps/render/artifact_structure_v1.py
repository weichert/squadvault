"""Canonical artifact structure (Unit 1.7b) — the spec section 3 model, parsed once.

Narrative Presentation Spec v1.0 (docs/Narrative_Presentation_Spec_v1_0.md) section 3. This module
parses an APPROVED recap artifact's rendered_text into the canonical structure exactly once, at the
derived/render layer, so every channel renderer is a pure function of the structure. It creates,
modifies, or re-derives NO fact: the narrative lede and the facts block are carried through
VERBATIM; nothing is read from the database here.

Reconciliation note (Gate 1, ratified 2026-07-04). Real approved artifacts carry a masthead
(synthesized), a narrative lede (the SHAREABLE RECAP prose), and a facts block ("What happened this
week:"). They do NOT carry discrete per-matchup SECTIONS, a separate transactions block, or a
standings note — those matchups are woven into the lede prose. Spec section 3 enumerates that fuller
structure as DORMANT CAPACITY the silence rule (section 3: "everything between appears only if the
approved artifact contains it") leaves absent; the parser therefore returns matchups=[],
transactions=None, standings_note=None for every current artifact. This is not loss — the absent
sections are legitimately absent, and the approved content (lede + facts block) round-trips exactly.

Masthead ruling (Gate 1 Q2). The masthead is emitted from artifact METADATA (league, season, week),
which is the artifact's own identity, NOT a factual claim re-derived from the database. Spec section
6 forbids re-deriving numbers/names/scores from data; carrying the artifact's own header identity is
structure, not content creation. This is the one place section 6 could be misread; it is not a
violation.
"""
from __future__ import annotations

from dataclasses import dataclass

from squadvault.core.exports.season_html_export_v1 import extract_shareable_parts
from squadvault.core.recaps.render.presentation_lint_v1 import render_transactions_block_v1

_SHARE_START = "--- SHAREABLE RECAP ---"
_FACTS_HEADER = "What happened this week:"


@dataclass(frozen=True)
class Masthead:
    """The artifact's own identity, from metadata — never re-derived from data (spec 6 / Q2)."""

    league_name: str
    season: int
    week_index: int


@dataclass(frozen=True)
class MatchupSection:
    """Dormant capacity (spec 3): a discrete per-matchup section. Absent in all current artifacts."""

    heading: str  # e.g. "Team A vs Team B — a-b"; drawn from structure if ever present, never re-derived
    body: str


@dataclass(frozen=True)
class ArtifactStructure:
    """The spec section 3 canonical structure of one approved weekly recap artifact."""

    masthead: Masthead                     # unconditional
    title: str | None                      # approved title block; None until artifacts carry one (Q2)
    narrative_lede: str                    # the approved creative prose (SHAREABLE RECAP), VERBATIM
    matchups: list[MatchupSection]         # dormant; [] for current artifacts (silence rule)
    transactions: str | None               # dormant; None (transactions live inside the facts block)
    standings_note: str | None             # dormant; None for current artifacts
    facts_block: str                       # deterministic facts block, byte-identical, rendered LAST


@dataclass(frozen=True)
class UnparseableArtifact:
    """A malformed artifact, surfaced not repaired (spec 6). Carries a human-readable reason and the
    raw text; NEVER a fabricated/reconstructed structure. The distribution and review paths refuse to
    emit a rendering for it and show the reason (P8b: surfacing must be human-readable, not a trace)."""

    reason: str
    raw_text: str


def parse_artifact(
    rendered_text: str,
    *,
    league_name: str,
    season: int,
    week_index: int,
) -> ArtifactStructure | UnparseableArtifact:
    """Parse an approved artifact's rendered_text into the canonical structure, or surface it.

    Pure: no DB, no clock, no network. league_name/season/week_index are the artifact's own metadata
    (supplied by the caller, which owns the lifecycle row), used only for the masthead. The lede and
    facts block are carried verbatim via the shared extractors (extract_shareable_parts +
    render_transactions_block_v1), so the facts block is byte-identical to the lifecycle emission and
    the L2 reference by construction.
    """
    if not rendered_text or _SHARE_START not in rendered_text:
        return UnparseableArtifact("no SHAREABLE RECAP narrative delimiter", rendered_text or "")

    narrative, bullets = extract_shareable_parts(rendered_text)
    if not narrative.strip():
        return UnparseableArtifact("empty narrative lede between SHAREABLE RECAP delimiters", rendered_text)
    if _FACTS_HEADER not in rendered_text or not bullets:
        return UnparseableArtifact("no facts block (missing 'What happened this week:' or bullets)", rendered_text)

    facts_block = render_transactions_block_v1(bullets, bullet_prefix="- ")
    return ArtifactStructure(
        masthead=Masthead(league_name=league_name, season=season, week_index=week_index),
        title=None,
        narrative_lede=narrative,
        matchups=[],
        transactions=None,
        standings_note=None,
        facts_block=facts_block,
    )
