"""Query head-to-head matchup facts from canonical events for rivalry chronicles."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from squadvault.core.storage.session import DatabaseSession


@dataclass(frozen=True)
class MatchupFactV1:
    """One canonical head-to-head matchup result."""
    season: int
    week: int
    winner_franchise_id: str
    loser_franchise_id: str
    winner_name: str
    loser_name: str
    winner_score: str
    loser_score: str
    is_tie: bool
    canonical_event_fingerprint: str


def _resolve_franchise_name(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    franchise_id: str,
) -> str:
    """Resolve franchise_id to name via franchise_directory. Falls back to raw ID."""
    row = conn.execute(
        "SELECT name FROM franchise_directory "
        "WHERE league_id=? AND season=? AND franchise_id=? LIMIT 1",
        (str(league_id), int(season), str(franchise_id)),
    ).fetchone()
    if row and row[0]:
        return str(row[0]).strip()
    return str(franchise_id)


def query_head_to_head_matchups_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    team_a_id: str,
    team_b_id: str,
    week_indices: Sequence[int] | None = None,
) -> list[MatchupFactV1]:
    """Query canonical WEEKLY_MATCHUP_RESULT events for a specific team pair.

    Returns matchup facts ordered by week (chronological).
    Only includes weeks where team_a and team_b faced each other.

    If week_indices is provided, only those weeks are considered.
    """
    sorted_pair = tuple(sorted([str(team_a_id), str(team_b_id)]))

    with DatabaseSession(db_path) as conn:
        conn.row_factory = sqlite3.Row

        # Check if franchise_directory exists for name resolution
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        has_franchise_dir = "franchise_directory" in tables

        # Query canonical matchup events for this team pair.
        # The action_fingerprint contains sorted franchise IDs:
        #   WEEKLY_MATCHUP_RESULT:{league_id}:{season}:W{week}:{id1}_{id2}
        # We filter by matching both franchise IDs in the payload.
        rows = conn.execute(
            """
            SELECT
                ce.action_fingerprint,
                me.payload_json
            FROM canonical_events ce
            JOIN memory_events me ON me.id = ce.best_memory_event_id
            WHERE ce.league_id = ?
              AND ce.season = ?
              AND ce.event_type = 'WEEKLY_MATCHUP_RESULT'
            ORDER BY me.occurred_at, ce.action_fingerprint
            """,
            (str(league_id), int(season)),
        ).fetchall()

        facts: list[MatchupFactV1] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            winner_fid = str(payload.get("winner_franchise_id", ""))
            loser_fid = str(payload.get("loser_franchise_id", ""))

            # Filter: both teams must be in this matchup
            matchup_pair = tuple(sorted([winner_fid, loser_fid]))
            if matchup_pair != sorted_pair:
                continue

            week = int(payload.get("week", 0))

            # Filter by requested weeks if specified
            if week_indices is not None and week not in week_indices:
                continue

            # Resolve names
            if has_franchise_dir:
                winner_name = _resolve_franchise_name(conn, league_id, season, winner_fid)
                loser_name = _resolve_franchise_name(conn, league_id, season, loser_fid)
            else:
                winner_name = winner_fid
                loser_name = loser_fid

            facts.append(MatchupFactV1(
                season=int(season),
                week=week,
                winner_franchise_id=winner_fid,
                loser_franchise_id=loser_fid,
                winner_name=winner_name,
                loser_name=loser_name,
                winner_score=str(payload.get("winner_score", "")),
                loser_score=str(payload.get("loser_score", "")),
                is_tie=bool(payload.get("is_tie", False)),
                canonical_event_fingerprint=str(row["action_fingerprint"]),
            ))

        # Order by week (chronological)
        facts.sort(key=lambda f: f.week)
        return facts


def facts_block_hash_v1(facts: Sequence[MatchupFactV1]) -> str:
    """Compute deterministic SHA256 hash of the facts block."""
    payload = [
        {
            "season": f.season,
            "week": f.week,
            "winner_franchise_id": f.winner_franchise_id,
            "loser_franchise_id": f.loser_franchise_id,
            "winner_score": f.winner_score,
            "loser_score": f.loser_score,
            "is_tie": f.is_tie,
        }
        for f in facts
    ]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
