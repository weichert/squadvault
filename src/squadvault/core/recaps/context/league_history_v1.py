"""League History Context v1 — cross-season longitudinal derivation.

Contract:
- Derived-only: reads canonical events across ALL seasons, never writes back.
- Deterministic: identical inputs produce identical outputs.
- Non-authoritative: context is for creative layer consumption, not fact.
- Reconstructable: can be dropped and rebuilt from canonical events.

This module computes all-time records, head-to-head history, scoring
records, and streak records across the full league history. It is the
longitudinal companion to SeasonContextV1 (single-season).

Together they give the creative layer the material for:
- "That 158.5 is the highest score in league history, breaking the 2021 record"
- "Gopher Boys have beaten Team Elway in 7 of their last 10 meetings"
- "This is the first 6-0 start since the 2019 dynasty run"
- "Their 4-game losing streak is the worst since 2020"

Governance:
- Defers to Canonical Operating Constitution
- Aligned with PLAYER_WEEK_CONTEXT contract pattern (derived, non-authoritative)
- No inference, projection, or gap-filling
- Missing data stays missing
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from squadvault.core.storage.session import DatabaseSession


# ── Data classes ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class HistoricalMatchup:
    """A single matchup result from any season."""
    season: int
    week: int
    winner_id: str
    loser_id: str
    winner_score: float
    loser_score: float
    is_tie: bool
    margin: float


@dataclass(frozen=True)
class AllTimeRecord:
    """All-time W-L-T record for a franchise across all seasons."""
    franchise_id: str
    seasons_active: Tuple[int, ...]
    total_wins: int
    total_losses: int
    total_ties: int
    total_points_for: float
    total_points_against: float

    @property
    def total_games(self) -> int:
        """Total games played all-time."""
        return self.total_wins + self.total_losses + self.total_ties

    @property
    def all_time_win_pct(self) -> float:
        """All-time winning percentage (0.0 to 1.0)."""
        if self.total_games == 0:
            return 0.0
        return self.total_wins / self.total_games


@dataclass(frozen=True)
class HeadToHeadRecord:
    """All-time head-to-head record between two franchises."""
    franchise_a: str
    franchise_b: str
    a_wins: int
    b_wins: int
    ties: int
    meetings: Tuple[HistoricalMatchup, ...]  # chronological

    @property
    def total_meetings(self) -> int:
        """Total head-to-head meetings between the two franchises."""
        return self.a_wins + self.b_wins + self.ties


@dataclass(frozen=True)
class ScoringRecord:
    """An all-time scoring record."""
    franchise_id: str
    season: int
    week: int
    score: float
    label: str  # "all_time_high", "all_time_low"


@dataclass(frozen=True)
class StreakRecord:
    """A notable streak in league history."""
    franchise_id: str
    streak_type: str  # "win", "loss"
    length: int
    start_season: int
    start_week: int
    end_season: int
    end_week: int


@dataclass(frozen=True)
class SeasonRecord:
    """A single franchise's record for a single season."""
    franchise_id: str
    season: int
    wins: int
    losses: int
    ties: int
    points_for: float


@dataclass(frozen=True)
class LeagueHistoryContextV1:
    """Full longitudinal context for a league across all ingested seasons.

    This is the cross-season companion to SeasonContextV1.
    Together they feed the creative layer everything it needs.
    """
    league_id: str
    seasons_available: Tuple[int, ...]   # all seasons with data, sorted
    total_matchups_all_time: int

    # All-time records per franchise, sorted by total wins desc
    all_time_records: Tuple[AllTimeRecord, ...]

    # All-time scoring records
    all_time_high: Optional[ScoringRecord]
    all_time_low: Optional[ScoringRecord]
    all_time_avg_score: Optional[float]

    # Longest streaks in league history
    longest_win_streak: Optional[StreakRecord]
    longest_loss_streak: Optional[StreakRecord]

    # Best and worst single-season records
    best_season_record: Optional[SeasonRecord]
    worst_season_record: Optional[SeasonRecord]

    @property
    def has_history(self) -> bool:
        """True if any matchup data exists across any season."""
        return self.total_matchups_all_time > 0

    @property
    def is_multi_season(self) -> bool:
        """True if data spans more than one season."""
        return len(self.seasons_available) > 1


# ── Loading ──────────────────────────────────────────────────────────


def _parse_matchup(payload_json: str, season: int, fallback_week: int) -> Optional[HistoricalMatchup]:
    """Parse a WEEKLY_MATCHUP_RESULT payload into a HistoricalMatchup."""
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
    margin = round(abs(winner_score - loser_score), 2)

    return HistoricalMatchup(
        season=season,
        week=week,
        winner_id=str(winner_id).strip(),
        loser_id=str(loser_id).strip(),
        winner_score=winner_score,
        loser_score=loser_score,
        is_tie=is_tie,
        margin=margin,
    )


def load_all_matchups(db_path: str, league_id: str) -> List[HistoricalMatchup]:
    """Load ALL WEEKLY_MATCHUP_RESULT events across all seasons.

    Returns parsed list sorted by (season, week, winner_id, loser_id).
    """
    matchups: List[HistoricalMatchup] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT season, payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'
               ORDER BY season ASC, occurred_at ASC NULLS LAST""",
            (str(league_id),),
        ).fetchall()

    for row in rows:
        season = int(row[0])
        m = _parse_matchup(row[1], season=season, fallback_week=0)
        if m is not None:
            matchups.append(m)

    matchups.sort(key=lambda m: (m.season, m.week, m.winner_id, m.loser_id))
    return matchups


# ── Derivation: all-time records ─────────────────────────────────────


def _compute_all_time_records(
    matchups: Sequence[HistoricalMatchup],
) -> Dict[str, AllTimeRecord]:
    """Compute all-time W-L-T records for every franchise."""
    wins: Dict[str, int] = {}
    losses: Dict[str, int] = {}
    ties: Dict[str, int] = {}
    pf: Dict[str, float] = {}
    pa: Dict[str, float] = {}
    seasons: Dict[str, set] = {}

    for m in matchups:
        for fid in (m.winner_id, m.loser_id):
            wins.setdefault(fid, 0)
            losses.setdefault(fid, 0)
            ties.setdefault(fid, 0)
            pf.setdefault(fid, 0.0)
            pa.setdefault(fid, 0.0)
            seasons.setdefault(fid, set())
            seasons[fid].add(m.season)

        if m.is_tie:
            ties[m.winner_id] += 1
            ties[m.loser_id] += 1
            pf[m.winner_id] += m.winner_score
            pa[m.winner_id] += m.loser_score
            pf[m.loser_id] += m.loser_score
            pa[m.loser_id] += m.winner_score
        else:
            wins[m.winner_id] += 1
            losses[m.loser_id] += 1
            pf[m.winner_id] += m.winner_score
            pa[m.winner_id] += m.loser_score
            pf[m.loser_id] += m.loser_score
            pa[m.loser_id] += m.winner_score

    records: Dict[str, AllTimeRecord] = {}
    for fid in wins:
        records[fid] = AllTimeRecord(
            franchise_id=fid,
            seasons_active=tuple(sorted(seasons.get(fid, set()))),
            total_wins=wins.get(fid, 0),
            total_losses=losses.get(fid, 0),
            total_ties=ties.get(fid, 0),
            total_points_for=round(pf.get(fid, 0.0), 2),
            total_points_against=round(pa.get(fid, 0.0), 2),
        )
    return records


# ── Derivation: head-to-head ─────────────────────────────────────────


def compute_head_to_head(
    matchups: Sequence[HistoricalMatchup],
    franchise_a: str,
    franchise_b: str,
) -> HeadToHeadRecord:
    """Compute all-time head-to-head record between two franchises."""
    a = str(franchise_a).strip()
    b = str(franchise_b).strip()
    a_wins = 0
    b_wins = 0
    t = 0
    meetings: List[HistoricalMatchup] = []

    for m in matchups:
        pair = {m.winner_id, m.loser_id}
        if pair != {a, b}:
            continue
        meetings.append(m)
        if m.is_tie:
            t += 1
        elif m.winner_id == a:
            a_wins += 1
        else:
            b_wins += 1

    meetings.sort(key=lambda m: (m.season, m.week))

    return HeadToHeadRecord(
        franchise_a=a,
        franchise_b=b,
        a_wins=a_wins,
        b_wins=b_wins,
        ties=t,
        meetings=tuple(meetings),
    )


# ── Derivation: streaks ─────────────────────────────────────────────


def _compute_longest_streaks(
    matchups: Sequence[HistoricalMatchup],
) -> Tuple[Optional[StreakRecord], Optional[StreakRecord]]:
    """Find the longest win streak and longest loss streak in league history.

    Streaks span across seasons. A tie ends any active streak.
    """
    # Build per-franchise game logs in chronological order
    game_log: Dict[str, List[Tuple[str, int, int]]] = {}  # fid -> [(result, season, week)]

    sorted_matchups = sorted(matchups, key=lambda m: (m.season, m.week))
    for m in sorted_matchups:
        game_log.setdefault(m.winner_id, [])
        game_log.setdefault(m.loser_id, [])
        if m.is_tie:
            game_log[m.winner_id].append(("T", m.season, m.week))
            game_log[m.loser_id].append(("T", m.season, m.week))
        else:
            game_log[m.winner_id].append(("W", m.season, m.week))
            game_log[m.loser_id].append(("L", m.season, m.week))

    best_win: Optional[StreakRecord] = None
    best_loss: Optional[StreakRecord] = None

    for fid, log in game_log.items():
        if not log:
            continue

        # Walk the log tracking current streak
        streak_type = log[0][0]
        streak_start = 0
        streak_len = 1

        for i in range(1, len(log)):
            if log[i][0] == streak_type and streak_type != "T":
                streak_len += 1
            else:
                # Record completed streak
                if streak_type == "W" and (best_win is None or streak_len > best_win.length):
                    best_win = StreakRecord(
                        franchise_id=fid,
                        streak_type="win",
                        length=streak_len,
                        start_season=log[streak_start][1],
                        start_week=log[streak_start][2],
                        end_season=log[i - 1][1],
                        end_week=log[i - 1][2],
                    )
                elif streak_type == "L" and (best_loss is None or streak_len > best_loss.length):
                    best_loss = StreakRecord(
                        franchise_id=fid,
                        streak_type="loss",
                        length=streak_len,
                        start_season=log[streak_start][1],
                        start_week=log[streak_start][2],
                        end_season=log[i - 1][1],
                        end_week=log[i - 1][2],
                    )
                streak_type = log[i][0]
                streak_start = i
                streak_len = 1

        # Don't forget the final streak
        if streak_type == "W" and (best_win is None or streak_len > best_win.length):
            best_win = StreakRecord(
                franchise_id=fid,
                streak_type="win",
                length=streak_len,
                start_season=log[streak_start][1],
                start_week=log[streak_start][2],
                end_season=log[-1][1],
                end_week=log[-1][2],
            )
        elif streak_type == "L" and (best_loss is None or streak_len > best_loss.length):
            best_loss = StreakRecord(
                franchise_id=fid,
                streak_type="loss",
                length=streak_len,
                start_season=log[streak_start][1],
                start_week=log[streak_start][2],
                end_season=log[-1][1],
                end_week=log[-1][2],
            )

    return best_win, best_loss


# ── Derivation: scoring records ──────────────────────────────────────


def _compute_scoring_records(
    matchups: Sequence[HistoricalMatchup],
) -> Tuple[Optional[ScoringRecord], Optional[ScoringRecord], Optional[float]]:
    """Find all-time scoring high, low, and league average."""
    scores: List[Tuple[str, int, int, float]] = []  # (fid, season, week, score)

    for m in matchups:
        scores.append((m.winner_id, m.season, m.week, m.winner_score))
        scores.append((m.loser_id, m.season, m.week, m.loser_score))

    if not scores:
        return None, None, None

    # High: highest score, tiebreak by earliest (season, week, fid)
    by_high = sorted(scores, key=lambda x: (-x[3], x[1], x[2], x[0]))
    h = by_high[0]
    high = ScoringRecord(franchise_id=h[0], season=h[1], week=h[2], score=h[3], label="all_time_high")

    # Low: lowest score
    by_low = sorted(scores, key=lambda x: (x[3], x[1], x[2], x[0]))
    lo = by_low[0]
    low = ScoringRecord(franchise_id=lo[0], season=lo[1], week=lo[2], score=lo[3], label="all_time_low")

    avg = round(sum(s[3] for s in scores) / len(scores), 2)

    return high, low, avg


# ── Derivation: best/worst seasons ──────────────────────────────────


def _compute_season_records(
    matchups: Sequence[HistoricalMatchup],
) -> Tuple[Optional[SeasonRecord], Optional[SeasonRecord]]:
    """Find the best and worst single-season records in league history."""
    # Accumulate per (franchise, season)
    key_data: Dict[Tuple[str, int], Dict[str, Any]] = {}

    for m in matchups:
        for fid, is_winner in [(m.winner_id, True), (m.loser_id, False)]:
            k = (fid, m.season)
            if k not in key_data:
                key_data[k] = {"w": 0, "l": 0, "t": 0, "pf": 0.0}
            if m.is_tie:
                key_data[k]["t"] += 1
            elif is_winner:
                key_data[k]["w"] += 1
            else:
                key_data[k]["l"] += 1
            score = m.winner_score if is_winner else m.loser_score
            key_data[k]["pf"] += score

    if not key_data:
        return None, None

    records: List[SeasonRecord] = []
    for (fid, season), d in key_data.items():
        records.append(SeasonRecord(
            franchise_id=fid,
            season=season,
            wins=d["w"],
            losses=d["l"],
            ties=d["t"],
            points_for=round(d["pf"], 2),
        ))

    # Best: most wins, tiebreak by PF desc, then earliest season
    by_best = sorted(records, key=lambda r: (-r.wins, -r.points_for, r.season, r.franchise_id))
    # Worst: most losses, tiebreak by PF asc, then earliest season
    by_worst = sorted(records, key=lambda r: (-r.losses, r.points_for, r.season, r.franchise_id))

    return by_best[0], by_worst[0]


# ── Franchise name resolution (cross-season) ────────────────────────


def resolve_franchise_name_any_season(
    db_path: str,
    league_id: str,
    franchise_id: str,
) -> str:
    """Resolve a franchise ID to its most recent display name.

    Queries franchise_directory across all seasons, preferring the most
    recent season's name. Returns the raw franchise_id if not found.
    """
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT name FROM franchise_directory
               WHERE league_id = ? AND franchise_id = ?
               ORDER BY season DESC LIMIT 1""",
            (str(league_id), str(franchise_id)),
        ).fetchone()
    if row and row[0]:
        return str(row[0]).strip()
    return franchise_id


def build_cross_season_name_resolver(
    db_path: str,
    league_id: str,
) -> dict:
    """Build a franchise_id -> name map using the most recent season for each.

    Returns a dict suitable for use as a lookup or wrapped in a lambda.
    """
    name_map: Dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT franchise_id, name, season FROM franchise_directory
               WHERE league_id = ?
               ORDER BY season DESC""",
            (str(league_id),),
        ).fetchall()
    for row in rows:
        fid = str(row[0]).strip()
        name = str(row[1]).strip() if row[1] else fid
        # First seen = most recent season (ordered DESC)
        if fid not in name_map:
            name_map[fid] = name
    return name_map


# ── Public API ───────────────────────────────────────────────────────


def derive_league_history_v1(
    *,
    db_path: str,
    league_id: str,
) -> LeagueHistoryContextV1:
    """Derive full longitudinal context for a league across all seasons.

    Returns a LeagueHistoryContextV1 with all-time records, scoring records,
    streak records, and best/worst seasons.
    """
    all_matchups = load_all_matchups(db_path, str(league_id))

    if not all_matchups:
        return LeagueHistoryContextV1(
            league_id=str(league_id),
            seasons_available=(),
            total_matchups_all_time=0,
            all_time_records=(),
            all_time_high=None,
            all_time_low=None,
            all_time_avg_score=None,
            longest_win_streak=None,
            longest_loss_streak=None,
            best_season_record=None,
            worst_season_record=None,
        )

    seasons = tuple(sorted(set(m.season for m in all_matchups)))
    at_records = _compute_all_time_records(all_matchups)
    at_sorted = tuple(sorted(
        at_records.values(),
        key=lambda r: (-r.total_wins, -r.total_points_for, r.franchise_id),
    ))

    high, low, avg = _compute_scoring_records(all_matchups)
    win_streak, loss_streak = _compute_longest_streaks(all_matchups)
    best_season, worst_season = _compute_season_records(all_matchups)

    return LeagueHistoryContextV1(
        league_id=str(league_id),
        seasons_available=seasons,
        total_matchups_all_time=len(all_matchups),
        all_time_records=at_sorted,
        all_time_high=high,
        all_time_low=low,
        all_time_avg_score=avg,
        longest_win_streak=win_streak,
        longest_loss_streak=loss_streak,
        best_season_record=best_season,
        worst_season_record=worst_season,
    )


# ── Prompt rendering ─────────────────────────────────────────────────


def render_league_history_for_prompt(
    ctx: LeagueHistoryContextV1,
    *,
    name_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render league history as a text block for the creative layer prompt.

    name_map: optional dict of franchise_id -> display_name.
    """
    if not ctx.has_history:
        return "(No league history available.)\n"

    def _name(fid: str) -> str:
        """Resolve franchise ID to display name via name_map."""
        if name_map and fid in name_map:
            return name_map[fid]
        return fid

    lines: List[str] = []

    season_str = ", ".join(str(s) for s in ctx.seasons_available)
    lines.append(f"League history ({len(ctx.seasons_available)} season(s): {season_str}):")
    lines.append(f"Total matchups all-time: {ctx.total_matchups_all_time}")

    # All-time standings
    lines.append("")
    lines.append("All-time records:")
    for rec in ctx.all_time_records:
        name = _name(rec.franchise_id)
        record = f"{rec.total_wins}-{rec.total_losses}"
        if rec.total_ties > 0:
            record += f"-{rec.total_ties}"
        pct = f"{rec.all_time_win_pct:.3f}"
        lines.append(f"  {name}: {record} ({pct}), PF: {rec.total_points_for:.1f}")

    # Scoring records
    if ctx.all_time_high or ctx.all_time_low:
        lines.append("")
        lines.append("All-time scoring records:")
        if ctx.all_time_high:
            name = _name(ctx.all_time_high.franchise_id)
            lines.append(
                f"  Highest score ever: {name} — {ctx.all_time_high.score:.2f}"
                f" (Season {ctx.all_time_high.season}, Week {ctx.all_time_high.week})"
            )
        if ctx.all_time_low:
            name = _name(ctx.all_time_low.franchise_id)
            lines.append(
                f"  Lowest score ever: {name} — {ctx.all_time_low.score:.2f}"
                f" (Season {ctx.all_time_low.season}, Week {ctx.all_time_low.week})"
            )
        if ctx.all_time_avg_score is not None:
            lines.append(f"  League all-time average: {ctx.all_time_avg_score:.2f}")

    # Streak records
    if ctx.longest_win_streak or ctx.longest_loss_streak:
        lines.append("")
        lines.append("Streak records:")
        if ctx.longest_win_streak:
            s = ctx.longest_win_streak
            name = _name(s.franchise_id)
            span = f"Season {s.start_season} Week {s.start_week} to Season {s.end_season} Week {s.end_week}"
            lines.append(f"  Longest win streak: {name} — {s.length} games ({span})")
        if ctx.longest_loss_streak:
            s = ctx.longest_loss_streak
            name = _name(s.franchise_id)
            span = f"Season {s.start_season} Week {s.start_week} to Season {s.end_season} Week {s.end_week}"
            lines.append(f"  Longest loss streak: {name} — {s.length} games ({span})")

    # Best/worst seasons
    if ctx.best_season_record or ctx.worst_season_record:
        lines.append("")
        lines.append("Notable seasons:")
        if ctx.best_season_record:
            r = ctx.best_season_record
            name = _name(r.franchise_id)
            record = f"{r.wins}-{r.losses}"
            if r.ties > 0:
                record += f"-{r.ties}"
            lines.append(f"  Best season: {name} — {record} in {r.season}")
        if ctx.worst_season_record:
            r = ctx.worst_season_record
            name = _name(r.franchise_id)
            record = f"{r.wins}-{r.losses}"
            if r.ties > 0:
                record += f"-{r.ties}"
            lines.append(f"  Worst season: {name} — {record} in {r.season}")

    return "\n".join(lines) + "\n"
