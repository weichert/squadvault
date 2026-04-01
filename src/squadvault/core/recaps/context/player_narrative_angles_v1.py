"""Player Narrative Angle Detection v1 — Dimensions 1-5: Player Scoring Angles.

Contract:
- Derived-only: computes angles from WEEKLY_PLAYER_SCORE canonical events.
- Deterministic: identical inputs produce identical angles.
- Non-authoritative: angles are suggestions for the creative layer, not facts.
- Reconstructable: drop and rebuild from canonical events produces identical output.
- No inference, projection, or gap-filling.

Detectors (Dimension 1 — current-season player scores only):
1. PLAYER_HOT_STREAK — consecutive weeks scoring 25+ pts
2. PLAYER_COLD_STREAK — consecutive weeks scoring under 8 pts (starters)
3. PLAYER_SEASON_HIGH — highest individual score of the season this week
4. PLAYER_BOOM_BUST — score >= 2x or <= 0.3x their 4-week average
5. PLAYER_BREAKOUT — first time exceeding 20+ pts on this franchise
6. ZERO_POINT_STARTER — a starter scored exactly 0.00 points

Detectors (Dimension 2 — cross-season player scores):
7. PLAYER_ALLTIME_HIGH — highest individual score in league history
8. PLAYER_FRANCHISE_RECORD — new single-week scoring record for franchise (tenure-scoped)
9. CAREER_MILESTONE — crossed 500/1000/1500/2000 career points on a franchise
10. PLAYER_FRANCHISE_TENURE — player on same franchise for 3+ consecutive seasons
11. PLAYER_JOURNEY — player rostered by 3+ different franchises in career

Detectors (Dimension 3 — player scores cross-referenced with matchups):
12. PLAYER_VS_OPPONENT — player dominates a specific opposing franchise
13. REVENGE_GAME — player scores against franchise they were previously on
14. PLAYER_DUEL — two players on opposing franchises, tracked head-to-head

Detectors (Dimension 4 — trade & transaction outcomes):
15. TRADE_OUTCOME — post-trade scoring comparison between traded players
16. THE_ONE_THAT_GOT_AWAY — dropped player scoring well on another franchise

Detectors (Dimension 5 — FAAB & waiver efficiency):
17. FAAB_ROI_NOTABLE — FAAB acquisition points exceed 3x bid amount
18. FAAB_FRANCHISE_EFFICIENCY — franchise FAAB pickups outproduce league average
19. WAIVER_DEPENDENCY — 30%+ of franchise scoring from non-drafted players

Reuses the NarrativeAngle dataclass from narrative_angles_v1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from squadvault.core.recaps.context.narrative_angles_v1 import NarrativeAngle
from squadvault.core.storage.session import DatabaseSession

from squadvault.core.resolvers import NameFn, identity as _identity


# ── Data loading ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class _PlayerWeekRecord:
    """Minimal record for a player's scoring in a single week."""
    week: int
    franchise_id: str
    player_id: str
    score: float
    is_starter: bool


def _load_season_player_scores(
    db_path: str,
    league_id: str,
    season: int,
) -> List[_PlayerWeekRecord]:
    """Load all WEEKLY_PLAYER_SCORE events for a season.

    Returns records sorted by (week, franchise_id, player_id) for determinism.
    """
    records: List[_PlayerWeekRecord] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
               ORDER BY payload_json ASC""",
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
        if week < 1:
            continue

        player_id = str(p.get("player_id", "")).strip()
        franchise_id = str(p.get("franchise_id", "")).strip()
        if not player_id or not franchise_id:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0

        is_starter = bool(p.get("is_starter", False))

        records.append(_PlayerWeekRecord(
            week=week,
            franchise_id=franchise_id,
            player_id=player_id,
            score=score,
            is_starter=is_starter,
        ))

    # Deterministic sort
    records.sort(key=lambda r: (r.week, r.franchise_id, r.player_id))
    return records


def _load_all_seasons_starter_zeros(
    db_path: str,
    league_id: str,
) -> int:
    """Count all-time zero-point starter events across all seasons.

    Used by ZERO_POINT_STARTER to provide historical context
    ("only the Nth time a starter has been zeroed out in league history").

    Returns the total count of WEEKLY_PLAYER_SCORE events where
    is_starter=True and score=0.0 across all seasons.
    """
    count = 0

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'""",
            (str(league_id),),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        is_starter = bool(p.get("is_starter", False))
        if not is_starter:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue

        if score == 0.0:
            count += 1

    return count


@dataclass(frozen=True)
class _CrossSeasonRecord:
    """Player scoring record with season context for cross-season detectors."""
    season: int
    week: int
    franchise_id: str
    player_id: str
    score: float
    is_starter: bool


def _load_all_seasons_player_scores(
    db_path: str,
    league_id: str,
) -> List[_CrossSeasonRecord]:
    """Load all WEEKLY_PLAYER_SCORE events across all seasons.

    Returns records sorted by (season, week, franchise_id, player_id) for determinism.
    Used by Dimension 2 detectors for cross-season analysis.
    """
    records: List[_CrossSeasonRecord] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT season, payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
               ORDER BY season ASC, payload_json ASC""",
            (str(league_id),),
        ).fetchall()

    for row in rows:
        try:
            row_season = int(row[0])
        except (ValueError, TypeError):
            continue

        try:
            p = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        except (ValueError, TypeError):
            continue

        if not isinstance(p, dict):
            continue

        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week < 1:
            continue

        player_id = str(p.get("player_id", "")).strip()
        franchise_id = str(p.get("franchise_id", "")).strip()
        if not player_id or not franchise_id:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0

        is_starter = bool(p.get("is_starter", False))

        records.append(_CrossSeasonRecord(
            season=row_season,
            week=week,
            franchise_id=franchise_id,
            player_id=player_id,
            score=score,
            is_starter=is_starter,
        ))

    records.sort(key=lambda r: (r.season, r.week, r.franchise_id, r.player_id))
    return records


def _load_all_matchup_opponents(
    db_path: str,
    league_id: str,
) -> Dict[Tuple[int, int, str], str]:
    """Load all WEEKLY_MATCHUP_RESULT events and build an opponent index.

    Returns dict: (season, week, franchise_id) -> opponent_franchise_id.
    Each matchup produces two entries (one per franchise).
    Used by Dimension 3 detectors to link player scores with opponents.
    """
    opponents: Dict[Tuple[int, int, str], str] = {}

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT season, payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'
               ORDER BY season ASC""",
            (str(league_id),),
        ).fetchall()

    for row in rows:
        try:
            season = int(row[0])
        except (ValueError, TypeError):
            continue

        try:
            p = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week < 1:
            continue

        winner = str(p.get("winner_franchise_id") or p.get("winner_team_id") or "").strip()
        loser = str(p.get("loser_franchise_id") or p.get("loser_team_id") or "").strip()
        if not winner or not loser:
            continue

        opponents[(season, week, winner)] = loser
        opponents[(season, week, loser)] = winner

    return opponents


@dataclass(frozen=True)
class _TradeMove:
    """One side of a trade: which franchise added/dropped which players."""
    season: int
    franchise_id: str
    players_added: Tuple[str, ...]
    players_dropped: Tuple[str, ...]
    occurred_at: str


@dataclass(frozen=True)
class _PlayerDrop:
    """A player dropped from a franchise (any transaction type)."""
    season: int
    franchise_id: str
    player_id: str
    occurred_at: str


def _load_season_trades(
    db_path: str,
    league_id: str,
    season: int,
) -> List[Tuple[_TradeMove, _TradeMove]]:
    """Load TRANSACTION_TRADE events for a season and pair them.

    Returns list of trade pairs. Each pair is two _TradeMove records
    representing the two sides of a trade, matched by occurred_at timestamp.
    Unpaired trade records are discarded (data integrity issue, silence over
    fabrication).
    """
    moves: List[_TradeMove] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json, occurred_at
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'TRANSACTION_TRADE'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        franchise_id = str(p.get("franchise_id", "")).strip()
        if not franchise_id:
            continue

        occurred_at = str(row[1] or "").strip()

        added_raw = p.get("players_added_ids", "")
        dropped_raw = p.get("players_dropped_ids", "")

        def _split_ids(val) -> Tuple[str, ...]:
            if isinstance(val, list):
                return tuple(str(x).strip() for x in val if str(x).strip())
            if isinstance(val, str) and val.strip():
                return tuple(x.strip() for x in val.split(",") if x.strip())
            return ()

        added = _split_ids(added_raw)
        dropped = _split_ids(dropped_raw)

        if not added and not dropped:
            continue

        moves.append(_TradeMove(
            season=season,
            franchise_id=franchise_id,
            players_added=added,
            players_dropped=dropped,
            occurred_at=occurred_at,
        ))

    # Pair trades by occurred_at timestamp
    by_timestamp: Dict[str, List[_TradeMove]] = {}
    for m in moves:
        if m.occurred_at not in by_timestamp:
            by_timestamp[m.occurred_at] = []
        by_timestamp[m.occurred_at].append(m)

    pairs: List[Tuple[_TradeMove, _TradeMove]] = []
    for ts in sorted(by_timestamp.keys()):
        group = by_timestamp[ts]
        if len(group) == 2:
            # Deterministic ordering: lower franchise_id first
            group.sort(key=lambda m: m.franchise_id)
            pairs.append((group[0], group[1]))
        # Unpaired or 3+ way: silence (data anomaly)

    return pairs


def _load_season_drops(
    db_path: str,
    league_id: str,
    season: int,
) -> List[_PlayerDrop]:
    """Load all transactions that dropped players in a season.

    Returns _PlayerDrop records for every player in players_dropped_ids
    across all TRANSACTION_* events (trades, free agent swaps, waivers).
    """
    drops: List[_PlayerDrop] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json, occurred_at
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type LIKE 'TRANSACTION_%'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        franchise_id = str(p.get("franchise_id", "")).strip()
        if not franchise_id:
            continue

        occurred_at = str(row[1] or "").strip()

        dropped_raw = p.get("players_dropped_ids", "")
        if isinstance(dropped_raw, list):
            dropped_ids = [str(x).strip() for x in dropped_raw if str(x).strip()]
        elif isinstance(dropped_raw, str) and dropped_raw.strip():
            dropped_ids = [x.strip() for x in dropped_raw.split(",") if x.strip()]
        else:
            continue

        for pid in dropped_ids:
            drops.append(_PlayerDrop(
                season=season,
                franchise_id=franchise_id,
                player_id=pid,
                occurred_at=occurred_at,
            ))

    # Deterministic sort
    drops.sort(key=lambda d: (d.occurred_at, d.franchise_id, d.player_id))
    return drops


@dataclass(frozen=True)
class _FaabAcquisition:
    """A FAAB (waiver bid) acquisition."""
    season: int
    franchise_id: str
    player_id: str
    bid_amount: float


def _load_season_faab_acquisitions(
    db_path: str,
    league_id: str,
    season: int,
) -> List[_FaabAcquisition]:
    """Load WAIVER_BID_AWARDED events for a season.

    Returns _FaabAcquisition records for each awarded bid.
    Only awards — never losing bids (per FAAB Outcome Insight contract).
    """
    acquisitions: List[_FaabAcquisition] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        franchise_id = str(p.get("franchise_id", "")).strip()
        if not franchise_id:
            continue

        # Extract player_id — may be direct or in players_added_ids
        player_id = str(p.get("player_id", "")).strip()
        if not player_id:
            added = p.get("players_added_ids")
            if isinstance(added, str) and added.strip():
                player_id = added.split(",")[0].strip()
            elif isinstance(added, list) and added:
                player_id = str(added[0]).strip()
        if not player_id:
            continue

        try:
            bid_amount = float(p.get("bid_amount", 0))
        except (ValueError, TypeError):
            continue
        if bid_amount <= 0:
            continue

        acquisitions.append(_FaabAcquisition(
            season=season,
            franchise_id=franchise_id,
            player_id=player_id,
            bid_amount=bid_amount,
        ))

    acquisitions.sort(key=lambda a: (a.franchise_id, a.player_id))
    return acquisitions


def _load_season_drafted_players(
    db_path: str,
    league_id: str,
    season: int,
) -> Dict[str, set]:
    """Load DRAFT_PICK events for a season and return drafted players per franchise.

    Returns dict: franchise_id -> set of player_ids drafted by that franchise.
    """
    drafted: Dict[str, set] = {}

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'DRAFT_PICK'""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        franchise_id = str(p.get("franchise_id", "")).strip()
        player_id = str(p.get("player_id", "")).strip()
        if not franchise_id or not player_id:
            continue

        if franchise_id not in drafted:
            drafted[franchise_id] = set()
        drafted[franchise_id].add(player_id)

    return drafted


# ── Index builders ───────────────────────────────────────────────────


def _build_player_franchise_weeks(
    records: List[_PlayerWeekRecord],
    through_week: int,
) -> Dict[Tuple[str, str], List[_PlayerWeekRecord]]:
    """Group records by (franchise_id, player_id), filtered to <= through_week.

    Returns dict keyed by (franchise_id, player_id) with records sorted by week asc.
    """
    index: Dict[Tuple[str, str], List[_PlayerWeekRecord]] = {}
    for r in records:
        if r.week > through_week:
            continue
        key = (r.franchise_id, r.player_id)
        if key not in index:
            index[key] = []
        index[key].append(r)

    # Sort each player's records by week for streak/sequence detection
    for key in index:
        index[key].sort(key=lambda r: r.week)

    return index


def _build_week_scores(
    records: List[_PlayerWeekRecord],
    week: int,
) -> List[_PlayerWeekRecord]:
    """Extract all records for a specific week."""
    return [r for r in records if r.week == week]


# ── Detector 1: PLAYER_HOT_STREAK ───────────────────────────────────


def detect_player_hot_streak(
    records: List[_PlayerWeekRecord],
    target_week: int,
    *,
    threshold: float = 25.0,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect players scoring above threshold for consecutive weeks ending at target_week.

    Thresholds: 3 weeks = MINOR, 4 = NOTABLE, 5+ = HEADLINE.
    Only counts weeks where the player was a starter.
    """
    index = _build_player_franchise_weeks(records, target_week)
    angles: List[NarrativeAngle] = []

    for (franchise_id, player_id), player_records in sorted(index.items()):
        # Only consider starters — a hot streak is a starter phenomenon
        starter_records = [r for r in player_records if r.is_starter]
        if not starter_records:
            continue

        # Count consecutive weeks ending at target_week where score >= threshold
        # Walk backwards from target_week
        streak = 0
        week_cursor = target_week
        # Build a week -> score map for this player's starter appearances
        week_score_map = {r.week: r.score for r in starter_records}

        while week_cursor >= 1:
            if week_cursor in week_score_map and week_score_map[week_cursor] >= threshold:
                streak += 1
                week_cursor -= 1
            else:
                break

        if streak >= 3:
            if streak >= 5:
                strength = 3  # HEADLINE
            elif streak == 4:
                strength = 2  # NOTABLE
            else:
                strength = 1  # MINOR

            latest_score = week_score_map.get(target_week, 0.0)
            angles.append(NarrativeAngle(
                category="PLAYER_HOT_STREAK",
                headline=(
                    f"{pname(player_id)} has scored {threshold:.0f}+ points in "
                    f"{streak} consecutive weeks for {fname(franchise_id)}"
                ),
                detail=f"Latest: {latest_score:.2f} pts in Week {target_week}.",
                strength=strength,
                franchise_ids=(franchise_id,),
            ))

    return angles


# ── Detector 2: PLAYER_COLD_STREAK ──────────────────────────────────


def detect_player_cold_streak(
    records: List[_PlayerWeekRecord],
    target_week: int,
    *,
    threshold: float = 8.0,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect starters scoring below threshold for consecutive weeks ending at target_week.

    Thresholds: 3 weeks = NOTABLE, 4+ = HEADLINE.
    Only starters — a cold streak for a benched player is not newsworthy.
    """
    index = _build_player_franchise_weeks(records, target_week)
    angles: List[NarrativeAngle] = []

    for (franchise_id, player_id), player_records in sorted(index.items()):
        starter_records = [r for r in player_records if r.is_starter]
        if not starter_records:
            continue

        week_score_map = {r.week: r.score for r in starter_records}

        streak = 0
        week_cursor = target_week
        while week_cursor >= 1:
            if week_cursor in week_score_map and week_score_map[week_cursor] < threshold:
                streak += 1
                week_cursor -= 1
            else:
                break

        if streak >= 3:
            strength = 3 if streak >= 4 else 2  # 4+ = HEADLINE, 3 = NOTABLE
            latest_score = week_score_map.get(target_week, 0.0)
            angles.append(NarrativeAngle(
                category="PLAYER_COLD_STREAK",
                headline=(
                    f"{pname(player_id)} has scored under {threshold:.0f} points in "
                    f"{streak} straight starts for {fname(franchise_id)}"
                ),
                detail=f"Latest: {latest_score:.2f} pts in Week {target_week}.",
                strength=strength,
                franchise_ids=(franchise_id,),
            ))

    return angles


# ── Detector 3: PLAYER_SEASON_HIGH ──────────────────────────────────


def detect_player_season_high(
    records: List[_PlayerWeekRecord],
    target_week: int,
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect if a player posted the highest individual score of the season this week.

    Only starters. Compares the highest score in target_week against
    all prior weeks in the season.
    """
    all_through_week = [r for r in records if r.week <= target_week and r.is_starter]
    this_week = [r for r in all_through_week if r.week == target_week]
    prior_weeks = [r for r in all_through_week if r.week < target_week]

    if not this_week:
        return []

    # Find the highest score this week
    this_week_sorted = sorted(this_week, key=lambda r: (-r.score, r.franchise_id, r.player_id))
    best_this_week = this_week_sorted[0]

    # Find the highest score in all prior weeks
    prior_best = max((r.score for r in prior_weeks), default=0.0)

    if best_this_week.score > prior_best and best_this_week.score > 0.0:
        angles: List[NarrativeAngle] = []

        # Week 1 edge case: no prior data, so every score is the season high.
        # Only flag if there are prior weeks to compare against.
        if not prior_weeks:
            return []

        angles.append(NarrativeAngle(
            category="PLAYER_SEASON_HIGH",
            headline=(
                f"{pname(best_this_week.player_id)}'s {best_this_week.score:.2f} points "
                f"is the highest individual score of the season"
            ),
            detail=(
                f"For {fname(best_this_week.franchise_id)}. "
                f"Previous season high: {prior_best:.2f}."
            ),
            strength=3,  # Always HEADLINE
            franchise_ids=(best_this_week.franchise_id,),
        ))
        return angles

    return []


# ── Detector 4: PLAYER_BOOM_BUST ────────────────────────────────────


def detect_player_boom_bust(
    records: List[_PlayerWeekRecord],
    target_week: int,
    *,
    boom_multiplier: float = 2.0,
    bust_multiplier: float = 0.3,
    min_prior_weeks: int = 4,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect starters who dramatically outperformed or underperformed their recent average.

    Boom: score >= boom_multiplier × 4-week average.
    Bust: score <= bust_multiplier × 4-week average.
    Requires min_prior_weeks of starter data before target_week. Fewer = silence.
    """
    index = _build_player_franchise_weeks(records, target_week)
    angles: List[NarrativeAngle] = []

    for (franchise_id, player_id), player_records in sorted(index.items()):
        # Target week must be a starter appearance
        target_records = [r for r in player_records if r.week == target_week and r.is_starter]
        if not target_records:
            continue
        target_score = target_records[0].score

        # Collect prior starter weeks (up to 4 most recent before target_week)
        prior_starter = [
            r for r in player_records
            if r.week < target_week and r.is_starter
        ]
        prior_starter.sort(key=lambda r: r.week, reverse=True)
        recent_prior = prior_starter[:min_prior_weeks]

        if len(recent_prior) < min_prior_weeks:
            continue  # Silence — not enough data

        avg_score = sum(r.score for r in recent_prior) / len(recent_prior)

        # Avoid division by zero and trivially low averages
        if avg_score < 1.0:
            continue

        ratio = target_score / avg_score

        if ratio >= boom_multiplier:
            angles.append(NarrativeAngle(
                category="PLAYER_BOOM_BUST",
                headline=(
                    f"{pname(player_id)}'s {target_score:.2f} points is "
                    f"{ratio:.1f}x their {len(recent_prior)}-week average "
                    f"of {avg_score:.2f} for {fname(franchise_id)}"
                ),
                detail=f"Boom performance in Week {target_week}.",
                strength=1,  # Always MINOR per spec
                franchise_ids=(franchise_id,),
            ))
        elif ratio <= bust_multiplier:
            angles.append(NarrativeAngle(
                category="PLAYER_BOOM_BUST",
                headline=(
                    f"{pname(player_id)}'s {target_score:.2f} points is "
                    f"{ratio:.1f}x their {len(recent_prior)}-week average "
                    f"of {avg_score:.2f} for {fname(franchise_id)}"
                ),
                detail=f"Bust performance in Week {target_week}.",
                strength=1,  # Always MINOR per spec
                franchise_ids=(franchise_id,),
            ))

    return angles


# ── Detector 5: PLAYER_BREAKOUT ─────────────────────────────────────


def detect_player_breakout(
    records: List[_PlayerWeekRecord],
    target_week: int,
    *,
    breakout_threshold: float = 20.0,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect first time a player exceeds a scoring threshold on this franchise.

    Only starters. If a player scores 20+ for the first time on this franchise
    in this season, flag it.
    """
    index = _build_player_franchise_weeks(records, target_week)
    angles: List[NarrativeAngle] = []

    for (franchise_id, player_id), player_records in sorted(index.items()):
        # Target week must be a starter appearance over the threshold
        target_records = [r for r in player_records if r.week == target_week and r.is_starter]
        if not target_records:
            continue
        target_score = target_records[0].score
        if target_score < breakout_threshold:
            continue

        # Check if this is the first time over the threshold this season
        prior_over = [
            r for r in player_records
            if r.week < target_week and r.score >= breakout_threshold
        ]
        if len(prior_over) > 0:
            continue  # Not the first time

        # Must have at least 1 prior week on this franchise to be a "breakout"
        prior_any = [r for r in player_records if r.week < target_week]
        if not prior_any:
            continue  # First week on the franchise — not a breakout

        angles.append(NarrativeAngle(
            category="PLAYER_BREAKOUT",
            headline=(
                f"This was {pname(player_id)}'s first {breakout_threshold:.0f}+ point game "
                f"for {fname(franchise_id)}"
            ),
            detail=f"{target_score:.2f} pts in Week {target_week}.",
            strength=1,  # Always MINOR per spec
            franchise_ids=(franchise_id,),
        ))

    return angles


# ── Detector 6: ZERO_POINT_STARTER ──────────────────────────────────


def detect_zero_point_starter(
    records: List[_PlayerWeekRecord],
    target_week: int,
    *,
    alltime_zero_count: Optional[int] = None,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect starters who scored exactly 0.00 points this week.

    alltime_zero_count: if provided, adds historical context
    ("only the Nth time a starter has been zeroed out in league history").
    """
    this_week = [
        r for r in records
        if r.week == target_week and r.is_starter and r.score == 0.0
    ]

    angles: List[NarrativeAngle] = []
    for r in sorted(this_week, key=lambda r: (r.franchise_id, r.player_id)):
        detail_parts = [f"Week {target_week} starter."]
        if alltime_zero_count is not None and alltime_zero_count > 0:
            detail_parts.append(
                f"Only the {_ordinal(alltime_zero_count)} time a starter "
                f"has been zeroed out in league history."
            )

        angles.append(NarrativeAngle(
            category="ZERO_POINT_STARTER",
            headline=(
                f"{fname(r.franchise_id)} started {pname(r.player_id)} for 0.00 points"
            ),
            detail=" ".join(detail_parts),
            strength=2,  # NOTABLE per spec
            franchise_ids=(r.franchise_id,),
        ))

    return angles


def _ordinal(n: int) -> str:
    """Convert integer to ordinal string (1st, 2nd, 3rd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# ── Detector 7: PLAYER_ALLTIME_HIGH ─────────────────────────────────


def detect_player_alltime_high(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect if a player posted the highest individual score in league history.

    Only starters. Only surfaces when history depth > 1 season (per spec).
    """
    seasons_present = {r.season for r in all_records}
    if len(seasons_present) < 2:
        return []

    # All starter scores up through the target week of the current season
    eligible = [
        r for r in all_records
        if r.is_starter and (
            r.season < current_season
            or (r.season == current_season and r.week <= target_week)
        )
    ]
    if not eligible:
        return []

    # This week's starters
    this_week = [
        r for r in eligible
        if r.season == current_season and r.week == target_week
    ]
    if not this_week:
        return []

    # Prior history (everything except this week)
    prior = [
        r for r in eligible
        if not (r.season == current_season and r.week == target_week)
    ]
    if not prior:
        return []

    prior_best_score = max(r.score for r in prior)

    # Find the best scorer this week
    this_week_sorted = sorted(this_week, key=lambda r: (-r.score, r.franchise_id, r.player_id))
    best = this_week_sorted[0]

    if best.score > prior_best_score and best.score > 0.0:
        num_seasons = len(seasons_present)
        return [NarrativeAngle(
            category="PLAYER_ALLTIME_HIGH",
            headline=(
                f"{pname(best.player_id)}'s {best.score:.2f} points is the highest "
                f"individual score in league history ({num_seasons} seasons)"
            ),
            detail=f"For {fname(best.franchise_id)}. Previous all-time high: {prior_best_score:.2f}.",
            strength=3,  # Always HEADLINE
            franchise_ids=(best.franchise_id,),
        )]

    return []


# ── Detector 8: PLAYER_FRANCHISE_RECORD ─────────────────────────────


def detect_player_franchise_record(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    *,
    tenure_map: Optional[Dict[str, int]] = None,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect if a player set a new single-week scoring record for their franchise.

    Scoped to current owner's tenure (via tenure_map). Only starters.
    Only surfaces when there's at least 1 prior season of franchise history.
    """
    # This week's starters on the current season
    this_week = [
        r for r in all_records
        if r.season == current_season and r.week == target_week and r.is_starter
    ]
    if not this_week:
        return []

    angles: List[NarrativeAngle] = []

    # Group this week's records by franchise
    franchises_this_week: Dict[str, List[_CrossSeasonRecord]] = {}
    for r in this_week:
        if r.franchise_id not in franchises_this_week:
            franchises_this_week[r.franchise_id] = []
        franchises_this_week[r.franchise_id].append(r)

    for franchise_id in sorted(franchises_this_week.keys()):
        # Determine tenure start
        tenure_start = tenure_map.get(franchise_id) if tenure_map else None

        # All starter records for this franchise within tenure
        franchise_records = [
            r for r in all_records
            if r.franchise_id == franchise_id and r.is_starter
            and (tenure_start is None or r.season >= tenure_start)
            and (r.season < current_season or (r.season == current_season and r.week <= target_week))
        ]

        # Must have prior history (not just this week)
        prior_records = [
            r for r in franchise_records
            if not (r.season == current_season and r.week == target_week)
        ]
        if not prior_records:
            continue

        # Need at least 1 prior season for this to be meaningful
        prior_seasons = {r.season for r in prior_records}
        if current_season not in prior_seasons and len(prior_seasons) < 1:
            continue

        prior_best = max(r.score for r in prior_records)

        # Best this week for this franchise
        week_records = sorted(
            franchises_this_week[franchise_id],
            key=lambda r: (-r.score, r.player_id),
        )
        best = week_records[0]

        if best.score > prior_best and best.score > 0.0:
            tenure_label = f"since {tenure_start}" if tenure_start else "all-time"
            angles.append(NarrativeAngle(
                category="PLAYER_FRANCHISE_RECORD",
                headline=(
                    f"{pname(best.player_id)}'s {best.score:.2f} points is the highest "
                    f"single-week score for {fname(franchise_id)} ({tenure_label})"
                ),
                detail=f"Previous franchise record: {prior_best:.2f}.",
                strength=2,  # NOTABLE per spec
                franchise_ids=(franchise_id,),
            ))

    return angles


# ── Detector 9: CAREER_MILESTONE ────────────────────────────────────


_CAREER_MILESTONES = [2000, 1500, 1000, 500]  # checked high to low


def detect_career_milestone(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect if a player crossed a career scoring milestone on a franchise.

    Milestones: 500, 1000, 1500, 2000 career points on the same franchise.
    Only checks when the milestone was crossed THIS week (not previously).
    """
    # Group all records by (franchise_id, player_id) up through target week
    career_index: Dict[Tuple[str, str], List[_CrossSeasonRecord]] = {}
    for r in all_records:
        if r.season < current_season or (r.season == current_season and r.week <= target_week):
            key = (r.franchise_id, r.player_id)
            if key not in career_index:
                career_index[key] = []
            career_index[key].append(r)

    angles: List[NarrativeAngle] = []

    for (franchise_id, player_id), records in sorted(career_index.items()):
        # Total career points on this franchise
        total = sum(r.score for r in records)

        # Points BEFORE this week
        prior = sum(
            r.score for r in records
            if not (r.season == current_season and r.week == target_week)
        )

        # Check each milestone (high to low) — report only the highest one crossed
        for milestone in _CAREER_MILESTONES:
            if total >= milestone and prior < milestone:
                angles.append(NarrativeAngle(
                    category="CAREER_MILESTONE",
                    headline=(
                        f"{pname(player_id)} just crossed {milestone:,} career points "
                        f"for {fname(franchise_id)}"
                    ),
                    detail=f"Career total: {total:.2f} pts.",
                    strength=2,  # NOTABLE per spec
                    franchise_ids=(franchise_id,),
                ))
                break  # only report the highest milestone crossed

    return angles


# ── Detector 10: PLAYER_FRANCHISE_TENURE ─────────────────────────────


def detect_player_franchise_tenure(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect players on the same franchise for 3+ consecutive seasons.

    Only surfaces once per season (when target_week == 1) to avoid
    repeating the same angle every week.
    """
    if target_week != 1:
        return []

    # Build: (franchise_id, player_id) -> set of seasons they appeared
    roster_seasons: Dict[Tuple[str, str], set] = {}
    for r in all_records:
        if r.season <= current_season:
            key = (r.franchise_id, r.player_id)
            if key not in roster_seasons:
                roster_seasons[key] = set()
            roster_seasons[key].add(r.season)

    angles: List[NarrativeAngle] = []

    # Find longest active consecutive streak ending at current_season
    # Also find league-wide max for "longest active tenure" claim
    tenure_data: List[Tuple[str, str, int]] = []  # (franchise_id, player_id, streak)

    for (franchise_id, player_id), seasons in sorted(roster_seasons.items()):
        if current_season not in seasons:
            continue  # not active this season

        # Count consecutive seasons ending at current_season
        streak = 0
        yr = current_season
        while yr in seasons:
            streak += 1
            yr -= 1

        if streak >= 3:
            tenure_data.append((franchise_id, player_id, streak))

    if not tenure_data:
        return []

    max_streak = max(s for _, _, s in tenure_data)

    for franchise_id, player_id, streak in tenure_data:
        is_longest = (streak == max_streak)
        detail = f"{streak} consecutive seasons."
        if is_longest and len(tenure_data) > 1:
            detail += " Longest active player tenure in the league."

        angles.append(NarrativeAngle(
            category="PLAYER_FRANCHISE_TENURE",
            headline=(
                f"{pname(player_id)} has been on {fname(franchise_id)}'s roster "
                f"for {streak} consecutive seasons"
            ),
            detail=detail,
            strength=1,  # MINOR per spec
            franchise_ids=(franchise_id,),
        ))

    return angles


# ── Detector 11: PLAYER_JOURNEY ──────────────────────────────────────


def detect_player_journey(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect players rostered by 3+ different franchises in their league career.

    Only surfaces for players who scored this week (active and relevant).
    Only surfaces once per season (target_week == 1) to avoid repetition.
    """
    if target_week != 1:
        return []

    # This week's active players
    active_this_week = {
        r.player_id for r in all_records
        if r.season == current_season and r.week == target_week
    }

    if not active_this_week:
        return []

    # Build: player_id -> set of franchise_ids across all seasons
    player_franchises: Dict[str, set] = {}
    for r in all_records:
        if r.season <= current_season:
            if r.player_id not in player_franchises:
                player_franchises[r.player_id] = set()
            player_franchises[r.player_id].add(r.franchise_id)

    angles: List[NarrativeAngle] = []

    for player_id in sorted(active_this_week):
        franchises = player_franchises.get(player_id, set())
        if len(franchises) >= 3:
            # Find earliest season for this player
            player_seasons = {
                r.season for r in all_records if r.player_id == player_id
            }
            earliest = min(player_seasons) if player_seasons else current_season

            angles.append(NarrativeAngle(
                category="PLAYER_JOURNEY",
                headline=(
                    f"{pname(player_id)} has been rostered by {len(franchises)} different "
                    f"franchises since {earliest}"
                ),
                detail="",
                strength=1,  # MINOR per spec
                franchise_ids=tuple(sorted(franchises)),
            ))

    return angles


# ── Detector 12: PLAYER_VS_OPPONENT ──────────────────────────────────


def detect_player_vs_opponent(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    opponent_index: Dict[Tuple[int, int, str], str],
    *,
    threshold: float = 30.0,
    min_meetings: int = 3,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect players who consistently dominate a specific opposing franchise.

    Looks at all prior meetings where the player was on the same franchise
    and played against the same opponent. If the player scored >= threshold
    in all N meetings (N >= min_meetings), flag it.
    """
    # This week's starters
    this_week = [
        r for r in all_records
        if r.season == current_season and r.week == target_week and r.is_starter
    ]
    if not this_week:
        return []

    angles: List[NarrativeAngle] = []

    for r in sorted(this_week, key=lambda x: (x.franchise_id, x.player_id)):
        opponent_id = opponent_index.get((current_season, target_week, r.franchise_id))
        if not opponent_id:
            continue

        # Find all prior meetings where this player was on this franchise
        # and the franchise played this same opponent
        prior_scores: List[float] = []
        for hr in all_records:
            if hr.player_id != r.player_id or hr.franchise_id != r.franchise_id:
                continue
            if hr.season == current_season and hr.week >= target_week:
                continue  # exclude this week and future
            opp = opponent_index.get((hr.season, hr.week, hr.franchise_id))
            if opp == opponent_id and hr.is_starter:
                prior_scores.append(hr.score)

        if len(prior_scores) < min_meetings:
            continue

        # Check if player scored >= threshold in ALL prior meetings
        all_above = all(s >= threshold for s in prior_scores)
        if all_above:
            total_meetings = len(prior_scores)
            strength = 2 if total_meetings >= 4 else 1  # NOTABLE at 4+, MINOR at 3
            angles.append(NarrativeAngle(
                category="PLAYER_VS_OPPONENT",
                headline=(
                    f"{pname(r.player_id)} has scored {threshold:.0f}+ in all "
                    f"{total_meetings} career games against {fname(opponent_id)} "
                    f"for {fname(r.franchise_id)}"
                ),
                detail=f"This week: {r.score:.2f} pts.",
                strength=strength,
                franchise_ids=(r.franchise_id, opponent_id),
            ))

    return angles


# ── Detector 13: REVENGE_GAME ────────────────────────────────────────


def detect_revenge_game(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    opponent_index: Dict[Tuple[int, int, str], str],
    *,
    min_score: float = 15.0,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect a player scoring against a franchise they were previously on.

    A revenge game requires:
    1. Player P has historical WEEKLY_PLAYER_SCORE records on franchise F2.
    2. P is now on franchise F1 and scored >= min_score this week.
    3. F1 played F2 this week.

    Detection is from player score history (the most reliable signal).
    Only starters with meaningful scores (>= min_score) are flagged.
    """
    # This week's starters with meaningful scores
    this_week = [
        r for r in all_records
        if r.season == current_season and r.week == target_week
        and r.is_starter and r.score >= min_score
    ]
    if not this_week:
        return []

    # Build lookup: player_id -> set of franchise_ids they've been on (prior history)
    player_prior_franchises: Dict[str, set] = {}
    for r in all_records:
        if r.season < current_season or (r.season == current_season and r.week < target_week):
            if r.player_id not in player_prior_franchises:
                player_prior_franchises[r.player_id] = set()
            player_prior_franchises[r.player_id].add(r.franchise_id)

    angles: List[NarrativeAngle] = []

    for r in sorted(this_week, key=lambda x: (x.franchise_id, x.player_id)):
        opponent_id = opponent_index.get((current_season, target_week, r.franchise_id))
        if not opponent_id:
            continue

        prior_franchises = player_prior_franchises.get(r.player_id, set())
        if opponent_id in prior_franchises and opponent_id != r.franchise_id:
            angles.append(NarrativeAngle(
                category="REVENGE_GAME",
                headline=(
                    f"{pname(r.player_id)}, formerly on {fname(opponent_id)}, scored "
                    f"{r.score:.2f} against them for {fname(r.franchise_id)}"
                ),
                detail=f"Week {target_week}.",
                strength=1,  # MINOR per spec
                franchise_ids=(r.franchise_id, opponent_id),
            ))

    return angles


# ── Detector 14: PLAYER_DUEL ────────────────────────────────────────


def detect_player_duel(
    all_records: List[_CrossSeasonRecord],
    current_season: int,
    target_week: int,
    opponent_index: Dict[Tuple[int, int, str], str],
    *,
    min_meetings: int = 3,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect two players on opposing franchises who have met head-to-head multiple times.

    A duel requires:
    1. Player A on franchise F1, Player B on franchise F2.
    2. F1 and F2 played each other this week (both A and B are starters).
    3. A and B have been on opposing sides in the same matchup >= min_meetings times prior.
    4. Report the head-to-head record (who outscored whom more often).

    Only same-position duels (or QB vs QB) are most interesting, but position data
    is not in WEEKLY_PLAYER_SCORE. We surface based on meeting frequency and let
    the creative layer decide which to highlight.
    """
    # This week's starters
    this_week = [
        r for r in all_records
        if r.season == current_season and r.week == target_week and r.is_starter
    ]
    if not this_week:
        return []

    # Group this week's starters by franchise
    by_franchise: Dict[str, List[_CrossSeasonRecord]] = {}
    for r in this_week:
        if r.franchise_id not in by_franchise:
            by_franchise[r.franchise_id] = []
        by_franchise[r.franchise_id].append(r)

    # Build index: (season, week, franchise_id, player_id) -> score
    score_index: Dict[Tuple[int, int, str, str], float] = {}
    for r in all_records:
        if r.is_starter:
            score_index[(r.season, r.week, r.franchise_id, r.player_id)] = r.score

    angles: List[NarrativeAngle] = []
    seen_pairs: set = set()  # avoid duplicate duel angles (A vs B == B vs A)

    for franchise_a in sorted(by_franchise.keys()):
        opponent_id = opponent_index.get((current_season, target_week, franchise_a))
        if not opponent_id or opponent_id not in by_franchise:
            continue

        franchise_b = opponent_id

        # Avoid processing same matchup twice (A vs B and B vs A)
        matchup_key = tuple(sorted([franchise_a, franchise_b]))
        if matchup_key in seen_pairs:
            continue

        # Find all prior weeks where franchise_a and franchise_b played each other
        prior_meeting_weeks: List[Tuple[int, int]] = []  # (season, week)
        for (s, w, fid), opp in opponent_index.items():
            if fid == franchise_a and opp == franchise_b:
                if s < current_season or (s == current_season and w < target_week):
                    prior_meeting_weeks.append((s, w))

        if len(prior_meeting_weeks) < min_meetings:
            seen_pairs.add(matchup_key)
            continue

        # For each player on franchise_a this week, check duels with players on franchise_b
        for player_a in by_franchise[franchise_a]:
            for player_b in by_franchise[franchise_b]:
                duel_key = tuple(sorted([player_a.player_id, player_b.player_id]))
                if duel_key in seen_pairs:
                    continue

                # Count prior meetings where both were starters on their respective sides
                a_wins = 0
                b_wins = 0
                ties = 0
                for s, w in prior_meeting_weeks:
                    score_a = score_index.get((s, w, franchise_a, player_a.player_id))
                    score_b = score_index.get((s, w, franchise_b, player_b.player_id))
                    if score_a is not None and score_b is not None:
                        if score_a > score_b:
                            a_wins += 1
                        elif score_b > score_a:
                            b_wins += 1
                        else:
                            ties += 1

                total_meetings = a_wins + b_wins + ties
                if total_meetings < min_meetings:
                    continue

                # Report the duel — leader gets named first
                if a_wins >= b_wins:
                    leader, trailer = player_a.player_id, player_b.player_id
                    leader_wins, trailer_wins = a_wins, b_wins
                else:
                    leader, trailer = player_b.player_id, player_a.player_id
                    leader_wins, trailer_wins = b_wins, a_wins

                record_str = f"{leader_wins}-{trailer_wins}"
                if ties:
                    record_str += f"-{ties}"

                angles.append(NarrativeAngle(
                    category="PLAYER_DUEL",
                    headline=(
                        f"In the {pname(leader)} vs {pname(trailer)} duel, {pname(leader)} has outscored "
                        f"{pname(trailer)} in {leader_wins} of {total_meetings} head-to-head meetings"
                    ),
                    detail=f"Record: {record_str}.",
                    strength=1,  # MINOR per spec
                    franchise_ids=tuple(sorted([franchise_a, franchise_b])),
                ))
                seen_pairs.add(duel_key)

        seen_pairs.add(matchup_key)

    return angles


# ── Detector 15: TRADE_OUTCOME ───────────────────────────────────────


def detect_trade_outcome(
    all_records: List[_CrossSeasonRecord],
    trade_pairs: List[Tuple[_TradeMove, _TradeMove]],
    current_season: int,
    target_week: int,
    *,
    min_post_trade_weeks: int = 3,
    min_point_gap: float = 20.0,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Retrospective scoring comparison after a trade.

    For each trade pair, computes total post-trade scoring for the key
    players on each side. Reports when:
    - Both sides have at least min_post_trade_weeks of data
    - The point gap between the two sides exceeds min_point_gap

    Post-trade scoring is determined from WEEKLY_PLAYER_SCORE events:
    the first week a player appears on the receiving franchise defines
    the post-trade start.

    Constraint: retrospective only. Never frames as "who won." States numbers.
    """
    if not trade_pairs:
        return []

    angles: List[NarrativeAngle] = []

    for side_a, side_b in trade_pairs:
        # Key player for each side: the primary added player
        if not side_a.players_added or not side_b.players_added:
            continue

        # Track the most significant added player per side
        # (the first in the list — deterministic from ingestion sort)
        player_to_a = side_a.players_added[0]
        player_to_b = side_b.players_added[0]

        # Find post-trade scores for player_to_a on franchise side_a
        scores_a = [
            r for r in all_records
            if r.player_id == player_to_a and r.franchise_id == side_a.franchise_id
            and r.season == current_season and r.week <= target_week
        ]

        # Find post-trade scores for player_to_b on franchise side_b
        scores_b = [
            r for r in all_records
            if r.player_id == player_to_b and r.franchise_id == side_b.franchise_id
            and r.season == current_season and r.week <= target_week
        ]

        if len(scores_a) < min_post_trade_weeks or len(scores_b) < min_post_trade_weeks:
            continue

        total_a = round(sum(r.score for r in scores_a), 2)
        total_b = round(sum(r.score for r in scores_b), 2)
        gap = abs(total_a - total_b)

        if gap < min_point_gap:
            continue

        # Determine which side is ahead
        if total_a >= total_b:
            leader_player = player_to_a
            leader_franchise = side_a.franchise_id
            leader_total = total_a
            trailer_player = player_to_b
            trailer_franchise = side_b.franchise_id
            trailer_total = total_b
        else:
            leader_player = player_to_b
            leader_franchise = side_b.franchise_id
            leader_total = total_b
            trailer_player = player_to_a
            trailer_franchise = side_a.franchise_id
            trailer_total = total_a

        strength = 2 if gap >= 40.0 else 1  # NOTABLE at 40+ gap, MINOR otherwise

        angles.append(NarrativeAngle(
            category="TRADE_OUTCOME",
            headline=(
                f"Since the trade, {pname(leader_player)} has scored {leader_total:.1f} for "
                f"{fname(leader_franchise)} while {pname(trailer_player)} has scored {trailer_total:.1f} "
                f"for {fname(trailer_franchise)} — a {gap:.1f}-point gap"
            ),
            detail="",
            strength=strength,
            franchise_ids=tuple(sorted([side_a.franchise_id, side_b.franchise_id])),
        ))

    return angles


# ── Detector 16: THE_ONE_THAT_GOT_AWAY ──────────────────────────────


def detect_the_one_that_got_away(
    all_records: List[_CrossSeasonRecord],
    drops: List[_PlayerDrop],
    current_season: int,
    target_week: int,
    *,
    min_post_drop_points: float = 50.0,
    min_post_drop_weeks: int = 3,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect dropped players who scored well on another franchise.

    A player dropped by franchise F1 who has scored min_post_drop_points+
    over min_post_drop_weeks+ on another franchise since being dropped.

    Detection: find the player's last week on the dropping franchise, then
    sum their scores on other franchises after that point.
    """
    if not drops:
        return []

    # Build index: player_id -> list of (season, week, franchise_id, score)
    player_history: Dict[str, List[_CrossSeasonRecord]] = {}
    for r in all_records:
        if r.season == current_season and r.week <= target_week:
            if r.player_id not in player_history:
                player_history[r.player_id] = []
            player_history[r.player_id].append(r)

    angles: List[NarrativeAngle] = []
    seen_players: set = set()  # avoid duplicate angles for same player dropped multiple times

    for drop in drops:
        if drop.season != current_season:
            continue  # only current season drops for now

        player_id = drop.player_id
        dropping_franchise = drop.franchise_id

        if player_id in seen_players:
            continue

        history = player_history.get(player_id, [])
        if not history:
            continue

        # Find the last week this player appeared on the dropping franchise
        on_dropper = [r for r in history if r.franchise_id == dropping_franchise]
        if not on_dropper:
            continue
        last_week_on_dropper = max(r.week for r in on_dropper)

        # Find post-drop scores on OTHER franchises
        post_drop = [
            r for r in history
            if r.franchise_id != dropping_franchise and r.week > last_week_on_dropper
        ]

        if len(post_drop) < min_post_drop_weeks:
            continue

        total_post = round(sum(r.score for r in post_drop), 2)
        if total_post < min_post_drop_points:
            continue

        # Which franchises did they end up on?
        post_franchises = sorted({r.franchise_id for r in post_drop})
        franchise_label = fname(post_franchises[0]) if len(post_franchises) == 1 else "other teams"

        seen_players.add(player_id)
        angles.append(NarrativeAngle(
            category="THE_ONE_THAT_GOT_AWAY",
            headline=(
                f"Since being dropped by {fname(dropping_franchise)}, "
                f"{pname(player_id)} has scored {total_post:.1f} points "
                f"across {len(post_drop)} weeks for {franchise_label}"
            ),
            detail="",
            strength=1,  # MINOR per spec
            franchise_ids=(dropping_franchise,),
        ))

    return angles


# ── Detector 17: FAAB_ROI_NOTABLE ────────────────────────────────────


def detect_faab_roi(
    all_records: List[_CrossSeasonRecord],
    faab_acquisitions: List[_FaabAcquisition],
    current_season: int,
    target_week: int,
    *,
    min_roi_multiplier: float = 3.0,
    min_weeks: int = 3,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect FAAB acquisitions whose total points exceed min_roi_multiplier × bid.

    Only current-season FAAB pickups. The player must have at least
    min_weeks of scoring data on the acquiring franchise.
    """
    if not faab_acquisitions:
        return []

    angles: List[NarrativeAngle] = []

    for acq in faab_acquisitions:
        if acq.season != current_season:
            continue

        # Find all scoring weeks for this player on this franchise
        player_scores = [
            r for r in all_records
            if r.player_id == acq.player_id
            and r.franchise_id == acq.franchise_id
            and r.season == current_season
            and r.week <= target_week
        ]

        if len(player_scores) < min_weeks:
            continue

        total_pts = round(sum(r.score for r in player_scores), 2)

        if acq.bid_amount > 0 and total_pts >= acq.bid_amount * min_roi_multiplier:
            ratio = total_pts / acq.bid_amount
            starter_weeks = sum(1 for r in player_scores if r.is_starter)
            angles.append(NarrativeAngle(
                category="FAAB_ROI_NOTABLE",
                headline=(
                    f"{pname(acq.player_id)} (${acq.bid_amount:.0f} FAAB) has scored "
                    f"{total_pts:.1f} points across {starter_weeks} starts "
                    f"for {fname(acq.franchise_id)} — {ratio:.1f}x the acquisition cost"
                ),
                detail="",
                strength=2,  # NOTABLE per spec
                franchise_ids=(acq.franchise_id,),
            ))

    return angles


# ── Detector 18: FAAB_FRANCHISE_EFFICIENCY ───────────────────────────


def detect_faab_franchise_efficiency(
    all_records: List[_CrossSeasonRecord],
    faab_acquisitions: List[_FaabAcquisition],
    current_season: int,
    target_week: int,
    *,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect franchises whose FAAB pickups significantly outproduce the league average.

    Computes total scoring from FAAB acquisitions per franchise.
    Flags the franchise with the highest total if it's at least 1.5x
    the league average for FAAB pickup production.
    Requires at least 3 franchises with FAAB data to be meaningful.
    """
    if not faab_acquisitions:
        return []

    current_faab = [a for a in faab_acquisitions if a.season == current_season]
    if not current_faab:
        return []

    # Build franchise -> total FAAB pickup scoring
    franchise_faab_pts: Dict[str, float] = {}
    for acq in current_faab:
        player_scores = [
            r for r in all_records
            if r.player_id == acq.player_id
            and r.franchise_id == acq.franchise_id
            and r.season == current_season
            and r.week <= target_week
        ]
        total = sum(r.score for r in player_scores)
        franchise_faab_pts[acq.franchise_id] = franchise_faab_pts.get(acq.franchise_id, 0.0) + total

    if len(franchise_faab_pts) < 3:
        return []

    avg_pts = sum(franchise_faab_pts.values()) / len(franchise_faab_pts)
    if avg_pts < 1.0:
        return []

    # Find the leader
    best_fid = max(franchise_faab_pts, key=lambda f: franchise_faab_pts[f])
    best_pts = round(franchise_faab_pts[best_fid], 1)

    if best_pts >= avg_pts * 1.5:
        return [NarrativeAngle(
            category="FAAB_FRANCHISE_EFFICIENCY",
            headline=(
                f"{fname(best_fid)}'s FAAB pickups have produced {best_pts:.1f} total points "
                f"this season — the most in the league"
            ),
            detail=f"League average for FAAB pickup production: {avg_pts:.1f}.",
            strength=1,  # MINOR per spec
            franchise_ids=(best_fid,),
        )]

    return []


# ── Detector 19: WAIVER_DEPENDENCY ───────────────────────────────────


def detect_waiver_dependency(
    all_records: List[_CrossSeasonRecord],
    drafted_players: Dict[str, set],
    current_season: int,
    target_week: int,
    *,
    dependency_threshold: float = 0.30,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect franchises where 30%+ of scoring comes from non-drafted players.

    A player is "non-drafted" if they don't appear in the franchise's
    DRAFT_PICK events for the current season. This includes FAAB pickups,
    free agent adds, and waiver claims.

    Requires draft data to exist for the season. If no draft data,
    returns empty (silence over fabrication).
    """
    if not drafted_players:
        return []

    # Current season scoring per franchise, split by drafted/non-drafted
    franchise_totals: Dict[str, float] = {}
    franchise_nondrafted: Dict[str, float] = {}

    for r in all_records:
        if r.season != current_season or r.week > target_week:
            continue
        if not r.is_starter:
            continue

        fid = r.franchise_id
        franchise_totals[fid] = franchise_totals.get(fid, 0.0) + r.score

        drafted_set = drafted_players.get(fid, set())
        if r.player_id not in drafted_set:
            franchise_nondrafted[fid] = franchise_nondrafted.get(fid, 0.0) + r.score

    angles: List[NarrativeAngle] = []

    for fid in sorted(franchise_totals.keys()):
        total = franchise_totals[fid]
        if total < 1.0:
            continue

        nondrafted = franchise_nondrafted.get(fid, 0.0)
        ratio = nondrafted / total

        if ratio >= dependency_threshold:
            pct = round(ratio * 100)
            angles.append(NarrativeAngle(
                category="WAIVER_DEPENDENCY",
                headline=(
                    f"{pct}% of {fname(fid)}'s starter scoring this season "
                    f"came from non-drafted players"
                ),
                detail=f"Non-drafted: {nondrafted:.1f} pts of {total:.1f} total.",
                strength=1,  # MINOR per spec
                franchise_ids=(fid,),
            ))

    return angles


# ── Public API ───────────────────────────────────────────────────────


def detect_player_narrative_angles_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    tenure_map: Optional[Dict[str, int]] = None,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect all Dimension 1-5 player narrative angles for a given week.

    Dimension 1 (detectors 1-6): current-season player scores only.
    Dimension 2 (detectors 7-11): cross-season player score lookups.
    Dimension 3 (detectors 12-14): player scores cross-referenced with matchups.
    Dimension 4 (detectors 15-16): trade & transaction outcomes.
    Dimension 5 (detectors 17-19): FAAB & waiver efficiency.

    tenure_map: optional dict of franchise_id -> first_season_with_current_owner.
        Used by PLAYER_FRANCHISE_RECORD for tenure-scoped attribution.
    pname: callable resolving player_id -> display name (default: identity).
    fname: callable resolving franchise_id -> display name (default: identity).

    Returns angles sorted by strength descending then category ascending
    for determinism. Returns an empty list when no player scoring data
    exists (silence over fabrication).
    """
    season_records = _load_season_player_scores(db_path, league_id, season)

    if not season_records:
        return []

    # Check if we have any data for the target week
    target_week_data = [r for r in season_records if r.week == week]
    if not target_week_data:
        return []

    all_angles: List[NarrativeAngle] = []

    # ── Dimension 1: Short-horizon (current season only) ──

    # Detector 1: Hot streaks
    all_angles.extend(detect_player_hot_streak(season_records, week, pname=pname, fname=fname))

    # Detector 2: Cold streaks
    all_angles.extend(detect_player_cold_streak(season_records, week, pname=pname, fname=fname))

    # Detector 3: Season high
    all_angles.extend(detect_player_season_high(season_records, week, pname=pname, fname=fname))

    # Detector 4: Boom/bust
    all_angles.extend(detect_player_boom_bust(season_records, week, pname=pname, fname=fname))

    # Detector 5: Breakout
    all_angles.extend(detect_player_breakout(season_records, week, pname=pname, fname=fname))

    # Detector 6: Zero-point starters
    alltime_zeros = _load_all_seasons_starter_zeros(db_path, league_id)
    all_angles.extend(detect_zero_point_starter(
        season_records, week, alltime_zero_count=alltime_zeros, pname=pname, fname=fname,
    ))

    # ── Dimension 2: Long-horizon (cross-season) ──

    # Load all seasons lazily — only if we get this far
    all_seasons_records = _load_all_seasons_player_scores(db_path, league_id)

    if all_seasons_records:
        # Detector 7: All-time high
        all_angles.extend(detect_player_alltime_high(
            all_seasons_records, season, week, pname=pname, fname=fname,
        ))

        # Detector 8: Franchise record (tenure-scoped)
        all_angles.extend(detect_player_franchise_record(
            all_seasons_records, season, week, tenure_map=tenure_map, pname=pname, fname=fname,
        ))

        # Detector 9: Career milestone
        all_angles.extend(detect_career_milestone(
            all_seasons_records, season, week, pname=pname, fname=fname,
        ))

        # Detector 10: Player franchise tenure (week 1 only)
        all_angles.extend(detect_player_franchise_tenure(
            all_seasons_records, season, week, pname=pname, fname=fname,
        ))

        # Detector 11: Player journey (week 1 only)
        all_angles.extend(detect_player_journey(
            all_seasons_records, season, week, pname=pname, fname=fname,
        ))

        # ── Dimension 3: Player vs. Opponent (scores + matchups) ──

        opponent_index = _load_all_matchup_opponents(db_path, league_id)

        if opponent_index:
            # Detector 12: Player vs. opponent dominance
            all_angles.extend(detect_player_vs_opponent(
                all_seasons_records, season, week, opponent_index, pname=pname, fname=fname,
            ))

            # Detector 13: Revenge game
            all_angles.extend(detect_revenge_game(
                all_seasons_records, season, week, opponent_index, pname=pname, fname=fname,
            ))

            # Detector 14: Player duel
            all_angles.extend(detect_player_duel(
                all_seasons_records, season, week, opponent_index, pname=pname, fname=fname,
            ))

        # ── Dimension 4: Trade & Transaction Outcomes ──

        # Detector 15: Trade outcome
        trade_pairs = _load_season_trades(db_path, league_id, season)
        if trade_pairs:
            all_angles.extend(detect_trade_outcome(
                all_seasons_records, trade_pairs, season, week, pname=pname, fname=fname,
            ))

        # Detector 16: The one that got away
        drops = _load_season_drops(db_path, league_id, season)
        if drops:
            all_angles.extend(detect_the_one_that_got_away(
                all_seasons_records, drops, season, week, pname=pname, fname=fname,
            ))

        # ── Dimension 5: FAAB & Waiver Efficiency ──

        # Detector 17: FAAB ROI
        faab_acqs = _load_season_faab_acquisitions(db_path, league_id, season)
        if faab_acqs:
            all_angles.extend(detect_faab_roi(
                all_seasons_records, faab_acqs, season, week, pname=pname, fname=fname,
            ))

            # Detector 18: FAAB franchise efficiency
            all_angles.extend(detect_faab_franchise_efficiency(
                all_seasons_records, faab_acqs, season, week, fname=fname,
            ))

        # Detector 19: Waiver dependency
        drafted = _load_season_drafted_players(db_path, league_id, season)
        if drafted:
            all_angles.extend(detect_waiver_dependency(
                all_seasons_records, drafted, season, week, fname=fname,
            ))

    # Deterministic sort: strength desc, then category asc, then headline asc
    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))

    return all_angles


def render_player_angles_for_prompt(
    angles: List[NarrativeAngle],
    *,
    name_map: Optional[Dict[str, str]] = None,
    player_name_map: Optional[Dict[str, str]] = None,
    max_angles: int = 15,
) -> str:
    """Render player narrative angles as a text block for the creative layer prompt.

    name_map: optional dict of franchise_id -> display_name.
    player_name_map: optional dict of player_id -> display_name.
    max_angles: cap the number of angles included.
    """
    if not angles:
        return ""

    def _resolve(text: str) -> str:
        """Replace franchise and player IDs with names in angle text."""
        result = text
        if name_map:
            for fid, name in name_map.items():
                result = result.replace(fid, name)
        if player_name_map:
            for pid, name in player_name_map.items():
                result = result.replace(pid, name)
        return result

    lines: List[str] = []
    lines.append("Player narrative angles (individual performances):")

    shown = 0
    for a in angles:
        if shown >= max_angles:
            break
        strength_label = {3: "HEADLINE", 2: "NOTABLE", 1: "MINOR"}.get(a.strength, "")
        headline = _resolve(a.headline)
        detail = _resolve(a.detail) if a.detail else ""

        line = f"  [{strength_label}] {headline}"
        if detail:
            line += f" — {detail}"
        lines.append(line)
        shown += 1

    remaining = len(angles) - shown
    if remaining > 0:
        lines.append(f"  (+ {remaining} minor angles omitted)")

    return "\n".join(lines) + "\n"
