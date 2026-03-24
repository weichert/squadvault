"""Derive canonical WEEKLY_MATCHUP_RESULT events from MFL weeklyResults data."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _stable_external_id(*parts: str) -> str:
    """Generate a stable external ID for deduplication."""
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _safe_float(v: Any) -> Optional[float]:
    """Parse a value to float, returning None on failure."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _ensure_list(v: Any) -> List[Any]:
    """MFL returns a single dict when there's one item, a list for many."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def derive_matchup_result_envelopes(
    *,
    year: int,
    week: int,
    league_id: str,
    weekly_results_json: Dict[str, Any],
    source_url: str,
    occurred_at: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Produces canonical WEEKLY_MATCHUP_RESULT event envelopes from MFL
    weeklyResults API response.

    MFL weeklyResults JSON shape:
    {
      "weeklyResults": {
        "week": "6",
        "matchup": [
          {
            "franchise": [
              {"id": "0001", "score": "142.60", "result": "W"},
              {"id": "0002", "score": "98.30", "result": "L"}
            ]
          },
          ...
        ]
      }
    }

    DEDUPE GUARANTEE:
    - external_id is based ONLY on stable MFL facts:
      league + season + week + sorted franchise IDs
    - Re-ingestion with same data produces no duplicates.
    """
    events: List[Dict[str, Any]] = []

    results_root = weekly_results_json.get("weeklyResults", {})
    matchups = _ensure_list(results_root.get("matchup"))

    if not matchups:
        logger.info(
            "No matchups found for league=%s season=%s week=%s",
            league_id, year, week,
        )
        return events

    for matchup in matchups:
        franchises = _ensure_list(matchup.get("franchise"))

        if len(franchises) != 2:
            logger.warning(
                "Skipping matchup with %d franchises (expected 2) in week %s",
                len(franchises), week,
            )
            continue

        f1, f2 = franchises[0], franchises[1]
        f1_id = str(f1.get("id", "")).strip()
        f2_id = str(f2.get("id", "")).strip()
        f1_score = _safe_float(f1.get("score"))
        f2_score = _safe_float(f2.get("score"))
        f1_result = str(f1.get("result", "")).strip().upper()
        f2_result = str(f2.get("result", "")).strip().upper()

        if not f1_id or not f2_id:
            logger.warning("Skipping matchup with missing franchise IDs in week %s", week)
            continue

        if f1_score is None or f2_score is None:
            logger.warning(
                "Skipping matchup %s vs %s with missing scores in week %s",
                f1_id, f2_id, week,
            )
            continue

        # Determine winner/loser
        is_tie = False
        if f1_result == "W":
            winner_id, loser_id = f1_id, f2_id
            winner_score, loser_score = f1_score, f2_score
        elif f2_result == "W":
            winner_id, loser_id = f2_id, f1_id
            winner_score, loser_score = f2_score, f1_score
        elif f1_result == "T" or f2_result == "T" or f1_score == f2_score:
            # Tie: use lower franchise ID as "home" (deterministic)
            is_tie = True
            if f1_id < f2_id:
                winner_id, loser_id = f1_id, f2_id
                winner_score, loser_score = f1_score, f2_score
            else:
                winner_id, loser_id = f2_id, f1_id
                winner_score, loser_score = f2_score, f1_score
        else:
            # Fallback: determine by score
            if f1_score > f2_score:
                winner_id, loser_id = f1_id, f2_id
                winner_score, loser_score = f1_score, f2_score
            elif f2_score > f1_score:
                winner_id, loser_id = f2_id, f1_id
                winner_score, loser_score = f2_score, f1_score
            else:
                is_tie = True
                if f1_id < f2_id:
                    winner_id, loser_id = f1_id, f2_id
                    winner_score, loser_score = f1_score, f2_score
                else:
                    winner_id, loser_id = f2_id, f1_id
                    winner_score, loser_score = f2_score, f1_score

        # Stable external ID: sorted franchise IDs for determinism
        sorted_ids = sorted([f1_id, f2_id])
        external_id = _stable_external_id(
            league_id,
            str(year),
            str(week),
            sorted_ids[0],
            sorted_ids[1],
        )

        # Format scores consistently (strip trailing zeros but keep one decimal)
        def _fmt_score(s: float) -> str:
            # MFL scores are typically 2 decimal places
            return f"{s:.2f}"

        raw_matchup_json = json.dumps(matchup, separators=(",", ":"), sort_keys=True)

        events.append(
            {
                "event_type": "WEEKLY_MATCHUP_RESULT",
                "occurred_at": occurred_at,  # From lock timestamp; None if unavailable
                "external_source": "MFL",
                "external_id": external_id,
                "league_id": league_id,
                "season": year,
                "payload": {
                    "week": week,
                    "winner_franchise_id": winner_id,
                    "loser_franchise_id": loser_id,
                    "winner_score": _fmt_score(winner_score),
                    "loser_score": _fmt_score(loser_score),
                    "is_tie": is_tie,
                    "home_franchise_id": f1_id,
                    "away_franchise_id": f2_id,
                    "home_score": _fmt_score(f1_score),
                    "away_score": _fmt_score(f2_score),
                    "source_url": source_url,
                    "raw_mfl_json": raw_matchup_json,
                },
            }
        )

    return events
