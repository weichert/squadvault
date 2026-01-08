# src/squadvault/recaps/preflight.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Sequence

from .dng_reasons import DNGReason


class PreflightVerdictType(str, Enum):
    GENERATE_OK = "GENERATE_OK"
    DO_NOT_GENERATE = "DO_NOT_GENERATE"


@dataclass(frozen=True)
class PreflightVerdict:
    verdict: PreflightVerdictType
    reason_code: Optional[DNGReason] = None
    evidence: dict[str, Any] = None

    def __post_init__(self):
        # dataclasses + frozen: use object.__setattr__
        if self.evidence is None:
            object.__setattr__(self, "evidence", {})


def recap_preflight_verdict(
    *,
    league_id: str,
    season: int,
    week: int,
    canonical_events: Sequence[Any],
) -> PreflightVerdict:
    """
    Preflight gate: decides if recap generation is allowed.
    Must run BEFORE any prompt assembly or LLM call.
    """

    # HARD CHECK #1 (the only one you implement right now):
    # If there are no canonical events, we cannot generate without fabricating.
    if not canonical_events:
        return PreflightVerdict(
            verdict=PreflightVerdictType.DO_NOT_GENERATE,
            reason_code=DNGReason.DNG_INCOMPLETE_WEEK,
            evidence={
                "league_id": league_id,
                "season": season,
                "week": week,
                "canonical_event_count": 0,
            },
        )

    return PreflightVerdict(
        verdict=PreflightVerdictType.GENERATE_OK,
        evidence={
            "league_id": league_id,
            "season": season,
            "week": week,
            "canonical_event_count": len(canonical_events),
        },
    )

