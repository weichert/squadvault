from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


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
    return s if s.endswith("\n") else s + "\n"


def render_rivalry_chronicle_v1(
    *,
    league_id: int,
    season: int,
    week_indices_requested: Sequence[int],
    upstream_quotes: Sequence[UpstreamRecapQuoteV1],
    missing_weeks: Sequence[int],
    created_at_utc: str,
) -> str:
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
