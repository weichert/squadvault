"""Ingest NFL bye week data from MFL nflByeWeeks endpoint.

Parses the MFL nflByeWeeks API response and upserts into the
nfl_bye_weeks metadata table. One API call per season.

This is NFL calendar data, not league activity. It does not create
canonical events — it creates reference metadata used by Dimension 10
(Bye Week Impact) detectors.

MFL response shape:
  {"nflByeWeeks": {"year": "2024", "team": [
    {"id": "KCC", "bye_week": "6"},
    {"id": "PHI", "bye_week": "5"}, ...]}}
"""

from __future__ import annotations

import logging
from typing import Any

from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)


def parse_nfl_bye_weeks(
    raw_json: dict[str, Any],
) -> list[tuple[str, int]]:
    """Parse MFL nflByeWeeks response into (nfl_team, bye_week) tuples.

    Returns a sorted list of (team_id, bye_week_number) tuples.
    Silently skips malformed entries.
    """
    entries: list[tuple[str, int]] = []

    root = raw_json.get("nflByeWeeks", {})
    teams = root.get("team", [])

    # MFL returns a single dict if only one team, or a list
    if isinstance(teams, dict):
        teams = [teams]

    for team in teams:
        if not isinstance(team, dict):
            continue

        team_id = str(team.get("id", "")).strip()
        if not team_id:
            continue

        try:
            bye_week = int(team.get("bye_week", -1))
        except (ValueError, TypeError):
            continue

        if bye_week < 1:
            continue

        entries.append((team_id, bye_week))

    entries.sort(key=lambda e: (e[0], e[1]))
    return entries


def upsert_nfl_bye_weeks(
    db_path: str,
    league_id: str,
    season: int,
    bye_weeks: list[tuple[str, int]],
) -> int:
    """Upsert bye week data into nfl_bye_weeks table.

    Returns the number of rows upserted.
    Idempotent: re-ingesting the same season replaces existing data.
    """
    if not bye_weeks:
        return 0

    count = 0
    with DatabaseSession(db_path) as con:
        for nfl_team, bye_week in bye_weeks:
            con.execute(
                """INSERT OR REPLACE INTO nfl_bye_weeks
                   (league_id, season, nfl_team, bye_week)
                   VALUES (?, ?, ?, ?)""",
                (str(league_id), int(season), nfl_team, bye_week),
            )
            count += 1

    logger.info(
        "Upserted %d NFL bye week entries for league=%s season=%d",
        count, league_id, season,
    )
    return count


def ingest_nfl_bye_weeks_from_mfl(
    *,
    db_path: str,
    league_id: str,
    season: int,
    raw_json: dict[str, Any],
) -> int:
    """Full pipeline: parse MFL response and upsert into DB.

    Returns the number of rows upserted.
    """
    entries = parse_nfl_bye_weeks(raw_json)
    if not entries:
        logger.warning(
            "No bye week data parsed for league=%s season=%d", league_id, season,
        )
        return 0

    return upsert_nfl_bye_weeks(db_path, league_id, season, entries)
