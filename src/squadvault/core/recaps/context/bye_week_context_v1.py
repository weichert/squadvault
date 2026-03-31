"""Bye Week Context v1 — Dimension 10: NFL Bye Week Impact.

Contract:
- Derived-only: computes angles from nfl_bye_weeks metadata + canonical events.
- Deterministic: identical inputs produce identical angles.
- Non-authoritative: angles are story hooks, not facts.
- Reconstructable: drop and rebuild produces identical output.
- No inference, projection, or gap-filling.

Requires: nfl_bye_weeks metadata table populated via MFL nflSchedule ingestion.
If no bye week data exists, all detectors return empty (silence over fabrication).

Detectors:
51. BYE_WEEK_IMPACT — low score explained by multiple starters on bye
52. BYE_WEEK_CONFLICT — franchise with the most bye week conflicts this week
53. FRANCHISE_BYE_WEEK_RECORD — historical record in weeks with 2+ starters on bye

Reuses the NarrativeAngle dataclass from narrative_angles_v1.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Sequence

from squadvault.core.recaps.context.narrative_angles_v1 import NarrativeAngle
from squadvault.core.recaps.context.league_history_v1 import HistoricalMatchup
from squadvault.core.storage.session import DatabaseSession


# ── Data loading ─────────────────────────────────────────────────────


def _load_bye_weeks(
    db_path: str,
    league_id: str,
    season: int,
) -> Dict[str, int]:
    """Load bye week assignments: nfl_team -> bye_week number.

    Returns empty dict if no data exists (silence over fabrication).
    """
    bye_map: Dict[str, int] = {}
    try:
        with DatabaseSession(db_path) as con:
            rows = con.execute(
                """SELECT nfl_team, bye_week FROM nfl_bye_weeks
                   WHERE league_id = ? AND season = ?""",
                (str(league_id), int(season)),
            ).fetchall()
        for row in rows:
            team = str(row[0]).strip()
            week = int(row[1])
            if team and week > 0:
                bye_map[team] = week
    except Exception:
        pass  # table may not exist yet — silence
    return bye_map


def _load_player_nfl_teams(
    db_path: str,
    league_id: str,
    season: int,
) -> Dict[str, str]:
    """Load player_id -> nfl_team from player_directory."""
    teams: Dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT player_id, team FROM player_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        pid = str(row[0]).strip()
        team = str(row[1] or "").strip()
        if pid and team:
            teams[pid] = team
    return teams


def _load_week_starters(
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> Dict[str, List[str]]:
    """Load starters per franchise for a given week: franchise_id -> [player_ids].

    Only starters (is_starter=True).
    """
    starters: Dict[str, List[str]] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        try:
            pw = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if pw != week or not p.get("is_starter"):
            continue

        fid = str(p.get("franchise_id", "")).strip()
        pid = str(p.get("player_id", "")).strip()
        if fid and pid:
            if fid not in starters:
                starters[fid] = []
            starters[fid].append(pid)

    return starters


def _count_starters_on_bye(
    starters: Dict[str, List[str]],
    player_teams: Dict[str, str],
    bye_map: Dict[str, int],
    week: int,
) -> Dict[str, int]:
    """Count how many starters per franchise are on NFL bye this week.

    Returns franchise_id -> count of starters on bye.
    """
    counts: Dict[str, int] = {}
    for fid, player_ids in starters.items():
        on_bye = 0
        for pid in player_ids:
            nfl_team = player_teams.get(pid, "")
            if nfl_team and bye_map.get(nfl_team) == week:
                on_bye += 1
        if on_bye > 0:
            counts[fid] = on_bye
    return counts


# ── Detector 51: BYE_WEEK_IMPACT ────────────────────────────────────


def detect_bye_week_impact(
    bye_counts: Dict[str, int],
    *,
    min_on_bye: int = 2,
) -> List[NarrativeAngle]:
    """Detect franchises with multiple starters on bye this week.

    Flags when a franchise has min_on_bye+ starters on NFL bye weeks.
    """
    angles: List[NarrativeAngle] = []
    for fid in sorted(bye_counts.keys()):
        count = bye_counts[fid]
        if count >= min_on_bye:
            angles.append(NarrativeAngle(
                category="BYE_WEEK_IMPACT",
                headline=(
                    f"{fid} has {count} starters on NFL bye this week"
                ),
                detail="",
                strength=1,  # MINOR
                franchise_ids=(fid,),
            ))
    return angles


# ── Detector 52: BYE_WEEK_CONFLICT ──────────────────────────────────


def detect_bye_week_conflict(
    bye_counts: Dict[str, int],
) -> List[NarrativeAngle]:
    """Detect the franchise with the most bye week conflicts this week."""
    if not bye_counts:
        return []

    max_count = max(bye_counts.values())
    if max_count < 2:
        return []

    # Find all franchises tied for most
    leaders = sorted([fid for fid, c in bye_counts.items() if c == max_count])
    if not leaders:
        return []

    fid = leaders[0]
    return [NarrativeAngle(
        category="BYE_WEEK_CONFLICT",
        headline=(
            f"{fid} had {max_count} starters on bye this week "
            f"— the most in the league"
        ),
        detail="",
        strength=1,  # MINOR
        franchise_ids=(fid,),
    )]


# ── Detector 53: FRANCHISE_BYE_WEEK_RECORD ──────────────────────────


def detect_franchise_bye_week_record(
    db_path: str,
    league_id: str,
    season: int,
    target_week: int,
    all_matchups: Sequence[HistoricalMatchup],
    *,
    min_on_bye: int = 2,
    min_bye_weeks: int = 3,
) -> List[NarrativeAngle]:
    """Detect franchise historical record in weeks with 2+ starters on bye.

    Looks across the current season for weeks where a franchise had
    min_on_bye+ starters on bye, and computes their W-L in those weeks.
    Requires bye week data and sufficient bye-heavy weeks.
    """
    bye_map = _load_bye_weeks(db_path, league_id, season)
    if not bye_map:
        return []

    player_teams = _load_player_nfl_teams(db_path, league_id, season)
    if not player_teams:
        return []

    # For each week through target_week, compute bye counts per franchise
    # Use prior week's starters — players on bye don't have score records
    franchise_bye_weeks: Dict[str, List[int]] = {}  # fid -> [week numbers with bye conflicts]
    for wk in range(2, target_week + 1):
        wk_starters = _load_week_starters(db_path, league_id, season, wk - 1)
        wk_bye_counts = _count_starters_on_bye(wk_starters, player_teams, bye_map, wk)
        for fid, count in wk_bye_counts.items():
            if count >= min_on_bye:
                if fid not in franchise_bye_weeks:
                    franchise_bye_weeks[fid] = []
                franchise_bye_weeks[fid].append(wk)

    # Build W-L per franchise in their bye-heavy weeks
    angles: List[NarrativeAngle] = []
    for fid in sorted(franchise_bye_weeks.keys()):
        bye_wks = franchise_bye_weeks[fid]
        if len(bye_wks) < min_bye_weeks:
            continue

        wins = losses = 0
        for m in all_matchups:
            if m.season == season and m.week in bye_wks and not m.is_tie:
                if m.winner_id == fid:
                    wins += 1
                elif m.loser_id == fid:
                    losses += 1

        total = wins + losses
        if total < min_bye_weeks:
            continue

        angles.append(NarrativeAngle(
            category="FRANCHISE_BYE_WEEK_RECORD",
            headline=(
                f"{fid} has gone {wins}-{losses} in weeks with "
                f"{min_on_bye}+ starters on bye"
            ),
            detail=f"Across {len(bye_wks)} bye-heavy weeks this season.",
            strength=1,  # MINOR
            franchise_ids=(fid,),
        ))

    return angles


# ── Public API ───────────────────────────────────────────────────────


def detect_bye_week_angles_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    all_matchups: Optional[Sequence[HistoricalMatchup]] = None,
) -> List[NarrativeAngle]:
    """Detect all Dimension 10 bye week angles for a given week.

    Uses the previous week's starters to determine who is affected by
    this week's byes, since players on bye don't have WEEKLY_PLAYER_SCORE
    records for the bye week itself.

    Returns empty list if no bye week data exists (silence over fabrication).
    """
    if week < 2:
        return []  # no prior roster to check in week 1

    bye_map = _load_bye_weeks(db_path, league_id, season)
    if not bye_map:
        return []

    player_teams = _load_player_nfl_teams(db_path, league_id, season)
    if not player_teams:
        return []

    # Use prior week's starters — players on bye don't have score records
    starters = _load_week_starters(db_path, league_id, season, week - 1)
    if not starters:
        return []

    bye_counts = _count_starters_on_bye(starters, player_teams, bye_map, week)

    all_angles: List[NarrativeAngle] = []

    # Detector 51: Bye week impact
    all_angles.extend(detect_bye_week_impact(bye_counts))

    # Detector 52: Bye week conflict
    all_angles.extend(detect_bye_week_conflict(bye_counts))

    # Detector 53: Bye week record (needs matchup data)
    if all_matchups:
        all_angles.extend(detect_franchise_bye_week_record(
            db_path, league_id, season, week, all_matchups,
        ))

    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))
    return all_angles
