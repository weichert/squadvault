"""Season Context Derivation v1 — derived narrative context from canonical events.

Contract:
- Derived-only: reads canonical events, never writes back into memory.
- Deterministic: identical inputs produce identical outputs.
- Non-authoritative: context is for creative layer consumption, not fact.
- Reconstructable: can be dropped and rebuilt from canonical events.

This module computes standings, streaks, and scoring context from
WEEKLY_MATCHUP_RESULT canonical events. It is the primary engine upgrade
that gives the creative layer enough material to produce Colbert/Fallon
caliber commentary instead of dry factual summaries.

Governance:
- Defers to Canonical Operating Constitution
- Aligned with PLAYER_WEEK_CONTEXT contract pattern (derived, non-authoritative)
- No inference, projection, or gap-filling
- Missing data stays missing
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from squadvault.core.storage.session import DatabaseSession


# ── Data classes (all frozen for determinism) ────────────────────────


@dataclass(frozen=True)
class MatchupResult:
    """A single matchup result from a canonical event."""
    week: int
    winner_id: str
    loser_id: str
    winner_score: float
    loser_score: float
    is_tie: bool
    margin: float  # always >= 0


@dataclass(frozen=True)
class TeamRecord:
    """Win-loss-tie record for a team through a given week."""
    franchise_id: str
    wins: int
    losses: int
    ties: int
    points_for: float       # total points scored
    points_against: float   # total points allowed
    current_streak: int     # positive = win streak, negative = loss streak, 0 = no games

    @property
    def games_played(self) -> int:
        return self.wins + self.losses + self.ties

    @property
    def win_pct(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played


@dataclass(frozen=True)
class WeekMatchupContext:
    """Context for a single matchup this week — richer than a bare bullet."""
    winner_id: str
    loser_id: str
    winner_score: float
    loser_score: float
    margin: float
    is_tie: bool
    winner_record_after: Optional[TeamRecord]  # record INCLUDING this game
    loser_record_after: Optional[TeamRecord]


@dataclass(frozen=True)
class ScoringMilestone:
    """A notable scoring fact (season high, low, etc.)."""
    franchise_id: str
    week: int
    score: float
    label: str  # e.g. "season_high", "season_low"


@dataclass(frozen=True)
class SeasonContextV1:
    """Full derived season context for a given week.

    This is the payload that feeds the creative layer prompt.
    All fields are derived from canonical WEEKLY_MATCHUP_RESULT events.
    """
    league_id: str
    season: int
    through_week: int  # context computed through (and including) this week

    # Standings ordered by: wins desc, then points_for desc (tiebreaker)
    standings: Tuple[TeamRecord, ...]

    # This week's matchups with context
    week_matchups: Tuple[WeekMatchupContext, ...]

    # This week's scoring highlights
    week_high_scorer: Optional[Tuple[str, float]]     # (franchise_id, score)
    week_low_scorer: Optional[Tuple[str, float]]
    week_closest_game: Optional[Tuple[str, str, float]]  # (winner, loser, margin)
    week_biggest_blowout: Optional[Tuple[str, str, float]]

    # Season-level milestones (through this week)
    season_high: Optional[ScoringMilestone]
    season_low: Optional[ScoringMilestone]
    season_avg_score: Optional[float]

    # Metadata
    total_matchups_through_week: int
    matchups_this_week: int

    @property
    def has_matchup_data(self) -> bool:
        return self.total_matchups_through_week > 0

    @property
    def has_this_week_data(self) -> bool:
        return self.matchups_this_week > 0


# ── Empty context (silence over fabrication) ─────────────────────────


def _empty_context(league_id: str, season: int, week: int) -> SeasonContextV1:
    """Return empty context when no matchup data exists."""
    return SeasonContextV1(
        league_id=league_id,
        season=season,
        through_week=week,
        standings=(),
        week_matchups=(),
        week_high_scorer=None,
        week_low_scorer=None,
        week_closest_game=None,
        week_biggest_blowout=None,
        season_high=None,
        season_low=None,
        season_avg_score=None,
        total_matchups_through_week=0,
        matchups_this_week=0,
    )


# ── Core derivation ─────────────────────────────────────────────────


def _parse_matchup(payload_json: str, fallback_week: int) -> Optional[MatchupResult]:
    """Parse a WEEKLY_MATCHUP_RESULT payload into a MatchupResult.

    Returns None if the payload is malformed or missing required fields.
    Silence over fabrication: we skip what we can't parse cleanly.
    """
    try:
        p = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
    except (ValueError, TypeError):
        return None

    if not isinstance(p, dict):
        return None

    winner_id = p.get("winner_franchise_id") or p.get("winner_team_id")
    loser_id = p.get("loser_franchise_id") or p.get("loser_team_id")

    if not winner_id or not loser_id:
        return None

    try:
        winner_score = float(p.get("winner_score", 0))
        loser_score = float(p.get("loser_score", 0))
    except (ValueError, TypeError):
        return None

    week = fallback_week
    if "week" in p:
        try:
            week = int(p["week"])
        except (ValueError, TypeError):
            pass

    is_tie = bool(p.get("is_tie", False))
    margin = abs(winner_score - loser_score)

    return MatchupResult(
        week=week,
        winner_id=str(winner_id).strip(),
        loser_id=str(loser_id).strip(),
        winner_score=winner_score,
        loser_score=loser_score,
        is_tie=is_tie,
        margin=round(margin, 2),
    )


def _load_matchups(
    db_path: str,
    league_id: str,
    season: int,
) -> List[MatchupResult]:
    """Load all WEEKLY_MATCHUP_RESULT events from canonical_events.

    Returns parsed MatchupResult list sorted by (week, winner_id, loser_id).
    """
    matchups: List[MatchupResult] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        m = _parse_matchup(row[0], fallback_week=0)
        if m is not None:
            matchups.append(m)

    # Deterministic sort
    matchups.sort(key=lambda m: (m.week, m.winner_id, m.loser_id))
    return matchups


def _compute_records(
    matchups: Sequence[MatchupResult],
    through_week: int,
) -> Dict[str, TeamRecord]:
    """Compute W-L-T records and streaks for all teams through a given week.

    Streak logic: walk games in chronological order per team.
    Positive = consecutive wins, negative = consecutive losses.
    Ties reset the streak to 0.
    """
    # Accumulators per franchise
    wins: Dict[str, int] = {}
    losses: Dict[str, int] = {}
    ties: Dict[str, int] = {}
    pf: Dict[str, float] = {}
    pa: Dict[str, float] = {}
    # Game log per franchise for streak computation: list of 'W', 'L', 'T'
    game_log: Dict[str, List[str]] = {}

    for m in matchups:
        if m.week > through_week:
            continue

        for fid in (m.winner_id, m.loser_id):
            wins.setdefault(fid, 0)
            losses.setdefault(fid, 0)
            ties.setdefault(fid, 0)
            pf.setdefault(fid, 0.0)
            pa.setdefault(fid, 0.0)
            game_log.setdefault(fid, [])

        if m.is_tie:
            ties[m.winner_id] = ties.get(m.winner_id, 0) + 1
            ties[m.loser_id] = ties.get(m.loser_id, 0) + 1
            pf[m.winner_id] += m.winner_score
            pa[m.winner_id] += m.loser_score
            pf[m.loser_id] += m.loser_score
            pa[m.loser_id] += m.winner_score
            game_log[m.winner_id].append("T")
            game_log[m.loser_id].append("T")
        else:
            wins[m.winner_id] = wins.get(m.winner_id, 0) + 1
            losses[m.loser_id] = losses.get(m.loser_id, 0) + 1
            pf[m.winner_id] += m.winner_score
            pa[m.winner_id] += m.loser_score
            pf[m.loser_id] += m.loser_score
            pa[m.loser_id] += m.winner_score
            game_log[m.winner_id].append("W")
            game_log[m.loser_id].append("L")

    # Compute streaks from game logs
    def _streak(log: List[str]) -> int:
        if not log:
            return 0
        last = log[-1]
        if last == "T":
            return 0
        count = 0
        for result in reversed(log):
            if result == last:
                count += 1
            else:
                break
        return count if last == "W" else -count

    records: Dict[str, TeamRecord] = {}
    for fid in wins:
        records[fid] = TeamRecord(
            franchise_id=fid,
            wins=wins.get(fid, 0),
            losses=losses.get(fid, 0),
            ties=ties.get(fid, 0),
            points_for=round(pf.get(fid, 0.0), 2),
            points_against=round(pa.get(fid, 0.0), 2),
            current_streak=_streak(game_log.get(fid, [])),
        )

    return records


def _week_scoring_highlights(
    week_matchups: Sequence[MatchupResult],
) -> Tuple[
    Optional[Tuple[str, float]],  # high scorer
    Optional[Tuple[str, float]],  # low scorer
    Optional[Tuple[str, str, float]],  # closest game
    Optional[Tuple[str, str, float]],  # biggest blowout
]:
    """Derive this week's scoring highlights from matchup results."""
    if not week_matchups:
        return None, None, None, None

    # Collect all individual scores this week
    scores: List[Tuple[str, float]] = []
    for m in week_matchups:
        scores.append((m.winner_id, m.winner_score))
        scores.append((m.loser_id, m.loser_score))

    # Deterministic sort: score desc, then franchise_id asc for ties
    scores.sort(key=lambda x: (-x[1], x[0]))
    high = scores[0]
    low = scores[-1]

    # Closest game: smallest margin (ties excluded since margin = 0)
    non_tie = [m for m in week_matchups if not m.is_tie]
    if non_tie:
        by_margin = sorted(non_tie, key=lambda m: (m.margin, m.winner_id))
        closest = by_margin[0]
        closest_result = (closest.winner_id, closest.loser_id, closest.margin)
        biggest = by_margin[-1]
        blowout_result = (biggest.winner_id, biggest.loser_id, biggest.margin)
    else:
        closest_result = None
        blowout_result = None

    return high, low, closest_result, blowout_result


def _season_milestones(
    matchups: Sequence[MatchupResult],
    through_week: int,
) -> Tuple[Optional[ScoringMilestone], Optional[ScoringMilestone], Optional[float]]:
    """Derive season-level scoring milestones through a given week."""
    scores: List[Tuple[str, int, float]] = []  # (franchise_id, week, score)

    for m in matchups:
        if m.week > through_week:
            continue
        scores.append((m.winner_id, m.week, m.winner_score))
        scores.append((m.loser_id, m.week, m.loser_score))

    if not scores:
        return None, None, None

    # Season high: highest score, tiebreak by earliest week then franchise_id
    by_high = sorted(scores, key=lambda x: (-x[2], x[1], x[0]))
    high = by_high[0]
    season_high = ScoringMilestone(
        franchise_id=high[0], week=high[1], score=high[2], label="season_high"
    )

    # Season low: lowest score, tiebreak by earliest week then franchise_id
    by_low = sorted(scores, key=lambda x: (x[2], x[1], x[0]))
    low = by_low[0]
    season_low = ScoringMilestone(
        franchise_id=low[0], week=low[1], score=low[2], label="season_low"
    )

    # Season average
    avg = round(sum(s[2] for s in scores) / len(scores), 2) if scores else None

    return season_high, season_low, avg


# ── Public API ───────────────────────────────────────────────────────


def derive_season_context_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> SeasonContextV1:
    """Derive season context for a given week from canonical matchup events.

    Returns a SeasonContextV1 with standings, streaks, scoring context.
    If no matchup data exists, returns an empty context (silence over fabrication).

    This is the primary engine upgrade for the creative layer.
    """
    all_matchups = _load_matchups(db_path, str(league_id), int(season))

    if not all_matchups:
        return _empty_context(str(league_id), int(season), int(week_index))

    # Filter to through this week
    through = [m for m in all_matchups if m.week <= week_index]
    this_week = [m for m in all_matchups if m.week == week_index]

    if not through:
        return _empty_context(str(league_id), int(season), int(week_index))

    # Records and standings
    records = _compute_records(all_matchups, through_week=week_index)

    # Sort standings: wins desc, then PF desc (tiebreaker), then franchise_id asc
    standings = tuple(sorted(
        records.values(),
        key=lambda r: (-r.wins, -r.points_for, r.franchise_id),
    ))

    # Week matchups with post-game records
    week_matchup_contexts: List[WeekMatchupContext] = []
    for m in this_week:
        week_matchup_contexts.append(WeekMatchupContext(
            winner_id=m.winner_id,
            loser_id=m.loser_id,
            winner_score=m.winner_score,
            loser_score=m.loser_score,
            margin=m.margin,
            is_tie=m.is_tie,
            winner_record_after=records.get(m.winner_id),
            loser_record_after=records.get(m.loser_id),
        ))
    # Deterministic order
    week_matchup_contexts.sort(key=lambda wm: (wm.winner_id, wm.loser_id))

    # This week's highlights
    high, low, closest, blowout = _week_scoring_highlights(this_week)

    # Season milestones
    season_high, season_low, season_avg = _season_milestones(all_matchups, week_index)

    return SeasonContextV1(
        league_id=str(league_id),
        season=int(season),
        through_week=int(week_index),
        standings=standings,
        week_matchups=tuple(week_matchup_contexts),
        week_high_scorer=high,
        week_low_scorer=low,
        week_closest_game=closest,
        week_biggest_blowout=blowout,
        season_high=season_high,
        season_low=season_low,
        season_avg_score=season_avg,
        total_matchups_through_week=len(through),
        matchups_this_week=len(this_week),
    )


# ── Prompt rendering (for creative layer consumption) ────────────────


def render_season_context_for_prompt(
    ctx: SeasonContextV1,
    *,
    team_resolver: Optional[Any] = None,
) -> str:
    """Render season context as a text block for the creative layer prompt.

    This is the bridge between the engine and the writer's room.
    The output is a structured text block that gives an LLM everything
    it needs to write sharp, informed commentary.

    team_resolver: optional callable (franchise_id -> display_name).
    If None, franchise IDs are used directly.
    """
    if not ctx.has_matchup_data:
        return "(No matchup data available for this season/week.)\n"

    def _name(fid: str) -> str:
        if team_resolver is not None:
            try:
                n = team_resolver(fid)
                if n and str(n).strip():
                    return str(n).strip()
            except (KeyError, ValueError, TypeError, LookupError):
                pass
        return fid

    def _streak_str(s: int) -> str:
        if s > 0:
            return f"W{s}"
        elif s < 0:
            return f"L{abs(s)}"
        return "-"

    lines: List[str] = []

    # Standings
    lines.append(f"Season standings through Week {ctx.through_week}:")
    for i, rec in enumerate(ctx.standings, 1):
        name = _name(rec.franchise_id)
        record = f"{rec.wins}-{rec.losses}"
        if rec.ties > 0:
            record += f"-{rec.ties}"
        streak = _streak_str(rec.current_streak)
        pf = f"{rec.points_for:.1f}"
        lines.append(f"  {i}. {name} ({record}, PF: {pf}, Streak: {streak})")

    if ctx.has_this_week_data:
        lines.append("")
        lines.append(f"Week {ctx.through_week} results:")
        for wm in ctx.week_matchups:
            winner = _name(wm.winner_id)
            loser = _name(wm.loser_id)
            if wm.is_tie:
                lines.append(f"  {winner} tied {loser} {wm.winner_score:.2f}-{wm.loser_score:.2f}")
            else:
                lines.append(
                    f"  {winner} beat {loser} {wm.winner_score:.2f}-{wm.loser_score:.2f}"
                    f" (margin: {wm.margin:.2f})"
                )

        # Week highlights
        if ctx.week_high_scorer:
            name = _name(ctx.week_high_scorer[0])
            lines.append(f"  High scorer: {name} ({ctx.week_high_scorer[1]:.2f})")
        if ctx.week_low_scorer:
            name = _name(ctx.week_low_scorer[0])
            lines.append(f"  Low scorer: {name} ({ctx.week_low_scorer[1]:.2f})")
        if ctx.week_closest_game:
            w, l, margin = ctx.week_closest_game
            lines.append(f"  Closest game: {_name(w)} over {_name(l)} by {margin:.2f}")
        if ctx.week_biggest_blowout:
            w, l, margin = ctx.week_biggest_blowout
            lines.append(f"  Biggest margin: {_name(w)} over {_name(l)} by {margin:.2f}")

    # Season milestones
    if ctx.season_high or ctx.season_low or ctx.season_avg_score:
        lines.append("")
        lines.append("Season scoring context:")
        if ctx.season_high:
            name = _name(ctx.season_high.franchise_id)
            lines.append(
                f"  Season high: {name} — {ctx.season_high.score:.2f} (Week {ctx.season_high.week})"
            )
        if ctx.season_low:
            name = _name(ctx.season_low.franchise_id)
            lines.append(
                f"  Season low: {name} — {ctx.season_low.score:.2f} (Week {ctx.season_low.week})"
            )
        if ctx.season_avg_score is not None:
            lines.append(f"  League average score: {ctx.season_avg_score:.2f}")

    return "\n".join(lines) + "\n"
