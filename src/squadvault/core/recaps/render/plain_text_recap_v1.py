"""Plain-text / group-text recap renderer (Unit 1.7b) — the distributed artifact form.

Narrative Presentation Spec v1.0 section 4.1 (the operative distribution channel). A channel
rendering is a PURE FUNCTION of the canonical structure (artifact_structure_v1): masthead in caps,
the approved narrative lede verbatim, a single hyphen divider, then the deterministic facts block
last and byte-identical. No markup: the setext "=" underline of the pre-1.7b form (the W7 v27
markdown-in-group-text defect class, finding R5) is GONE — structure is carried by whitespace and
case only. Renderers never add, remove, reorder, or rephrase content, and never re-derive from data.

Pure: deterministic string assembly, no DB / network / clock. Used by the distribution path
(scripts/distribute_recap.py) AND the Office review surface (consumers/editorial_review_week.py) —
one shared renderer so what the reviewer approves is what ships (Gate 1 Fork A).
"""
from __future__ import annotations

from squadvault.core.recaps.render.artifact_structure_v1 import (
    ArtifactStructure,
    Masthead,
)
from squadvault.core.recaps.render.presentation_lint_v1 import (
    render_transactions_block_v1,
)


def render_masthead_line_v1(masthead: Masthead) -> str:
    """Spec 3 masthead: '<LEAGUE> — WEEK {n} — {season}' (all caps, em-dash separators).

    Emitted from the artifact's own metadata (Gate 1 Q2) — identity carried into the header, not a
    factual claim re-derived from data.
    """
    return f"{masthead.league_name.upper()} — WEEK {masthead.week_index} — {masthead.season}"


def render_structure_plain_text(structure: ArtifactStructure) -> str:
    """Render the canonical structure to the spec 4.1 plain-text form. Pure function of `structure`.

    Order (spec 3): masthead, [title], narrative lede, [matchups], [transactions], [standings],
    facts block LAST. Dormant sections (empty/None) are omitted entirely — no headers over nothing
    (silence rule). A single '----' hyphen divider sits between the narrative body and the facts
    block, nowhere else. No setext underline, no emoji, no manual wrapping. The facts block and the
    approved lede are carried through byte-for-byte.
    """
    parts: list[str] = [render_masthead_line_v1(structure.masthead), ""]
    if structure.title:
        parts.extend([structure.title, ""])
    parts.append(structure.narrative_lede)
    for m in structure.matchups:  # dormant; empty for current artifacts
        parts.extend(["", m.heading, "", m.body])
    if structure.transactions:
        parts.extend(["", structure.transactions])
    if structure.standings_note:
        parts.extend(["", structure.standings_note])
    if structure.facts_block:
        parts.extend(["", "----", "", structure.facts_block])
    return "\n".join(parts).rstrip() + "\n"


def render_plain_text_recap_v1(
    *,
    narrative: str,
    bullets: list[str],
    season: int,
    week_index: int,
    league_name: str = "PFL Buddies",
) -> str:
    """Adapter: build the canonical structure from (narrative, bullets) and render it (spec 4.1).

    Kept for callers that hold the extracted parts rather than a parsed structure; delegates to
    render_structure_plain_text so both entry points emit the identical spec-conformant form. The
    facts block is render_transactions_block_v1(bullets) — byte-identical to the lifecycle emission
    and the L2 reference by construction. Quiet weeks (no bullets) omit the facts block.
    """
    facts_block = render_transactions_block_v1(bullets, bullet_prefix="- ") if bullets else ""
    structure = ArtifactStructure(
        masthead=Masthead(league_name=league_name, season=season, week_index=week_index),
        title=None,
        narrative_lede=narrative,
        matchups=[],
        transactions=None,
        standings_note=None,
        facts_block=facts_block,
    )
    return render_structure_plain_text(structure)
