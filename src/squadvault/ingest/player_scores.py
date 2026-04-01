"""Derive canonical WEEKLY_PLAYER_SCORE events from MFL weeklyResults data.

The MFL weeklyResults endpoint includes per-player scoring and lineup
status for every franchise in every matchup. This module extracts those
player-level details and produces one event per rostered player per
franchise per week.

Per the Platform Adapter Contract Card (v1.0):
- Adapters produce event envelopes only — never write to canonical_events
- Re-ingestion with identical data must produce zero new events
- Missing data must remain missing — never infer, estimate, or fabricate
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _stable_external_id(*parts: str) -> str:
    """Generate a stable external ID for deduplication."""
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _safe_float(v: Any) -> float | None:
    """Parse a value to float, returning None on failure."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _ensure_list(v: Any) -> list[Any]:
    """MFL returns a single dict when there's one item, a list for many."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def derive_player_score_envelopes(
    *,
    year: int,
    week: int,
    league_id: str,
    weekly_results_json: dict[str, Any],
    source_url: str,
    occurred_at: str | None = None,
) -> list[dict[str, Any]]:
    """
    Produces canonical WEEKLY_PLAYER_SCORE event envelopes from MFL
    weeklyResults API response.

    MFL weeklyResults includes per-player data within each franchise:
    {
      "weeklyResults": {
        "week": "1",
        "matchup": [
          {
            "franchise": [
              {
                "id": "0001",
                "score": "142.60",
                "starters": "16582,13130,...",
                "player": [
                  {"id": "16582", "status": "starter", "score": "10.60",
                   "shouldStart": "0"},
                  {"id": "12345", "status": "nonstarter", "score": "15.00",
                   "shouldStart": "1"},
                  ...
                ]
              },
              ...
            ]
          },
          ...
        ]
      }
    }

    Creates one event per player per franchise per week (starters and
    bench) for any player with a parseable score.

    DEDUPE GUARANTEE:
    - external_id is based ONLY on stable MFL facts:
      league + season + week + franchise_id + player_id
    - Re-ingestion with same data produces no duplicates.
    """
    events: list[dict[str, Any]] = []

    results_root = weekly_results_json.get("weeklyResults", {})
    matchups = _ensure_list(results_root.get("matchup"))

    if not matchups:
        logger.info(
            "No matchups found for league=%s season=%s week=%s",
            league_id, year, week,
        )
        return events

    # Collect all player events across all matchups, keyed for sorting
    player_events: list[tuple[str, str, dict[str, Any]]] = []

    for matchup in matchups:
        franchises = _ensure_list(matchup.get("franchise"))

        for franchise in franchises:
            franchise_id = str(franchise.get("id", "")).strip()
            if not franchise_id:
                continue

            players = _ensure_list(franchise.get("player"))
            if not players:
                continue

            for player in players:
                player_id = str(player.get("id", "")).strip()
                if not player_id:
                    continue

                score = _safe_float(player.get("score"))
                if score is None:
                    # No score data — skip silently
                    continue

                status = str(player.get("status", "")).strip().lower()
                is_starter = status == "starter"

                # shouldStart indicates optimal lineup placement
                should_start_raw = str(player.get("shouldStart", "")).strip()
                should_start = should_start_raw == "1"

                external_id = _stable_external_id(
                    league_id,
                    str(year),
                    str(week),
                    franchise_id,
                    player_id,
                )

                raw_data = json.dumps(
                    {
                        "franchise_id": franchise_id,
                        "player_id": player_id,
                        "score": str(player.get("score", "")),
                        "status": status,
                        "shouldStart": should_start_raw,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )

                envelope = {
                    "event_type": "WEEKLY_PLAYER_SCORE",
                    "occurred_at": occurred_at,
                    "external_source": "MFL",
                    "external_id": external_id,
                    "league_id": league_id,
                    "season": year,
                    "payload": {
                        "week": week,
                        "franchise_id": franchise_id,
                        "player_id": player_id,
                        "score": score,
                        "is_starter": is_starter,
                        "should_start": should_start,
                        "source_url": source_url,
                        "raw_mfl_json": raw_data,
                    },
                }

                player_events.append((franchise_id, player_id, envelope))

    # Sort by franchise_id then player_id for deterministic output
    player_events.sort(key=lambda x: (x[0], x[1]))
    events = [e for _, _, e in player_events]

    return events
