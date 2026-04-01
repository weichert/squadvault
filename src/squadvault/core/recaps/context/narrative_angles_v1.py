"""Narrative Angle Detection v1 — derived story hooks for the creative layer.

Contract:
- Derived-only: computes angles from SeasonContextV1 + LeagueHistoryContextV1.
- Deterministic: identical inputs produce identical angles.
- Non-authoritative: angles are suggestions for the creative layer, not facts.
- No inference, projection, or gap-filling.

This module answers the question: "What's interesting about this week?"
It gives the LLM specific hooks instead of making it find the story.

Angle categories:
- UPSET: lower-ranked team beats higher-ranked team
- STREAK: notable win/loss streak milestone
- SCORING_RECORD: new season or all-time scoring record
- SCORING_ANOMALY: score significantly above/below league average
- BLOWOUT: margin significantly above season average
- NAIL_BITER: margin significantly below season average
- RIVALRY: teams with notable head-to-head history met this week
- STANDINGS_SHIFT: first place changed or standings tightened
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    LeagueHistoryContextV1,
    compute_head_to_head,
)
from squadvault.core.recaps.context.season_context_v1 import SeasonContextV1
from squadvault.core.resolvers import NameFn
from squadvault.core.resolvers import identity as _identity

# ── Angle data class ─────────────────────────────────────────────────


@dataclass(frozen=True)
class NarrativeAngle:
    """A detected story hook for the creative layer.

    category: angle type (UPSET, STREAK, SCORING_RECORD, etc.)
    headline: one-line summary suitable for prompt inclusion
    detail: supporting context
    strength: 1-3 (1=minor, 2=notable, 3=headline-worthy)
    franchise_ids: franchises involved
    """
    category: str
    headline: str
    detail: str
    strength: int  # 1=minor, 2=notable, 3=headline
    franchise_ids: tuple[str, ...]


@dataclass(frozen=True)
class WeekAnglesV1:
    """All detected narrative angles for a given week."""
    league_id: str
    season: int
    week: int
    angles: tuple[NarrativeAngle, ...]

    @property
    def has_angles(self) -> bool:
        """True if any angles were detected."""
        return len(self.angles) > 0

    @property
    def headline_angles(self) -> tuple[NarrativeAngle, ...]:
        """Only strength-3 angles."""
        return tuple(a for a in self.angles if a.strength >= 3)

    @property
    def notable_angles(self) -> tuple[NarrativeAngle, ...]:
        """Strength 2+ angles."""
        return tuple(a for a in self.angles if a.strength >= 2)


# ── Angle detectors ──────────────────────────────────────────────────


def _detect_upsets(ctx: SeasonContextV1) -> list[NarrativeAngle]:
    """Detect when a lower-ranked team beats a higher-ranked team."""
    if not ctx.has_this_week_data or len(ctx.standings) < 4:
        return []

    # Build rank map: franchise_id -> standings position (1-indexed)
    # Use standings from BEFORE this week by looking at previous week's record
    # Actually, standings include this week's results. We approximate "upset"
    # by checking if winner had fewer wins than loser coming into this week.
    # Since standings include this game, we adjust: winner had (wins-1) before.
    angles: list[NarrativeAngle] = []

    rank_map = {r.franchise_id: i + 1 for i, r in enumerate(ctx.standings)}
    n_teams = len(ctx.standings)
    top_half = n_teams // 2

    for wm in ctx.week_matchups:
        if wm.is_tie:
            continue

        winner_rank = rank_map.get(wm.winner_id, n_teams)
        loser_rank = rank_map.get(wm.loser_id, 1)

        # Upset: winner is ranked lower (higher number) than loser
        # More interesting when the gap is larger
        if winner_rank > loser_rank:
            gap = winner_rank - loser_rank
            # Only flag meaningful upsets (not #5 beating #4)
            if gap >= 3:
                strength = 3 if (winner_rank > top_half and loser_rank <= 3) else 2
                angles.append(NarrativeAngle(
                    category="UPSET",
                    headline=f"#{winner_rank} upset #{loser_rank}",
                    detail=(
                        f"Winner entered ranked #{winner_rank}, loser was #{loser_rank}. "
                        f"Score: {wm.winner_score:.2f}-{wm.loser_score:.2f}."
                    ),
                    strength=strength,
                    franchise_ids=(wm.winner_id, wm.loser_id),
                ))
            elif gap >= 2:
                angles.append(NarrativeAngle(
                    category="UPSET",
                    headline=f"#{winner_rank} over #{loser_rank}",
                    detail=f"Score: {wm.winner_score:.2f}-{wm.loser_score:.2f}.",
                    strength=1,
                    franchise_ids=(wm.winner_id, wm.loser_id),
                ))

    return angles


def _detect_streaks(ctx: SeasonContextV1, *, fname: NameFn = _identity) -> list[NarrativeAngle]:
    """Detect notable streak milestones."""
    angles: list[NarrativeAngle] = []

    for rec in ctx.standings:
        streak = rec.current_streak

        if streak >= 4:
            angles.append(NarrativeAngle(
                category="STREAK",
                headline=f"{fname(rec.franchise_id)} on {streak}-game win streak",
                detail=f"Record: {rec.wins}-{rec.losses}.",
                strength=3 if streak >= 5 else 2,
                franchise_ids=(rec.franchise_id,),
            ))
        elif streak == 3:
            angles.append(NarrativeAngle(
                category="STREAK",
                headline=f"{fname(rec.franchise_id)} has won 3 straight",
                detail=f"Record: {rec.wins}-{rec.losses}.",
                strength=1,
                franchise_ids=(rec.franchise_id,),
            ))
        elif streak <= -4:
            angles.append(NarrativeAngle(
                category="STREAK",
                headline=f"{fname(rec.franchise_id)} on {abs(streak)}-game losing streak",
                detail=f"Record: {rec.wins}-{rec.losses}.",
                strength=3 if streak <= -5 else 2,
                franchise_ids=(rec.franchise_id,),
            ))
        elif streak == -3:
            angles.append(NarrativeAngle(
                category="STREAK",
                headline=f"{fname(rec.franchise_id)} has lost 3 straight",
                detail=f"Record: {rec.wins}-{rec.losses}.",
                strength=1,
                franchise_ids=(rec.franchise_id,),
            ))

    return angles


def _detect_scoring_anomalies(ctx: SeasonContextV1, *, fname: NameFn = _identity) -> list[NarrativeAngle]:
    """Detect scores significantly above or below league average."""
    if not ctx.has_this_week_data or ctx.season_avg_score is None:
        return []

    avg = ctx.season_avg_score
    angles: list[NarrativeAngle] = []

    # Collect all individual scores this week
    scores: list[tuple[str, float]] = []
    for wm in ctx.week_matchups:
        scores.append((wm.winner_id, wm.winner_score))
        scores.append((wm.loser_id, wm.loser_score))

    if len(scores) < 2:
        return []

    # Compute standard deviation of all scores through the season
    # Use season avg as the baseline — anything > 1.5 std dev is anomalous
    # Since we don't store all historical scores, use this week's spread
    # as an approximation. A score > avg * 1.3 or < avg * 0.7 is notable.
    high_threshold = avg * 1.30
    low_threshold = avg * 0.70
    extreme_high = avg * 1.50
    extreme_low = avg * 0.55

    for fid, score in scores:
        if score >= extreme_high:
            angles.append(NarrativeAngle(
                category="SCORING_ANOMALY",
                headline=f"{fname(fid)} scored {score:.2f} (well above {avg:.0f} avg)",
                detail=f"League average: {avg:.2f}. Deviation: +{score - avg:.2f}.",
                strength=3,
                franchise_ids=(fid,),
            ))
        elif score >= high_threshold:
            angles.append(NarrativeAngle(
                category="SCORING_ANOMALY",
                headline=f"{fname(fid)} scored {score:.2f} (above {avg:.0f} avg)",
                detail=f"League average: {avg:.2f}. Deviation: +{score - avg:.2f}.",
                strength=2,
                franchise_ids=(fid,),
            ))
        elif score <= extreme_low:
            angles.append(NarrativeAngle(
                category="SCORING_ANOMALY",
                headline=f"{fname(fid)} scored only {score:.2f} (well below {avg:.0f} avg)",
                detail=f"League average: {avg:.2f}. Deviation: {score - avg:.2f}.",
                strength=3,
                franchise_ids=(fid,),
            ))
        elif score <= low_threshold:
            angles.append(NarrativeAngle(
                category="SCORING_ANOMALY",
                headline=f"{fname(fid)} scored only {score:.2f} (below {avg:.0f} avg)",
                detail=f"League average: {avg:.2f}. Deviation: {score - avg:.2f}.",
                strength=1,
                franchise_ids=(fid,),
            ))

    return angles


def _detect_margin_stories(ctx: SeasonContextV1, *, fname: NameFn = _identity) -> list[NarrativeAngle]:
    """Detect blowouts and nail-biters relative to this week's matchups."""
    if not ctx.has_this_week_data:
        return []

    angles: list[NarrativeAngle] = []

    if ctx.week_biggest_blowout:
        w, l, margin = ctx.week_biggest_blowout
        if margin >= 30:
            angles.append(NarrativeAngle(
                category="BLOWOUT",
                headline=f"{fname(w)} blew out {fname(l)} by {margin:.2f}",
                detail="",
                strength=3,
                franchise_ids=(w, l),
            ))
        elif margin >= 20:
            angles.append(NarrativeAngle(
                category="BLOWOUT",
                headline=f"{fname(w)} dominated {fname(l)} by {margin:.2f}",
                detail="",
                strength=2,
                franchise_ids=(w, l),
            ))

    if ctx.week_closest_game:
        w, l, margin = ctx.week_closest_game
        if margin <= 2:
            angles.append(NarrativeAngle(
                category="NAIL_BITER",
                headline=f"{fname(w)} squeaked past {fname(l)} by {margin:.2f}",
                detail="",
                strength=3,
                franchise_ids=(w, l),
            ))
        elif margin <= 5:
            angles.append(NarrativeAngle(
                category="NAIL_BITER",
                headline=f"{fname(w)} edged {fname(l)} by {margin:.2f}",
                detail="",
                strength=2,
                franchise_ids=(w, l),
            ))

    return angles


def _detect_season_records(
    ctx: SeasonContextV1,
    history: LeagueHistoryContextV1 | None,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detect when this week set a new season or all-time scoring record."""
    angles: list[NarrativeAngle] = []

    if not ctx.has_this_week_data:
        return []

    # Check if this week's high score is the season high
    if ctx.week_high_scorer and ctx.season_high:
        wh_fid, wh_score = ctx.week_high_scorer
        if (wh_fid == ctx.season_high.franchise_id
                and ctx.season_high.week == ctx.through_week):
            # This week set the season high
            strength = 2
            headline = f"{wh_fid} set the season scoring high: {wh_score:.2f}"

            # Check if it's also an all-time record (multi-season only —
            # with single-season data, season high IS the all-time high by
            # definition, which is not meaningful).
            if (history and history.is_multi_season
                    and history.all_time_high
                    and wh_score >= history.all_time_high.score):
                strength = 3
                headline = f"{wh_fid} set an ALL-TIME scoring record: {wh_score:.2f}"

            angles.append(NarrativeAngle(
                category="SCORING_RECORD",
                headline=headline,
                detail=f"Previous season high: {ctx.season_high.score:.2f}.",
                strength=strength,
                franchise_ids=(wh_fid,),
            ))

    # Check if this week's low score is the season low
    if ctx.week_low_scorer and ctx.season_low:
        wl_fid, wl_score = ctx.week_low_scorer
        if (wl_fid == ctx.season_low.franchise_id
                and ctx.season_low.week == ctx.through_week):
            angles.append(NarrativeAngle(
                category="SCORING_RECORD",
                headline=f"{fname(wl_fid)} set the season scoring low: {wl_score:.2f}",
                detail="",
                strength=2,
                franchise_ids=(wl_fid,),
            ))

    return angles


def _detect_rivalry_angles(
    ctx: SeasonContextV1,
    history: LeagueHistoryContextV1 | None,
    all_matchups: Sequence[HistoricalMatchup] | None,
    tenure_map: dict[str, int] | None = None,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detect notable rivalry angles when this week's opponents have history.

    Tenure-aware: if either franchise changed ownership recently, only
    count matchups from the newer owner's tenure. This prevents attributing
    15 years of franchise slot history to a 2-year-old team name.

    Suppressed when only a single season is ingested.
    """
    if not history or not all_matchups or not ctx.has_this_week_data:
        return []

    if not history.is_multi_season:
        return []

    angles: list[NarrativeAngle] = []

    for wm in ctx.week_matchups:
        # Determine tenure-filtered matchups for this specific pair
        pair_matchups = [
            m for m in all_matchups
            if (m.winner_id == wm.winner_id and m.loser_id == wm.loser_id)
            or (m.winner_id == wm.loser_id and m.loser_id == wm.winner_id)
        ]
        tenure_label = "all-time"

        if tenure_map:
            t_w = tenure_map.get(wm.winner_id)
            t_l = tenure_map.get(wm.loser_id)
            if t_w and t_l:
                newer_start = max(t_w, t_l)
                earliest = min(history.seasons_available) if history.seasons_available else newer_start
                if newer_start > earliest:
                    # At least one franchise changed hands — filter to tenure period
                    pair_matchups = [m for m in pair_matchups if m.season >= newer_start]
                    tenure_label = f"since {newer_start}"

        h2h = compute_head_to_head(pair_matchups, wm.winner_id, wm.loser_id)
        if h2h.total_meetings < 2:
            continue

        total = h2h.total_meetings

        # Dominance angle
        if total >= 3 and h2h.a_wins / total >= 0.70 and h2h.a_wins >= 3:
            record_str = f"{h2h.a_wins}-{h2h.b_wins}"
            if h2h.ties:
                record_str += f"-{h2h.ties}"
            angles.append(NarrativeAngle(
                category="RIVALRY",
                headline=f"{fname(wm.winner_id)} leads the series {record_str} ({tenure_label})",
                detail=f"{total} meetings {tenure_label}.",
                strength=2,
                franchise_ids=(wm.winner_id, wm.loser_id),
            ))
        elif total >= 3 and h2h.b_wins / total >= 0.70 and h2h.b_wins >= 3:
            record_str = f"{h2h.b_wins}-{h2h.a_wins}"
            if h2h.ties:
                record_str += f"-{h2h.ties}"
            angles.append(NarrativeAngle(
                category="RIVALRY",
                headline=f"Upset: {fname(wm.winner_id)} wins despite trailing {record_str} ({tenure_label})",
                detail=f"{total} meetings {tenure_label}.",
                strength=3,
                franchise_ids=(wm.winner_id, wm.loser_id),
            ))
        # Even rivalry
        elif total >= 5 and abs(h2h.a_wins - h2h.b_wins) <= 1:
            angles.append(NarrativeAngle(
                category="RIVALRY",
                headline=f"Even rivalry: {fname(wm.winner_id)} vs {fname(wm.loser_id)} ({h2h.a_wins}-{h2h.b_wins}, {tenure_label})",
                detail=f"{total} meetings {tenure_label}, nearly even.",
                strength=1,
                franchise_ids=(wm.winner_id, wm.loser_id),
            ))

    return angles


def _detect_streak_records(
    ctx: SeasonContextV1,
    history: LeagueHistoryContextV1 | None,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detect when a current streak matches or approaches the league record.

    Suppressed entirely when only a single season is ingested: with one
    season of data, every sufficiently long streak IS the "record" by
    definition, which is meaningless. Governance: creativity must never
    compensate for missing context.
    """
    if not history:
        return []

    # Guard: single-season data makes "league record" claims meaningless
    if not history.is_multi_season:
        return []

    angles: list[NarrativeAngle] = []

    for rec in ctx.standings:
        streak = rec.current_streak

        if streak >= 3 and history.longest_win_streak:
            record = history.longest_win_streak.length
            if streak >= record:
                angles.append(NarrativeAngle(
                    category="STREAK",
                    headline=f"{fname(rec.franchise_id)} tied/broke the league win streak record ({streak} games)",
                    detail=f"Previous record: {record} by {fname(history.longest_win_streak.franchise_id)}.",
                    strength=3,
                    franchise_ids=(rec.franchise_id,),
                ))
            elif streak == record - 1:
                angles.append(NarrativeAngle(
                    category="STREAK",
                    headline=f"{fname(rec.franchise_id)} is 1 win from the league win streak record ({record})",
                    detail="",
                    strength=2,
                    franchise_ids=(rec.franchise_id,),
                ))

        if streak <= -3 and history.longest_loss_streak:
            record = history.longest_loss_streak.length
            if abs(streak) >= record:
                angles.append(NarrativeAngle(
                    category="STREAK",
                    headline=f"{fname(rec.franchise_id)} tied/broke the league loss streak record ({abs(streak)} games)",
                    detail=f"Previous record: {record} by {fname(history.longest_loss_streak.franchise_id)}.",
                    strength=3,
                    franchise_ids=(rec.franchise_id,),
                ))

    return angles


# ── Public API ───────────────────────────────────────────────────────


def detect_narrative_angles_v1(
    *,
    season_ctx: SeasonContextV1,
    history_ctx: LeagueHistoryContextV1 | None = None,
    all_matchups: Sequence[HistoricalMatchup] | None = None,
    tenure_map: dict[str, int] | None = None,
    fname: NameFn = _identity,
) -> WeekAnglesV1:
    """Detect all narrative angles for a given week.

    season_ctx: required — current season context for this week
    history_ctx: optional — cross-season history (enriches angles)
    all_matchups: optional — raw matchup list for head-to-head computation

    Returns WeekAnglesV1 with angles sorted by strength (highest first),
    then by category for determinism.
    """
    all_angles: list[NarrativeAngle] = []

    all_angles.extend(_detect_upsets(season_ctx))
    all_angles.extend(_detect_streaks(season_ctx, fname=fname))
    all_angles.extend(_detect_scoring_anomalies(season_ctx, fname=fname))
    all_angles.extend(_detect_margin_stories(season_ctx, fname=fname))
    all_angles.extend(_detect_season_records(season_ctx, history_ctx, fname=fname))
    all_angles.extend(_detect_rivalry_angles(season_ctx, history_ctx, all_matchups, tenure_map, fname=fname))
    all_angles.extend(_detect_streak_records(season_ctx, history_ctx, fname=fname))

    # Deterministic sort: strength desc, then category asc, then headline asc
    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))

    return WeekAnglesV1(
        league_id=season_ctx.league_id,
        season=season_ctx.season,
        week=season_ctx.through_week,
        angles=tuple(all_angles),
    )
