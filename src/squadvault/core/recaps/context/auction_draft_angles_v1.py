"""Auction Draft Angle Detection v1 — Dimension 6: Auction Strategy & Outcomes.

Contract:
- Derived-only: computes angles from DRAFT_PICK + WEEKLY_PLAYER_SCORE canonical events.
- Deterministic: identical inputs produce identical angles.
- Non-authoritative: angles are suggestions for the creative layer, not facts.
- Reconstructable: drop and rebuild from canonical events produces identical output.
- No inference, projection, or gap-filling.

PFL Buddies context: $200 auction budget, 17 roster spots, data from 2018-2025.

Detectors:
20. AUCTION_PRICE_VS_PRODUCTION — career/season production vs. auction price
21. AUCTION_DOLLAR_PER_POINT — most/least efficient picks by points-per-dollar
22. AUCTION_BUST — high-dollar pick dramatically underperforming
23. AUCTION_BUDGET_ALLOCATION — how a franchise distributed their budget
24. AUCTION_POSITIONAL_SPENDING — franchise spending per position group
25. AUCTION_STRATEGY_CONSISTENCY — year-over-year spending pattern
26. AUCTION_LEAGUE_INFLATION — league-wide positional price trends
27. AUCTION_DRAFT_TO_FAAB_PIPELINE — combined draft+FAAB investment vs. production
28. AUCTION_MOST_EXPENSIVE_PLAYER_HISTORY — most expensive pick per position all-time

Reuses the NarrativeAngle dataclass from narrative_angles_v1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

from squadvault.core.recaps.context.narrative_angles_v1 import NarrativeAngle
from squadvault.core.storage.session import DatabaseSession

from squadvault.core.resolvers import NameFn, identity as _identity


# ── Data structures ──────────────────────────────────────────────────


@dataclass(frozen=True)
class _AuctionPick:
    """A single auction draft pick with position context."""
    season: int
    franchise_id: str
    player_id: str
    bid_amount: float
    position: str  # from player_directory; "" if unknown


@dataclass(frozen=True)
class _PlayerSeasonScoring:
    """Aggregated scoring for a player on a franchise in a season."""
    season: int
    franchise_id: str
    player_id: str
    total_points: float
    weeks_played: int
    starter_weeks: int


# ── Data loading ─────────────────────────────────────────────────────


def _load_all_auction_picks(
    db_path: str,
    league_id: str,
) -> List[_AuctionPick]:
    """Load all DRAFT_PICK events across all seasons with position enrichment.

    Joins with player_directory to attach position data.
    Returns picks sorted by (season, franchise_id, player_id) for determinism.
    """
    picks: List[_AuctionPick] = []

    # Load position lookup
    positions: Dict[Tuple[int, str], str] = {}  # (season, player_id) -> position
    with DatabaseSession(db_path) as con:
        pos_rows = con.execute(
            """SELECT season, player_id, position FROM player_directory
               WHERE league_id = ?""",
            (str(league_id),),
        ).fetchall()
    for row in pos_rows:
        try:
            positions[(int(row[0]), str(row[1]).strip())] = str(row[2] or "").strip()
        except (ValueError, TypeError):
            continue

    # Load draft picks
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT season, payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'DRAFT_PICK'
               ORDER BY season ASC, payload_json ASC""",
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

        franchise_id = str(p.get("franchise_id", "")).strip()
        player_id = str(p.get("player_id", "")).strip()
        if not franchise_id or not player_id:
            continue

        try:
            bid_amount = float(p.get("bid_amount", 0))
        except (ValueError, TypeError):
            bid_amount = 0.0
        if bid_amount <= 0:
            continue

        position = positions.get((season, player_id), "")

        picks.append(_AuctionPick(
            season=season,
            franchise_id=franchise_id,
            player_id=player_id,
            bid_amount=bid_amount,
            position=position,
        ))

    picks.sort(key=lambda pk: (pk.season, pk.franchise_id, pk.player_id))
    return picks


def _load_player_season_scoring(
    db_path: str,
    league_id: str,
    *,
    current_season: int = 0,
    target_week: int = 99,
) -> Dict[Tuple[int, str, str], _PlayerSeasonScoring]:
    """Load aggregated player scoring per (season, franchise_id, player_id).

    When current_season and target_week are specified, scores for the
    current season are filtered to week <= target_week. Prior seasons
    use full data (they're complete). This ensures angles reflect
    week-appropriate stats instead of full-season retrospective numbers.

    Returns dict keyed by (season, franchise_id, player_id).
    """
    # Accumulate from WEEKLY_PLAYER_SCORE events
    totals: Dict[Tuple[int, str, str], List[Tuple[float, bool]]] = {}

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT season, payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'""",
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

        # Week-scope the current season
        if current_season and season == current_season:
            try:
                week = int(p.get("week", 99))
            except (ValueError, TypeError):
                week = 99
            if week > target_week:
                continue

        franchise_id = str(p.get("franchise_id", "")).strip()
        player_id = str(p.get("player_id", "")).strip()
        if not franchise_id or not player_id:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0

        is_starter = bool(p.get("is_starter", False))

        key = (season, franchise_id, player_id)
        if key not in totals:
            totals[key] = []
        totals[key].append((score, is_starter))

    result: Dict[Tuple[int, str, str], _PlayerSeasonScoring] = {}
    for (season, fid, pid), entries in totals.items():
        result[(season, fid, pid)] = _PlayerSeasonScoring(
            season=season,
            franchise_id=fid,
            player_id=pid,
            total_points=round(sum(s for s, _ in entries), 2),
            weeks_played=len(entries),
            starter_weeks=sum(1 for _, is_st in entries if is_st),
        )

    return result


def _load_season_faab_by_position(
    db_path: str,
    league_id: str,
    season: int,
) -> Dict[Tuple[str, str], float]:
    """Load FAAB spending per (franchise_id, position) for a season.

    Returns dict: (franchise_id, position) -> total FAAB bid amount.
    Uses player_directory for position lookup.
    """
    # Position lookup
    positions: Dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        pos_rows = con.execute(
            """SELECT player_id, position FROM player_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in pos_rows:
        positions[str(row[0]).strip()] = str(row[1] or "").strip()

    # FAAB awards
    spending: Dict[Tuple[str, str], float] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'""",
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
        if not player_id:
            added = p.get("players_added_ids")
            if isinstance(added, str) and added.strip():
                player_id = added.split(",")[0].strip()

        if not franchise_id or not player_id:
            continue

        try:
            bid = float(p.get("bid_amount", 0))
        except (ValueError, TypeError):
            continue
        if bid <= 0:
            continue

        pos = positions.get(player_id, "")
        key = (franchise_id, pos)
        spending[key] = spending.get(key, 0.0) + bid

    return spending


# ── Detector 20: AUCTION_PRICE_VS_PRODUCTION ─────────────────────────


def detect_auction_price_vs_production(
    picks: List[_AuctionPick],
    scoring: Dict[Tuple[int, str, str], _PlayerSeasonScoring],
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Find the most productive auction investment in league history.

    Sums all-time scoring for a drafted player on the drafting franchise,
    then computes career points-per-dollar. Reports the all-time leader.
    Requires at least 2 seasons of draft data.
    """
    seasons = {pk.season for pk in picks}
    if len(seasons) < 2:
        return []

    # Career scoring per draft pick on the drafting franchise
    career: Dict[Tuple[str, str, int], float] = {}  # (franchise, player, draft_season) -> total
    for pk in picks:
        total = 0.0
        for (s, fid, pid), sc in scoring.items():
            if fid == pk.franchise_id and pid == pk.player_id and s >= pk.season:
                total += sc.total_points
        if total > 0:
            career[(pk.franchise_id, pk.player_id, pk.season)] = total

    if not career:
        return []

    # Find best career points-per-dollar
    best_key = None
    best_ppd = 0.0
    best_total = 0.0
    best_bid = 0.0
    for pk in picks:
        key = (pk.franchise_id, pk.player_id, pk.season)
        total = career.get(key, 0.0)
        if total > 0 and pk.bid_amount > 0:
            ppd = total / pk.bid_amount
            if ppd > best_ppd:
                best_ppd = ppd
                best_key = key
                best_total = total
                best_bid = pk.bid_amount

    if best_key is None:
        return []

    fid, pid, draft_season = best_key
    return [NarrativeAngle(
        category="AUCTION_PRICE_VS_PRODUCTION",
        headline=(
            f"{fname(fid)} spent ${best_bid:.0f} on {pname(pid)} in {draft_season} — "
            f"{best_total:.0f} career points, the most productive auction "
            f"investment in league history"
        ),
        detail=f"{best_ppd:.1f} points per dollar.",
        strength=2,  # NOTABLE
        franchise_ids=(fid,),
    )]


# ── Detector 21: AUCTION_DOLLAR_PER_POINT ────────────────────────────


def detect_auction_dollar_per_point(
    picks: List[_AuctionPick],
    scoring: Dict[Tuple[int, str, str], _PlayerSeasonScoring],
    current_season: int,
    *,
    min_weeks: int = 3,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Find the best and worst value picks of the current draft by points-per-dollar."""
    season_picks = [pk for pk in picks if pk.season == current_season]
    if len(season_picks) < 3:
        return []

    efficiencies: List[Tuple[_AuctionPick, float, float]] = []  # (pick, ppd, total)
    for pk in season_picks:
        sc = scoring.get((current_season, pk.franchise_id, pk.player_id))
        if sc is None or sc.weeks_played < min_weeks:
            continue
        ppd = sc.total_points / pk.bid_amount
        efficiencies.append((pk, ppd, sc.total_points))

    if len(efficiencies) < 3:
        return []

    efficiencies.sort(key=lambda x: (-x[1], x[0].franchise_id, x[0].player_id))
    angles: List[NarrativeAngle] = []

    # Best value
    best_pk, best_ppd, best_total = efficiencies[0]
    angles.append(NarrativeAngle(
        category="AUCTION_DOLLAR_PER_POINT",
        headline=(
            f"{fname(best_pk.franchise_id)}'s ${best_pk.bid_amount:.0f} pick of "
            f"{pname(best_pk.player_id)} has produced {best_ppd:.1f} points per dollar "
            f"— the best value of the {current_season} draft"
        ),
        detail=f"{best_total:.1f} total points.",
        strength=1,  # MINOR
        franchise_ids=(best_pk.franchise_id,),
    ))

    return angles


# ── Detector 22: AUCTION_BUST ────────────────────────────────────────


def detect_auction_bust(
    picks: List[_AuctionPick],
    scoring: Dict[Tuple[int, str, str], _PlayerSeasonScoring],
    current_season: int,
    *,
    min_weeks: int = 4,
    avg_threshold_ratio: float = 0.5,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect high-dollar auction picks who dramatically underperformed.

    Flags top-3 picks per franchise (by bid) averaging below half the
    league starter average.
    """
    season_picks = [pk for pk in picks if pk.season == current_season]
    if not season_picks:
        return []

    # League starter average per week
    all_starter_scores: List[float] = []
    for (s, _, _), sc in scoring.items():
        if s == current_season and sc.starter_weeks > 0:
            all_starter_scores.append(sc.total_points / sc.starter_weeks)
    if not all_starter_scores:
        return []
    league_avg = sum(all_starter_scores) / len(all_starter_scores)
    if league_avg < 1.0:
        return []

    # Group picks by franchise, take top 3 by bid
    by_franchise: Dict[str, List[_AuctionPick]] = {}
    for pk in season_picks:
        if pk.franchise_id not in by_franchise:
            by_franchise[pk.franchise_id] = []
        by_franchise[pk.franchise_id].append(pk)

    angles: List[NarrativeAngle] = []

    for fid in sorted(by_franchise.keys()):
        top_picks = sorted(by_franchise[fid], key=lambda p: -p.bid_amount)[:3]
        for pk in top_picks:
            sc_or_none = scoring.get((current_season, pk.franchise_id, pk.player_id))
            if sc_or_none is None or sc_or_none.starter_weeks < min_weeks:
                continue
            sc = sc_or_none
            player_avg = sc.total_points / sc.starter_weeks
            if player_avg < league_avg * avg_threshold_ratio:
                angles.append(NarrativeAngle(
                    category="AUCTION_BUST",
                    headline=(
                        f"{fname(fid)} spent ${pk.bid_amount:.0f} on {pname(pk.player_id)} "
                        f"— averaging just {player_avg:.1f} points through "
                        f"{sc.starter_weeks} starts"
                    ),
                    detail=f"League starter average: {league_avg:.1f}.",
                    strength=2,  # NOTABLE
                    franchise_ids=(fid,),
                ))

    return angles


# ── Detector 23: AUCTION_BUDGET_ALLOCATION ───────────────────────────


def detect_auction_budget_allocation(
    picks: List[_AuctionPick],
    current_season: int,
    *,
    budget: float = 200.0,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Analyze how franchises distributed their auction budget.

    Reports the most concentrated (stars-and-scrubs) and most balanced strategies.
    """
    season_picks = [pk for pk in picks if pk.season == current_season]
    if not season_picks:
        return []

    by_franchise: Dict[str, List[float]] = {}
    for pk in season_picks:
        if pk.franchise_id not in by_franchise:
            by_franchise[pk.franchise_id] = []
        by_franchise[pk.franchise_id].append(pk.bid_amount)

    if len(by_franchise) < 3:
        return []

    # Compute max bid and spread per franchise
    stats: List[Tuple[str, float, float, float]] = []  # (fid, max_bid, min_bid, std)
    for fid in sorted(by_franchise.keys()):
        bids = by_franchise[fid]
        if not bids:
            continue
        max_b = max(bids)
        min_b = min(bids)
        avg_b = sum(bids) / len(bids)
        variance = sum((b - avg_b) ** 2 for b in bids) / len(bids)
        std = variance ** 0.5
        stats.append((fid, max_b, min_b, std))

    if not stats:
        return []

    # Most concentrated (highest std dev = stars-and-scrubs)
    stats_by_std = sorted(stats, key=lambda s: -s[3])
    most_concentrated = stats_by_std[0]
    most_balanced = stats_by_std[-1]

    angles: List[NarrativeAngle] = []

    if most_concentrated[3] > most_balanced[3] * 1.5:
        fid, max_b, min_b, std = most_concentrated
        angles.append(NarrativeAngle(
            category="AUCTION_BUDGET_ALLOCATION",
            headline=(
                f"{fname(fid)} ran the most concentrated draft: "
                f"${max_b:.0f} top pick, ${min_b:.0f} cheapest"
            ),
            detail="",
            strength=1,  # MINOR
            franchise_ids=(fid,),
        ))

        fid2, max_b2, min_b2, std2 = most_balanced
        angles.append(NarrativeAngle(
            category="AUCTION_BUDGET_ALLOCATION",
            headline=(
                f"{fname(fid2)} ran the most balanced draft: "
                f"${max_b2:.0f} top pick, ${min_b2:.0f} cheapest"
            ),
            detail="",
            strength=1,  # MINOR
            franchise_ids=(fid2,),
        ))

    return angles


# ── Detector 24: AUCTION_POSITIONAL_SPENDING ─────────────────────────


def detect_auction_positional_spending(
    picks: List[_AuctionPick],
    current_season: int,
    *,
    budget: float = 200.0,
    min_pct: float = 0.35,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect franchises with extreme positional spending in their draft."""
    season_picks = [pk for pk in picks if pk.season == current_season and pk.position]
    if not season_picks:
        return []

    # Per franchise, per position group spending
    spending: Dict[str, Dict[str, float]] = {}  # fid -> {pos -> total}
    franchise_total: Dict[str, float] = {}
    for pk in season_picks:
        if pk.franchise_id not in spending:
            spending[pk.franchise_id] = {}
        pos = pk.position
        spending[pk.franchise_id][pos] = spending[pk.franchise_id].get(pos, 0.0) + pk.bid_amount
        franchise_total[pk.franchise_id] = franchise_total.get(pk.franchise_id, 0.0) + pk.bid_amount

    angles: List[NarrativeAngle] = []

    for fid in sorted(spending.keys()):
        total = franchise_total.get(fid, 0.0)
        if total < 1.0:
            continue
        for pos in sorted(spending[fid].keys()):
            pos_total = spending[fid][pos]
            pct = pos_total / total
            if pct >= min_pct:
                angles.append(NarrativeAngle(
                    category="AUCTION_POSITIONAL_SPENDING",
                    headline=(
                        f"{fname(fid)} spent {pct:.0%} of their draft budget on {pos}s"
                    ),
                    detail=f"${pos_total:.0f} of ${total:.0f} total.",
                    strength=1,  # MINOR
                    franchise_ids=(fid,),
                ))

    return angles


# ── Detector 25: AUCTION_STRATEGY_CONSISTENCY ────────────────────────


def detect_auction_strategy_consistency(
    picks: List[_AuctionPick],
    current_season: int,
    *,
    min_seasons: int = 3,
    consistency_pct: float = 0.35,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect franchises with consistent positional spending across seasons."""
    if not picks:
        return []

    # Per franchise, per season, per position: spending percentage
    # fid -> season -> pos -> pct
    franchise_seasons: Dict[str, Dict[int, Dict[str, float]]] = {}
    for pk in picks:
        if not pk.position:
            continue
        if pk.franchise_id not in franchise_seasons:
            franchise_seasons[pk.franchise_id] = {}
        if pk.season not in franchise_seasons[pk.franchise_id]:
            franchise_seasons[pk.franchise_id][pk.season] = {}
        pos_map = franchise_seasons[pk.franchise_id][pk.season]
        pos_map[pk.position] = pos_map.get(pk.position, 0.0) + pk.bid_amount

    angles: List[NarrativeAngle] = []

    for fid in sorted(franchise_seasons.keys()):
        seasons_data = franchise_seasons[fid]
        if len(seasons_data) < min_seasons:
            continue

        # Convert to percentages
        for s in seasons_data:
            total = sum(seasons_data[s].values())
            if total > 0:
                for pos in seasons_data[s]:
                    seasons_data[s][pos] = seasons_data[s][pos] / total

        # For each position, count seasons where spending >= consistency_pct
        all_positions: set = set()
        for s in seasons_data:
            all_positions.update(seasons_data[s].keys())

        for pos in sorted(all_positions):
            heavy_seasons = sum(
                1 for s in seasons_data
                if seasons_data[s].get(pos, 0) >= consistency_pct
            )
            total_seasons = len(seasons_data)
            if heavy_seasons >= min_seasons and heavy_seasons >= total_seasons * 0.6:
                angles.append(NarrativeAngle(
                    category="AUCTION_STRATEGY_CONSISTENCY",
                    headline=(
                        f"{fname(fid)} has spent {consistency_pct:.0%}+ of their budget "
                        f"on {pos}s in {heavy_seasons} of {total_seasons} drafts"
                    ),
                    detail="",
                    strength=1,  # MINOR
                    franchise_ids=(fid,),
                ))

    return angles


# ── Detector 26: AUCTION_LEAGUE_INFLATION ────────────────────────────


def detect_auction_league_inflation(
    picks: List[_AuctionPick],
    current_season: int,
    *,
    min_seasons: int = 3,
) -> List[NarrativeAngle]:
    """Detect league-wide positional price trends across draft years."""
    if not picks:
        return []

    # Average bid per position per season
    pos_season_bids: Dict[str, Dict[int, List[float]]] = {}  # pos -> season -> [bids]
    for pk in picks:
        if not pk.position:
            continue
        if pk.position not in pos_season_bids:
            pos_season_bids[pk.position] = {}
        if pk.season not in pos_season_bids[pk.position]:
            pos_season_bids[pk.position][pk.season] = []
        pos_season_bids[pk.position][pk.season].append(pk.bid_amount)

    angles: List[NarrativeAngle] = []

    for pos in sorted(pos_season_bids.keys()):
        season_avgs = pos_season_bids[pos]
        seasons = sorted(season_avgs.keys())
        if len(seasons) < min_seasons:
            continue

        earliest = seasons[0]
        latest = seasons[-1]
        avg_earliest = sum(season_avgs[earliest]) / len(season_avgs[earliest])
        avg_latest = sum(season_avgs[latest]) / len(season_avgs[latest])

        if avg_earliest < 1.0:
            continue

        change_pct = (avg_latest - avg_earliest) / avg_earliest
        if abs(change_pct) >= 0.30:  # 30%+ change
            direction = "risen" if change_pct > 0 else "fallen"
            angles.append(NarrativeAngle(
                category="AUCTION_LEAGUE_INFLATION",
                headline=(
                    f"Average {pos} price has {direction} from "
                    f"${avg_earliest:.0f} in {earliest} to ${avg_latest:.0f} in {latest}"
                ),
                detail=f"{abs(change_pct):.0%} change across {len(seasons)} drafts.",
                strength=1,  # MINOR
                franchise_ids=(),
            ))

    return angles


# ── Detector 27: AUCTION_DRAFT_TO_FAAB_PIPELINE ─────────────────────


def detect_auction_draft_to_faab_pipeline(
    picks: List[_AuctionPick],
    scoring: Dict[Tuple[int, str, str], _PlayerSeasonScoring],
    faab_by_position: Dict[Tuple[str, str], float],
    current_season: int,
    *,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Total investment (draft + FAAB) vs. production per position per franchise."""
    season_picks = [pk for pk in picks if pk.season == current_season and pk.position]
    if not season_picks:
        return []

    # Draft spending per (franchise, position)
    draft_spend: Dict[Tuple[str, str], float] = {}
    for pk in season_picks:
        key = (pk.franchise_id, pk.position)
        draft_spend[key] = draft_spend.get(key, 0.0) + pk.bid_amount

    # Production per (franchise, position) — sum player scoring by position
    positions: Dict[str, str] = {}
    for pk in picks:
        positions[pk.player_id] = pk.position

    pos_production: Dict[Tuple[str, str], float] = {}
    for (s, fid, pid), sc in scoring.items():
        if s == current_season and pid in positions and positions[pid]:
            key = (fid, positions[pid])
            pos_production[key] = pos_production.get(key, 0.0) + sc.total_points

    angles: List[NarrativeAngle] = []

    # Find the most notable combined investment
    all_keys = set(draft_spend.keys()) | set(faab_by_position.keys())
    best_key = None
    best_total_invest = 0.0
    best_production = 0.0

    for key in all_keys:
        fid, pos = key
        d_spend = draft_spend.get(key, 0.0)
        f_spend = faab_by_position.get(key, 0.0)
        total_invest = d_spend + f_spend
        production = pos_production.get(key, 0.0)

        if total_invest > best_total_invest and production > 0:
            best_total_invest = total_invest
            best_production = production
            best_key = key

    if best_key and best_total_invest >= 30.0:
        fid, pos = best_key
        d_spend = draft_spend.get(best_key, 0.0)
        f_spend = faab_by_position.get(best_key, 0.0)
        angles.append(NarrativeAngle(
            category="AUCTION_DRAFT_TO_FAAB_PIPELINE",
            headline=(
                f"{fname(fid)} spent ${d_spend:.0f} at the draft and ${f_spend:.0f} in FAAB "
                f"on {pos} — ${best_total_invest:.0f} total investment has produced "
                f"{best_production:.0f} points"
            ),
            detail="",
            strength=1,  # MINOR
            franchise_ids=(fid,),
        ))

    return angles


# ── Detector 28: AUCTION_MOST_EXPENSIVE_PLAYER_HISTORY ───────────────


def detect_auction_most_expensive_history(
    picks: List[_AuctionPick],
    *,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Find the most expensive player at each position across all auction drafts.

    Reports the all-time record bid per position. Requires 2+ seasons.
    """
    seasons = {pk.season for pk in picks}
    if len(seasons) < 2:
        return []

    # Max bid per position across all drafts
    pos_max: Dict[str, Tuple[_AuctionPick, float]] = {}  # pos -> (pick, bid)
    for pk in picks:
        if not pk.position:
            continue
        current = pos_max.get(pk.position)
        if current is None or pk.bid_amount > current[1]:
            pos_max[pk.position] = (pk, pk.bid_amount)

    # Overall most expensive single pick
    if not pos_max:
        return []

    overall_best = max(pos_max.values(), key=lambda x: x[1])
    pk, bid = overall_best

    return [NarrativeAngle(
        category="AUCTION_MOST_EXPENSIVE_HISTORY",
        headline=(
            f"{fname(pk.franchise_id)}'s ${bid:.0f} on {pname(pk.player_id)} in {pk.season} "
            f"is the most ever spent on a single player in a league auction"
        ),
        detail=f"Position: {pk.position}.",
        strength=1,  # MINOR
        franchise_ids=(pk.franchise_id,),
    )]


# ── Public API ───────────────────────────────────────────────────────


def detect_auction_draft_angles_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> List[NarrativeAngle]:
    """Detect all Dimension 6 auction draft angles for a given week.

    Loads DRAFT_PICK and WEEKLY_PLAYER_SCORE canonical events, enriches
    with player_directory positions, runs all 9 detectors, and returns
    angles sorted by strength descending then category ascending.

    Only surfaces auction angles once per season (week 1) for detectors
    that are draft-day observations (budget, positional, consistency,
    inflation, history). Production-based detectors (price vs production,
    dollar per point, bust, pipeline) surface any week with sufficient data.

    pname: callable resolving player_id -> display name (default: identity).
    fname: callable resolving franchise_id -> display name (default: identity).

    Returns an empty list when no auction data exists.
    """
    all_picks = _load_all_auction_picks(db_path, league_id)
    if not all_picks:
        return []

    scoring = _load_player_season_scoring(
        db_path, league_id,
        current_season=season, target_week=week,
    )

    all_angles: List[NarrativeAngle] = []

    # Production-based detectors (any week)
    all_angles.extend(detect_auction_price_vs_production(all_picks, scoring, pname=pname, fname=fname))
    all_angles.extend(detect_auction_dollar_per_point(all_picks, scoring, season, pname=pname, fname=fname))
    all_angles.extend(detect_auction_bust(all_picks, scoring, season, pname=pname, fname=fname))

    # Draft-day observations (week 1 only to avoid repetition)
    if week == 1:
        all_angles.extend(detect_auction_budget_allocation(all_picks, season, fname=fname))
        all_angles.extend(detect_auction_positional_spending(all_picks, season, fname=fname))
        all_angles.extend(detect_auction_strategy_consistency(all_picks, season, fname=fname))
        all_angles.extend(detect_auction_league_inflation(all_picks, season))
        all_angles.extend(detect_auction_most_expensive_history(all_picks, pname=pname, fname=fname))

        # Pipeline needs FAAB data
        faab_by_pos = _load_season_faab_by_position(db_path, league_id, season)
        all_angles.extend(detect_auction_draft_to_faab_pipeline(
            all_picks, scoring, faab_by_pos, season, fname=fname,
        ))

    # Deterministic sort
    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))

    return all_angles
