"""Scoring Rules Context v1 — Dimension 11: League Scoring Structure.

Contract:
- Derived-only: reads league_scoring_rules metadata + WEEKLY_PLAYER_SCORE events.
- Deterministic: identical inputs produce identical angles.
- Non-authoritative: contextual annotation, not a story hook.
- No inference, projection, or gap-filling.

Detector 54: SCORING_STRUCTURE_CONTEXT
Surfaces when a league's scoring rules create a notable positional deviation
compared to standard fantasy scoring. This is structural context that explains
patterns rather than surfacing them.

Example: "PFL Buddies awards 6 points per passing TD (vs. the standard 4),
which is why QBs account for 34% of all points in league history."

Reuses the NarrativeAngle dataclass from narrative_angles_v1.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from squadvault.core.recaps.context.narrative_angles_v1 import NarrativeAngle
from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)
# ── Data loading ─────────────────────────────────────────────────────


def _load_scoring_rules(
    db_path: str,
    league_id: str,
    season: int,
) -> dict[str, Any] | None:
    """Load parsed scoring rules from league_scoring_rules table.

    Returns the parsed JSON dict, or None if no data.
    """
    try:
        with DatabaseSession(db_path) as con:
            row = con.execute(
                """SELECT rules_json FROM league_scoring_rules
                   WHERE league_id = ? AND season = ?""",
                (str(league_id), int(season)),
            ).fetchone()
        if row and row[0]:
            parsed: dict[str, Any] = json.loads(row[0])
            return parsed
    except Exception as exc:
        logger.debug("%s", exc)
        pass
    return None


def _compute_positional_scoring_pct(
    db_path: str,
    league_id: str,
    season: int,
    target_week: int,
) -> dict[str, float]:
    """Compute percentage of total starter scoring per position.

    Returns dict: position -> percentage (0.0 to 1.0).
    Requires player_directory for position lookup.
    """
    # Position lookup
    positions: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT player_id, position FROM player_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        positions[str(row[0]).strip()] = str(row[1] or "").strip()

    if not positions:
        return {}

    # Aggregate starter scoring by position
    pos_totals: dict[str, float] = {}
    grand_total = 0.0

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
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue

        pid = str(p.get("player_id", "")).strip()
        pos = positions.get(pid, "")
        if not pos:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue

        pos_totals[pos] = pos_totals.get(pos, 0.0) + score
        grand_total += score

    if grand_total < 1.0:
        return {}

    return {pos: pts / grand_total for pos, pts in pos_totals.items()}


# ── Detector 54: SCORING_STRUCTURE_CONTEXT ───────────────────────────


def detect_scoring_structure_context(
    db_path: str,
    league_id: str,
    season: int,
    target_week: int,
) -> list[NarrativeAngle]:
    """Detect notable scoring rule deviations from standard fantasy.

    Surfaces when the league's rules create a measurable positional shift.
    Only fires on week 1 to avoid repetition (structural context is static).

    Returns CONTEXT-category angles (strength=1) that explain patterns
    rather than surfacing them.
    """
    if target_week != 1:
        return []

    rules = _load_scoring_rules(db_path, league_id, season)
    if not rules:
        return []

    key_rules = rules.get("key_rules", {})
    deviations = rules.get("deviations", {})
    if not deviations:
        return []

    # Compute actual positional scoring distribution
    pos_pcts = _compute_positional_scoring_pct(db_path, league_id, season, target_week)

    angles: list[NarrativeAngle] = []

    # Key deviation: passing TD points
    passing_td = key_rules.get("passing_td_pts")
    if passing_td is not None and passing_td != 4.0:
        qb_pct = pos_pcts.get("QB", 0.0)
        detail = ""
        if qb_pct > 0.25:
            detail = f"QBs account for {qb_pct:.0%} of all starter points this season."

        angles.append(NarrativeAngle(
            category="SCORING_STRUCTURE_CONTEXT",
            headline=(
                f"This league awards {passing_td:.0f} points per passing TD "
                f"(vs. the standard 4)"
            ),
            detail=detail,
            strength=1,  # MINOR / CONTEXT
            franchise_ids=(),
        ))

    # Key deviation: PPR
    reception_pts = key_rules.get("reception_pts")
    if reception_pts is not None and reception_pts > 0:
        label = "full PPR" if reception_pts >= 1.0 else f"{reception_pts}-PPR"
        wr_pct = pos_pcts.get("WR", 0.0)
        detail = ""
        if wr_pct > 0.20:
            detail = f"WRs account for {wr_pct:.0%} of all starter points this season."

        angles.append(NarrativeAngle(
            category="SCORING_STRUCTURE_CONTEXT",
            headline=f"This league uses {label} scoring ({reception_pts} pts per reception)",
            detail=detail,
            strength=1,
            franchise_ids=(),
        ))

    # Key deviation: passing yards
    passing_yd = key_rules.get("passing_yd_pts")
    if passing_yd is not None and abs(passing_yd - 0.04) > 0.005:
        yds_per_pt = round(1.0 / passing_yd) if passing_yd > 0 else 0
        standard_yds = 25
        if yds_per_pt != standard_yds:
            angles.append(NarrativeAngle(
                category="SCORING_STRUCTURE_CONTEXT",
                headline=(
                    f"Passing yards score at {yds_per_pt} yards per point "
                    f"(vs. the standard {standard_yds})"
                ),
                detail="",
                strength=1,
                franchise_ids=(),
            ))

    return angles


# ── Public API ───────────────────────────────────────────────────────


def detect_scoring_rules_angles_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> list[NarrativeAngle]:
    """Detect Dimension 11 scoring rules context angles.

    Returns empty list if no scoring rules data exists.
    Only fires on week 1.
    """
    return detect_scoring_structure_context(db_path, league_id, season, week)
