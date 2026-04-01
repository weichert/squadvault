"""Preflight gate: decide if recap generation is allowed before LLM calls."""

# src/squadvault/recaps/preflight.py
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .dng_reasons import DNGReason


class PreflightVerdictType(str, Enum):
    GENERATE_OK = "GENERATE_OK"
    DO_NOT_GENERATE = "DO_NOT_GENERATE"


@dataclass(frozen=True)
class PreflightVerdict:
    verdict: PreflightVerdictType
    reason_code: DNGReason | None = None
    evidence: dict[str, Any] | None = None

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


def check_duplicate_matchup_week(
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> PreflightVerdict | None:
    """Detect weeks where all matchup results are identical to the prior week.

    MFL sometimes duplicates championship results into multiple week slots.
    When every matchup in week N is identical (same teams, same scores) to
    week N-1, the week is a platform artifact, not a real game.

    Returns a DNG verdict if duplicate detected, None otherwise.
    Requires week >= 2 (week 1 has no prior week to compare).
    """
    if week < 2:
        return None

    import sqlite3

    from squadvault.core.storage.session import DatabaseSession

    def _matchup_fingerprints(con: sqlite3.Connection, w: int) -> set[str]:
        """Return a set of 'winner|score|loser|score' strings for a week."""
        rows = con.execute(
            "SELECT "
            "  json_extract(payload_json, '$.winner_franchise_id'),"
            "  json_extract(payload_json, '$.winner_score'),"
            "  json_extract(payload_json, '$.loser_franchise_id'),"
            "  json_extract(payload_json, '$.loser_score')"
            " FROM v_canonical_best_events"
            " WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
            "   AND CAST(json_extract(payload_json, '$.week') AS INTEGER) = ?",
            (league_id, season, w),
        ).fetchall()
        return {f"{r[0]}|{r[1]}|{r[2]}|{r[3]}" for r in rows}

    try:
        with DatabaseSession(db_path) as con:
            current = _matchup_fingerprints(con, week)
            prior = _matchup_fingerprints(con, week - 1)

            if current and prior and current == prior:
                return PreflightVerdict(
                    verdict=PreflightVerdictType.DO_NOT_GENERATE,
                    reason_code=DNGReason.DNG_DUPLICATE_MATCHUP_WEEK,
                    evidence={
                        "league_id": league_id,
                        "season": season,
                        "week": week,
                        "prior_week": week - 1,
                        "matchup_count": len(current),
                        "detail": (
                            f"All {len(current)} matchup(s) in week {week} are identical "
                            f"to week {week - 1} (MFL platform duplicate)"
                        ),
                    },
                )
    except Exception:
        pass  # Best-effort; default to allowing generation

    return None

