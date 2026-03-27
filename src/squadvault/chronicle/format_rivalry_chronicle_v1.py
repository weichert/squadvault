"""Format rivalry chronicle artifacts into rendered text.

When matchup facts and team names are provided, renders the contract-compliant
output structure (Header, Canonical Facts Block, Trace Block, Disclosures).

When only upstream quotes are provided (legacy path), renders the original
provenance-based format for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from squadvault.chronicle.matchup_facts_v1 import MatchupFactV1, facts_block_hash_v1


BANNER = (
    "NON-CANONICAL / DERIVED NARRATIVE — Rivalry Chronicle v1\n"
    "Derived strictly from APPROVED weekly recap artifacts. No new facts. No inference framed as fact.\n"
)

MARK_PROVENANCE = ("<!-- BEGIN_PROVENANCE -->", "<!-- END_PROVENANCE -->")
MARK_WEEKS = ("<!-- BEGIN_INCLUDED_WEEKS -->", "<!-- END_INCLUDED_WEEKS -->")
MARK_QUOTES = ("<!-- BEGIN_UPSTREAM_QUOTES -->", "<!-- END_UPSTREAM_QUOTES -->")


@dataclass(frozen=True)
class UpstreamRecapQuoteV1:
    week_index: int
    artifact_type: str
    version: int
    selection_fingerprint: str
    rendered_text: str  # verbatim upstream approved recap rendered text


def _nl(s: str) -> str:
    """Join lines with newline separator."""
    return s if s.endswith("\n") else s + "\n"


def render_rivalry_chronicle_contract_v1(
    *,
    league_id: int,
    season: int,
    team_a_id: str,
    team_b_id: str,
    team_a_name: str,
    team_b_name: str,
    week_indices_requested: Sequence[int],
    matchup_facts: Sequence[MatchupFactV1],
    missing_weeks: Sequence[int],
    created_at_utc: str,
    version: int = 1,
    narrative_prose: str | None = None,
) -> str:
    """Render contract-compliant rivalry chronicle output.

    Structure per contract card:
    - Header (artifact name, Team A vs Team B, scope, timestamp, version)
    - Canonical Facts Block (one entry per matchup)
    - Narrative Layer (optional)
    - Trace Block (event fingerprints, deterministic hash of fact block)
    - Disclosures (scope statement, missing data acknowledgment)
    """
    requested = sorted(set(int(w) for w in week_indices_requested))
    missing = sorted(set(int(w) for w in missing_weeks))
    facts = sorted(matchup_facts, key=lambda f: (f.season, f.week))

    lines: List[str] = []

    # ── Header ──
    lines.append(_nl("# Rivalry Chronicle v1"))
    lines.append(_nl(f"## {team_a_name} vs {team_b_name}"))
    lines.append(_nl(""))
    lines.append(_nl(f"League: {int(league_id)}"))
    lines.append(_nl(f"Season: {int(season)}"))
    lines.append(_nl(f"Scope: Weeks {min(requested)}-{max(requested)}"))
    lines.append(_nl(f"Generated: {created_at_utc}"))
    lines.append(_nl(f"Version: {version}"))
    lines.append(_nl(""))

    # ── Canonical Facts Block (Mandatory) ──
    lines.append(_nl("## Head-to-Head Results"))
    lines.append(_nl(""))
    if not facts:
        lines.append(_nl("No head-to-head matchups found in the requested scope."))
    else:
        for f in facts:
            if f.is_tie:
                lines.append(_nl(
                    f"- Season {f.season}, Week {f.week}: "
                    f"{f.winner_name} tied {f.loser_name} {f.winner_score}-{f.loser_score}"
                ))
            else:
                lines.append(_nl(
                    f"- Season {f.season}, Week {f.week}: "
                    f"{f.winner_name} def. {f.loser_name} {f.winner_score}-{f.loser_score}"
                ))
    lines.append(_nl(""))

    # ── Narrative Layer (Optional, Derived) ──
    if narrative_prose:
        lines.append(_nl("## Chronicle"))
        lines.append(_nl(""))
        lines.append(_nl(narrative_prose.rstrip()))
        lines.append(_nl(""))

    # ── Trace Block (Mandatory) ──
    lines.append(_nl("## Trace"))
    lines.append(_nl(""))
    lines.append(_nl(f"team_a_id: {team_a_id}"))
    lines.append(_nl(f"team_b_id: {team_b_id}"))
    lines.append(_nl(f"weeks_requested: {requested}"))
    lines.append(_nl(f"weeks_with_matchups: {[f.week for f in facts]}"))
    if facts:
        lines.append(_nl("canonical_event_fingerprints:"))
        for f in facts:
            lines.append(_nl(f"  - {f.canonical_event_fingerprint}"))
    lines.append(_nl(f"facts_block_hash: {facts_block_hash_v1(facts)}"))
    lines.append(_nl(""))

    # ── Disclosures ──
    lines.append(_nl("## Disclosures"))
    lines.append(_nl(""))
    lines.append(_nl(
        f"This chronicle covers head-to-head matchups between "
        f"{team_a_name} and {team_b_name} "
        f"for Season {season}, Weeks {min(requested)}-{max(requested)}."
    ))
    if missing:
        lines.append(_nl(
            f"Missing approved recap data for weeks: {missing}. "
            f"No gaps are filled; missing weeks are acknowledged."
        ))
    weeks_without_matchup = sorted(set(requested) - {f.week for f in facts} - set(missing))
    if weeks_without_matchup:
        lines.append(_nl(
            f"Weeks in scope where these teams did not face each other: {weeks_without_matchup}"
        ))
    lines.append(_nl(""))

    return "".join(lines)


def render_rivalry_chronicle_v1(
    *,
    league_id: int,
    season: int,
    week_indices_requested: Sequence[int],
    upstream_quotes: Sequence[UpstreamRecapQuoteV1],
    missing_weeks: Sequence[int],
    created_at_utc: str,
) -> str:
    """Render a rivalry chronicle artifact into formatted text (legacy format).

    Preserved for backward compatibility with existing tests.
    """
    requested = list(sorted(set(int(w) for w in week_indices_requested)))
    quotes = list(sorted(upstream_quotes, key=lambda q: int(q.week_index)))
    missing = list(sorted(set(int(w) for w in missing_weeks)))

    lines: List[str] = []
    lines.append(_nl(BANNER))
    lines.append(_nl(f"League: {int(league_id)}"))
    lines.append(_nl(f"Season: {int(season)}"))
    lines.append(_nl(f"CreatedAtUTC: {created_at_utc}"))
    lines.append("\n")

    lines.append(_nl(MARK_PROVENANCE[0]))
    lines.append(_nl(f"requested_weeks: {requested}"))
    lines.append(_nl(f"missing_weeks: {missing}"))
    lines.append(_nl(f"included_weeks: {[q.week_index for q in quotes]}"))
    lines.append(_nl("upstream:"))
    for q in quotes:
        lines.append(
            _nl(
                f"  - week_index: {q.week_index}  artifact_type: {q.artifact_type}  "
                f"version: {q.version}  selection_fingerprint: {q.selection_fingerprint}"
            )
        )
    lines.append(_nl(MARK_PROVENANCE[1]))
    lines.append("\n")

    lines.append(_nl(MARK_WEEKS[0]))
    if missing:
        lines.append(_nl("NOTE: Some requested weeks are missing APPROVED recaps. No gaps are filled."))
        lines.append(_nl(f"Missing weeks: {missing}"))
    else:
        lines.append(_nl("All requested weeks had APPROVED recaps."))
    lines.append(_nl(MARK_WEEKS[1]))
    lines.append("\n")

    lines.append(_nl(MARK_QUOTES[0]))
    for q in quotes:
        lines.append(_nl(f"## Week {q.week_index} — APPROVED WEEKLY_RECAP v{q.version}"))
        lines.append(_nl("```text"))
        lines.append(_nl((q.rendered_text or "").rstrip("\n")))
        lines.append(_nl("```"))
        lines.append("\n")
    lines.append(_nl(MARK_QUOTES[1]))

    return "".join(lines)
