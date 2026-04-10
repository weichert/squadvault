"""Franchise Deep Angle Detection v1 — Dimensions 7-9.

Contract:
- Derived-only: computes angles from canonical events.
- Deterministic: identical inputs produce identical angles.
- Non-authoritative: angles are story hooks, not facts.
- Reconstructable: drop and rebuild produces identical output.
- No inference, projection, or gap-filling.

Dimension 7 — Franchise Scoring Patterns (detectors 29-32):
29. SCORING_CONCENTRATION — one player accounts for 35%+ of franchise scoring
30. SCORING_VOLATILITY — unusually consistent or volatile week-to-week scoring
31. STAR_EXPLOSION_COUNT — disproportionately many 40+ point performances
32. POSITIONAL_STRENGTH — disproportionate production from a position group

Dimension 8 — Bench & Lineup Decisions (detectors 33-35):
33. BENCH_COST_GAME — lost by fewer points than left on bench
34. CHRONIC_BENCH_MISMANAGEMENT — 15+ bench points left on table in 3+ weeks
35. PERFECT_LINEUP_WEEK — actual lineup matched optimal lineup

Dimension 9 — Franchise History & Identity (detectors 36-50):
36. CLOSE_GAME_RECORD — all-time record in games decided by < 5 pts
37. SEASON_TRAJECTORY_MATCH — current record matches a historical season
38. SECOND_HALF_SURGE_COLLAPSE — 15%+ scoring change between season halves
39. CHAMPIONSHIP_HISTORY — playoff/championship appearance counts
40. FRANCHISE_ALLTIME_SCORING — total scoring across seasons (tenure-scoped)
41. TRANSACTION_VOLUME_IDENTITY — roster move volume as personality
42. LUCKY_RECORD — W-L deviates significantly from point differential
43. WEEKLY_SCORING_RANK_DOMINANCE — top/bottom scorer with unusual frequency
44. SCHEDULE_STRENGTH — opponents' combined winning percentage
45. REGULAR_SEASON_VS_PLAYOFF — regular season vs playoff record diverges
46. THE_BRIDESMAID — second-highest score but lost
47. POINTS_AGAINST_LUCK — faced opponent's season-high unusually often
48. REPEAT_MATCHUP_PATTERN — two franchises consistently produce high combined scores
49. SCORING_MOMENTUM_IN_STREAK — growing/shrinking margins during win streak
50. THE_ALMOST — finished one game out of playoffs multiple times

Reuses the NarrativeAngle dataclass from narrative_angles_v1.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from squadvault.core.recaps.context.league_history_v1 import HistoricalMatchup
from squadvault.core.recaps.context.narrative_angles_v1 import NarrativeAngle
from squadvault.core.resolvers import NameFn
from squadvault.core.resolvers import identity as _identity
from squadvault.core.storage.session import DatabaseSession

# ── Data loading (lightweight, module-local) ─────────────────────────


def _load_season_player_scores_flat(
    db_path: str, league_id: str, season: int,
) -> list[dict]:
    """Load WEEKLY_PLAYER_SCORE payloads for a season. Returns raw dicts."""
    out: list[dict] = []
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json FROM v_canonical_best_events
               WHERE league_id = ? AND season = ? AND event_type = 'WEEKLY_PLAYER_SCORE'""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if isinstance(p, dict):
            out.append(p)
    return out


def _load_player_positions(
    db_path: str, league_id: str, season: int,
) -> dict[str, str]:
    """Load player_id -> position from player_directory."""
    positions: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT player_id, position FROM player_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        pid = str(row[0]).strip()
        pos = str(row[1] or "").strip()
        if pid and pos:
            positions[pid] = pos
    return positions


def _load_all_matchups_flat(
    db_path: str, league_id: str,
) -> list[HistoricalMatchup]:
    """Load all WEEKLY_MATCHUP_RESULT events. Reuses league_history_v1 pattern."""
    from squadvault.core.recaps.context.league_history_v1 import load_all_matchups
    return load_all_matchups(db_path, league_id)


def _load_season_transaction_counts(
    db_path: str, league_id: str, season: int,
) -> dict[str, int]:
    """Count in-season roster move events per franchise for a season.

    Only counts transaction types that represent real in-season roster
    decisions (trades, free agents, waivers). Excludes auction draft wins,
    operational events, and boundary markers to avoid inflating early-week
    counts with draft-day activity.
    """
    # In-season roster move types only — excludes TRANSACTION_AUCTION_WON
    # (initial draft), operational events, and boundary markers.
    in_season_types = (
        "TRANSACTION_TRADE",
        "TRANSACTION_FREE_AGENT",
        "TRANSACTION_WAIVER",
        "TRANSACTION_BBID_WAIVER",
    )
    placeholders = ",".join(["?"] * len(in_season_types))
    counts: dict[str, int] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            f"""SELECT payload_json FROM v_canonical_best_events
               WHERE league_id = ? AND season = ? AND event_type IN ({placeholders})""",
            (str(league_id), int(season), *in_season_types),
        ).fetchall()
    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if isinstance(p, dict):
            fid = str(p.get("franchise_id", "")).strip()
            if fid:
                counts[fid] = counts.get(fid, 0) + 1
    return counts


# ── Dimension 7: Franchise Scoring Patterns ──────────────────────────


def detect_scoring_concentration(
    score_payloads: list[dict], target_week: int,
    *, threshold: float = 0.35,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 29: One player accounts for 35%+ of franchise starter scoring."""
    # Aggregate starter scoring per (franchise, player) through target_week
    franchise_player: dict[tuple[str, str], float] = {}
    franchise_total: dict[str, float] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        pid = str(p.get("player_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid and pid:
            franchise_player[(fid, pid)] = franchise_player.get((fid, pid), 0.0) + score
            franchise_total[fid] = franchise_total.get(fid, 0.0) + score

    angles: list[NarrativeAngle] = []
    for (fid, pid), pts in sorted(franchise_player.items()):
        total = franchise_total.get(fid, 0.0)
        if total < 1.0:
            continue
        pct = pts / total
        if pct >= threshold:
            angles.append(NarrativeAngle(
                category="SCORING_CONCENTRATION",
                headline=f"{round(pct * 100)}% of {fname(fid)}'s starter points come from {pname(pid)}",
                detail=f"{pts:.1f} of {total:.1f} total.",
                strength=2,  # NOTABLE
                franchise_ids=(fid,),
            ))
    return angles


def detect_scoring_volatility(
    score_payloads: list[dict], target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 30: Unusually consistent or volatile week-to-week scoring."""
    # Weekly totals per franchise (starters only)
    franchise_weeks: dict[str, list[float]] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid:
            if fid not in franchise_weeks:
                franchise_weeks[fid] = [0.0] * (target_week + 1)
            if week <= target_week:
                franchise_weeks[fid][week] = franchise_weeks[fid][week] + score

    # Need at least 4 weeks of data
    angles: list[NarrativeAngle] = []
    ranges: list[tuple[str, float]] = []
    for fid, weekly in sorted(franchise_weeks.items()):
        active = [w for i, w in enumerate(weekly) if i >= 1 and w > 0]
        if len(active) < 4:
            continue
        score_range = max(active) - min(active)
        ranges.append((fid, score_range))

    if len(ranges) < 3:
        return []

    ranges.sort(key=lambda x: x[1])
    most_consistent = ranges[0]
    most_volatile = ranges[-1]

    if most_volatile[1] > most_consistent[1] * 2:
        angles.append(NarrativeAngle(
            category="SCORING_VOLATILITY",
            headline=f"{most_consistent[0]} has the narrowest scoring range this season",
            detail=f"Range: {most_consistent[1]:.1f} pts between best and worst weeks.",
            strength=1, franchise_ids=(most_consistent[0],),
        ))
        angles.append(NarrativeAngle(
            category="SCORING_VOLATILITY",
            headline=f"{most_volatile[0]} has the widest scoring range this season",
            detail=f"Range: {most_volatile[1]:.1f} pts between best and worst weeks.",
            strength=1, franchise_ids=(most_volatile[0],),
        ))
    return angles


def detect_star_explosion_count(
    score_payloads: list[dict], target_week: int,
    *, explosion_threshold: float = 40.0,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 31: Franchise with disproportionately many 40+ point performances."""
    franchise_explosions: dict[str, int] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid and score >= explosion_threshold:
            franchise_explosions[fid] = franchise_explosions.get(fid, 0) + 1

    if not franchise_explosions:
        return []

    best_fid = max(franchise_explosions, key=lambda f: franchise_explosions[f])
    best_count = franchise_explosions[best_fid]
    others_max = max((c for f, c in franchise_explosions.items() if f != best_fid), default=0)

    if best_count >= 3 and best_count >= others_max * 2:
        return [NarrativeAngle(
            category="STAR_EXPLOSION_COUNT",
            headline=(
                f"{fname(best_fid)} has had a player score {explosion_threshold:.0f}+ "
                f"{best_count} times this season"
            ),
            detail=f"No other team has more than {others_max}.",
            strength=1, franchise_ids=(best_fid,),
        )]
    return []


def detect_positional_strength(
    score_payloads: list[dict], positions: dict[str, str], target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 32: Franchise with disproportionate production from a position."""
    # Aggregate by (franchise, position)
    fid_pos_pts: dict[tuple[str, str], float] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        pid = str(p.get("player_id", "")).strip()
        pos = positions.get(pid, "")
        if not fid or not pos:
            continue
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        key = (fid, pos)
        fid_pos_pts[key] = fid_pos_pts.get(key, 0.0) + score

    if not fid_pos_pts:
        return []

    # For each position, find the league leader
    pos_leaders: dict[str, tuple[str, float]] = {}  # pos -> (best_fid, total)
    for (fid, pos), pts in fid_pos_pts.items():
        current = pos_leaders.get(pos)
        if current is None or pts > current[1]:
            pos_leaders[pos] = (fid, pts)

    angles: list[NarrativeAngle] = []
    for pos in sorted(pos_leaders.keys()):
        fid, pts = pos_leaders[pos]
        # Only report major positions
        if pos not in ("QB", "RB", "WR", "TE"):
            continue
        angles.append(NarrativeAngle(
            category="POSITIONAL_STRENGTH",
            headline=f"{fname(fid)} has the most combined {pos} production this season",
            detail=f"{pts:.1f} total {pos} points.",
            strength=1, franchise_ids=(fid,),
        ))
    return angles


# ── Dimension 8: Bench & Lineup Decisions ────────────────────────────


def detect_bench_cost_game(
    score_payloads: list[dict],
    matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
    pname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 33: Lost by fewer points than left on bench."""
    # Bench points where should_start=True per (franchise, week)
    bench_pts: dict[tuple[str, int], list[tuple[str, float]]] = {}  # (fid, week) -> [(pid, score)]
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week != target_week:
            continue
        if p.get("is_starter") or not p.get("should_start"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        pid = str(p.get("player_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid and score > 0:
            key = (fid, week)
            if key not in bench_pts:
                bench_pts[key] = []
            bench_pts[key].append((pid, score))

    # Find this week's losses with margins
    week_matchups = [
        m for m in matchups
        if m.season == current_season and m.week == target_week and not m.is_tie
    ]

    # Collect candidates: (total_bench, margin, loser_id, best_bench_pid, best_bench_score)
    candidates: list[tuple[float, float, str, str, float]] = []
    for m in week_matchups:
        loser = m.loser_id
        margin = m.margin
        bench = bench_pts.get((loser, target_week), [])
        total_bench = sum(s for _, s in bench)
        if total_bench > margin and bench:
            best_bench_pid, best_bench_score = max(bench, key=lambda x: x[1])
            candidates.append((total_bench, margin, loser, best_bench_pid, best_bench_score))

    # Cap at 2 most dramatic (highest bench points left on table)
    candidates.sort(key=lambda c: -c[0])

    angles: list[NarrativeAngle] = []
    for total_bench, margin, loser, best_bench_pid, best_score in candidates[:2]:
        angles.append(NarrativeAngle(
            category="BENCH_COST_GAME",
            headline=(
                f"{fname(loser)} lost by {margin:.2f} with {total_bench:.2f} total bench points; "
                f"top benched player was {pname(best_bench_pid)} ({best_score:.2f})"
            ),
            detail="",
            strength=2, franchise_ids=(loser,),
        ))
    return angles


def detect_chronic_bench_mismanagement(
    score_payloads: list[dict], target_week: int,
    *, bench_threshold: float = 15.0, min_weeks: int = 3,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 34: Franchise leaves 15+ bench points on table in 3+ weeks."""
    # Per franchise per week: total should_start bench points
    fid_week_bench: dict[tuple[str, int], float] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week:
            continue
        if p.get("is_starter") or not p.get("should_start"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid:
            key = (fid, week)
            fid_week_bench[key] = fid_week_bench.get(key, 0.0) + score

    # Count weeks per franchise where bench > threshold
    fid_bad_weeks: dict[str, int] = {}
    for (fid, _), pts in fid_week_bench.items():
        if pts >= bench_threshold:
            fid_bad_weeks[fid] = fid_bad_weeks.get(fid, 0) + 1

    angles: list[NarrativeAngle] = []
    for fid in sorted(fid_bad_weeks.keys()):
        if fid_bad_weeks[fid] >= min_weeks:
            angles.append(NarrativeAngle(
                category="CHRONIC_BENCH_MISMANAGEMENT",
                headline=(
                    f"{fname(fid)} has left {bench_threshold:.0f}+ bench points "
                    f"on the table in {fid_bad_weeks[fid]} weeks this season"
                ),
                detail="", strength=1, franchise_ids=(fid,),
            ))
    return angles


def detect_perfect_lineup_week(
    score_payloads: list[dict], target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 35: Actual lineup matched optimal — zero bench regrets."""
    # Per franchise this week: check if every should_start=True player is also is_starter=True
    franchise_players: dict[str, list[dict]] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week != target_week:
            continue
        fid = str(p.get("franchise_id", "")).strip()
        if fid:
            if fid not in franchise_players:
                franchise_players[fid] = []
            franchise_players[fid].append(p)

    angles: list[NarrativeAngle] = []
    for fid in sorted(franchise_players.keys()):
        players = franchise_players[fid]
        if len(players) < 2:
            continue
        # Check: every player with should_start=True must also have is_starter=True
        perfect = True
        for pl in players:
            if pl.get("should_start") and not pl.get("is_starter"):
                perfect = False
                break
        if perfect:
            angles.append(NarrativeAngle(
                category="PERFECT_LINEUP_WEEK",
                headline=f"{fname(fid)} fielded a perfect lineup this week",
                detail="Every optimal player was started.",
                strength=1, franchise_ids=(fid,),
            ))
    return angles


# ── Dimension 9: Franchise History & Identity ────────────────────────


def detect_close_game_record(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    *, margin_threshold: float = 5.0,
    tenure_map: dict[str, int] | None = None,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 36: All-time record in close games (< 5 pts).

    Only fires when the franchise that holds the best clutch record is
    actually involved in a close game this week. This prevents the model
    from misattributing the record to whichever team happens to be in
    this week's close game.
    """
    # Gate: did a close game happen this week?
    this_week = [
        m for m in all_matchups
        if m.season == current_season and m.week == target_week
        and m.margin < margin_threshold and not m.is_tie
    ]
    if not this_week:
        return []

    # Collect franchise IDs involved in this week's close games
    this_week_close_fids: set[str] = set()
    for m in this_week:
        this_week_close_fids.add(m.winner_id)
        this_week_close_fids.add(m.loser_id)

    # Filter to tenure scope and through current week
    filtered = _tenure_filter(all_matchups, current_season, target_week, tenure_map)
    close_wins: dict[str, int] = {}
    close_losses: dict[str, int] = {}
    for m in filtered:
        if m.margin < margin_threshold and not m.is_tie:
            close_wins[m.winner_id] = close_wins.get(m.winner_id, 0) + 1
            close_losses[m.loser_id] = close_losses.get(m.loser_id, 0) + 1

    all_fids = set(close_wins.keys()) | set(close_losses.keys())
    if len(all_fids) < 3:
        return []

    # Find best clutch record
    best_fid = None
    best_pct = 0.0
    best_record = ""
    for fid in all_fids:
        w = close_wins.get(fid, 0)
        lo = close_losses.get(fid, 0)
        total = w + lo
        if total < 3:
            continue
        pct = w / total
        if pct > best_pct:
            best_pct = pct
            best_fid = fid
            best_record = f"{w}-{lo}"

    # Only fire if the best-clutch-record franchise is actually in a
    # close game this week. Otherwise the model will misattribute the
    # record to whichever team is in the close game.
    if best_fid and best_pct >= 0.60 and best_fid in this_week_close_fids:
        return [NarrativeAngle(
            category="CLOSE_GAME_RECORD",
            headline=f"{fname(best_fid)} is {best_record} in games decided by fewer than {margin_threshold:.0f} points",
            detail="The best clutch record in the league.",
            strength=2, franchise_ids=(best_fid,),
        )]
    return []


def detect_season_trajectory_match(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 37: Current W-L matches a historical season at same week."""
    # Current season records through target_week
    current_records: dict[str, tuple[int, int]] = {}  # fid -> (wins, losses)
    for m in all_matchups:
        if m.season == current_season and m.week <= target_week and not m.is_tie:
            current_records[m.winner_id] = (
                current_records.get(m.winner_id, (0, 0))[0] + 1,
                current_records.get(m.winner_id, (0, 0))[1],
            )
            current_records[m.loser_id] = (
                current_records.get(m.loser_id, (0, 0))[0],
                current_records.get(m.loser_id, (0, 0))[1] + 1,
            )

    # Historical records at same week
    hist_records: dict[tuple[str, int], tuple[int, int]] = {}  # (fid, season) -> (w, l)
    for m in all_matchups:
        if m.season < current_season and m.week <= target_week and not m.is_tie:
            key = (m.winner_id, m.season)
            hist_records[key] = (hist_records.get(key, (0, 0))[0] + 1, hist_records.get(key, (0, 0))[1])
            key2 = (m.loser_id, m.season)
            hist_records[key2] = (hist_records.get(key2, (0, 0))[0], hist_records.get(key2, (0, 0))[1] + 1)

    angles: list[NarrativeAngle] = []
    for fid, (cw, cl) in sorted(current_records.items()):
        if cw + cl < 4:
            continue
        # Find historical matches with same record (any franchise)
        for (hfid, hseason), (hw, hl) in hist_records.items():
            if hw == cw and hl == cl and hseason != current_season:
                # Find how that season ended
                final = _season_final_record(all_matchups, hfid, hseason)
                if final:
                    fw, fl = final
                    angles.append(NarrativeAngle(
                        category="SEASON_TRAJECTORY_MATCH",
                        headline=(
                            f"{fname(fid)} is {cw}-{cl} through Week {target_week}. "
                            f"The last team at {cw}-{cl} at this point was "
                            f"{fname(hfid)} in {hseason}, who finished {fw}-{fl}"
                        ),
                        detail="", strength=1, franchise_ids=(fid,),
                    ))
                    break  # one match per franchise

    return angles


def detect_lucky_record(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    *, luck_threshold: float = 30.0,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 42: W-L significantly deviates from point differential."""
    wins: dict[str, int] = {}
    losses: dict[str, int] = {}
    pf: dict[str, float] = {}
    pa: dict[str, float] = {}
    for m in all_matchups:
        if m.season != current_season or m.week > target_week or m.is_tie:
            continue
        wins[m.winner_id] = wins.get(m.winner_id, 0) + 1
        losses[m.loser_id] = losses.get(m.loser_id, 0) + 1
        pf[m.winner_id] = pf.get(m.winner_id, 0.0) + m.winner_score
        pa[m.winner_id] = pa.get(m.winner_id, 0.0) + m.loser_score
        pf[m.loser_id] = pf.get(m.loser_id, 0.0) + m.loser_score
        pa[m.loser_id] = pa.get(m.loser_id, 0.0) + m.winner_score

    all_fids = set(wins.keys()) | set(losses.keys())
    if len(all_fids) < 3:
        return []

    angles: list[NarrativeAngle] = []
    for fid in sorted(all_fids):
        w = wins.get(fid, 0)
        lo = losses.get(fid, 0)
        diff = pf.get(fid, 0.0) - pa.get(fid, 0.0)
        # Lucky: winning record despite being outscored
        if w > lo and diff < -luck_threshold:
            angles.append(NarrativeAngle(
                category="LUCKY_RECORD",
                headline=(
                    f"{fname(fid)} is {w}-{lo} despite being outscored by "
                    f"{abs(diff):.0f} total points"
                ),
                detail="", strength=2, franchise_ids=(fid,),
            ))
        # Unlucky: losing record despite outscoring
        elif lo > w and diff > luck_threshold:
            angles.append(NarrativeAngle(
                category="LUCKY_RECORD",
                headline=(
                    f"{fname(fid)} is {w}-{lo} despite outscoring opponents by "
                    f"{diff:.0f} total points"
                ),
                detail="", strength=2, franchise_ids=(fid,),
            ))
    return angles


def detect_the_bridesmaid(
    score_payloads: list[dict],
    matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 46: Second-highest score in the league this week but lost."""
    # Get franchise totals this week
    fid_totals: dict[str, float] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week != target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid:
            fid_totals[fid] = fid_totals.get(fid, 0.0) + score

    if len(fid_totals) < 3:
        return []

    ranked = sorted(fid_totals.items(), key=lambda x: -x[1])
    second_fid, second_score = ranked[1]

    # Did the second-highest scorer lose?
    for m in matchups:
        if m.season == current_season and m.week == target_week and not m.is_tie:
            if m.loser_id == second_fid:
                return [NarrativeAngle(
                    category="THE_BRIDESMAID",
                    headline=(
                        f"{fname(second_fid)} scored {second_score:.2f} — the second-highest "
                        f"in the league — and still lost"
                    ),
                    detail="", strength=1, franchise_ids=(second_fid,),
                )]
    return []


def detect_transaction_volume_identity(
    transaction_counts: dict[str, int],
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 41: Roster move volume as franchise personality."""
    if len(transaction_counts) < 3:
        return []
    ranked = sorted(transaction_counts.items(), key=lambda x: -x[1])
    most_fid, most_count = ranked[0]
    least_fid, least_count = ranked[-1]

    if most_count >= least_count * 2 and most_count >= 10:
        return [NarrativeAngle(
            category="TRANSACTION_VOLUME_IDENTITY",
            headline=(
                f"{fname(most_fid)} made {most_count} roster moves this season. "
                f"{fname(least_fid)} made {least_count}"
            ),
            detail="", strength=1, franchise_ids=(most_fid, least_fid),
        )]
    return []


def _is_near_monotonic_growing(margins: list[float]) -> bool:
    """True if removing any single element yields a strictly growing sequence.

    A "near-growing" margin sequence has a clear upward trend with one
    deviation. For example, [10, 15, 12, 20] is near-growing because
    removing the 12 yields [10, 15, 20] which is strictly growing.

    Requires the input sequence to have length ≥3 (so the reduced
    sequence has length ≥2 for a meaningful monotonic check).
    """
    n = len(margins)
    if n < 3:
        return False
    for j in range(n):
        reduced = margins[:j] + margins[j + 1:]
        if all(reduced[i] < reduced[i + 1] for i in range(len(reduced) - 1)):
            return True
    return False


def _is_near_monotonic_shrinking(margins: list[float]) -> bool:
    """True if removing any single element yields a strictly shrinking sequence.

    Symmetric to ``_is_near_monotonic_growing``. See that function's
    docstring for the design rationale.
    """
    n = len(margins)
    if n < 3:
        return False
    for j in range(n):
        reduced = margins[:j] + margins[j + 1:]
        if all(reduced[i] > reduced[i + 1] for i in range(len(reduced) - 1)):
            return True
    return False


def detect_scoring_momentum_in_streak(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 49: Directional margin momentum during an active win streak.

    Walks backwards from ``target_week`` to find each franchise's current
    consecutive-win streak, then classifies the chronological margin
    sequence and fires when it shows clear directional movement. Requires
    a streak of at least 4 consecutive wins.

    Four firing tiers, checked in priority order:

    1. **Strictly growing**: every margin strictly greater than the one
       before. "Each win more dominant than the last."
    2. **Strictly shrinking**: every margin strictly less than the one
       before. "Still winning, but each result closer than the last."
    3. **Mostly growing**: not strictly monotonic, but removing any one
       margin yields a strictly growing sequence. "Margins mostly
       growing" — clear upward trend with one deviation.
    4. **Mostly shrinking**: symmetric to (3).

    Flat (all equal) or genuinely mixed (multiple deviations) sequences
    produce no angle — governance-compliant silence.

    **Voice guardrail**: the headline ALWAYS includes the full chronological
    margin sequence. For the "mostly" tiers, this anchors the claim in
    exact data and protects against creative-layer rewriting that might
    strip the "mostly" qualifier. The detail field names the directional
    quality so the model can frame it honestly.

    **Design note**: the near-monotonic tiers (3 & 4) exist because PFL
    Buddies' 2024-2025 production data produced zero strictly-monotonic
    4+ game streaks across 31 active-streak observations. The strict-only
    gate was unreachable in practice. The "mostly" tiers catch ~45% of real
    observations while preserving selectivity — genuinely mixed sequences
    remain silent. Calibrated against ``scripts/diagnose_streak_momentum_gate.py``.
    """
    # Build full week results per franchise (W/L) for the current season.
    fid_weekly: dict[str, dict[int, tuple[bool, float]]] = {}
    for m in all_matchups:
        if m.season != current_season or m.week > target_week or m.is_tie:
            continue
        for fid, won, margin in [
            (m.winner_id, True, m.margin), (m.loser_id, False, m.margin)
        ]:
            if fid not in fid_weekly:
                fid_weekly[fid] = {}
            fid_weekly[fid][m.week] = (won, margin)

    angles: list[NarrativeAngle] = []
    for fid in sorted(fid_weekly.keys()):
        weekly = fid_weekly[fid]
        # Walk backwards from target_week to find current win streak
        streak_margins: list[float] = []
        wk = target_week
        while wk >= 1 and wk in weekly:
            won, margin = weekly[wk]
            if won:
                streak_margins.insert(0, margin)
                wk -= 1
            else:
                break

        if len(streak_margins) < 4:
            continue

        margin_str = ", ".join(f"{m:.0f}" for m in streak_margins)
        n_games = len(streak_margins)

        # ── Tier 1: strictly growing ──
        if all(
            streak_margins[i] < streak_margins[i + 1]
            for i in range(len(streak_margins) - 1)
        ):
            angles.append(NarrativeAngle(
                category="SCORING_MOMENTUM_IN_STREAK",
                headline=(
                    f"{fname(fid)}'s {n_games}-game win streak "
                    f"has growing margins: {margin_str}"
                ),
                detail="Each win more dominant than the last.",
                strength=1, franchise_ids=(fid,),
            ))
        # ── Tier 2: strictly shrinking ──
        elif all(
            streak_margins[i] > streak_margins[i + 1]
            for i in range(len(streak_margins) - 1)
        ):
            angles.append(NarrativeAngle(
                category="SCORING_MOMENTUM_IN_STREAK",
                headline=(
                    f"{fname(fid)}'s {n_games}-game win streak "
                    f"has shrinking margins: {margin_str}"
                ),
                detail="Still winning, but each result closer than the last.",
                strength=1, franchise_ids=(fid,),
            ))
        # ── Tier 3: mostly growing (1 blip from strictly growing) ──
        elif _is_near_monotonic_growing(streak_margins):
            angles.append(NarrativeAngle(
                category="SCORING_MOMENTUM_IN_STREAK",
                headline=(
                    f"{fname(fid)}'s {n_games}-game win streak "
                    f"has mostly growing margins: {margin_str}"
                ),
                detail="Winning by wider margins on balance.",
                strength=1, franchise_ids=(fid,),
            ))
        # ── Tier 4: mostly shrinking (1 blip from strictly shrinking) ──
        elif _is_near_monotonic_shrinking(streak_margins):
            angles.append(NarrativeAngle(
                category="SCORING_MOMENTUM_IN_STREAK",
                headline=(
                    f"{fname(fid)}'s {n_games}-game win streak "
                    f"has mostly shrinking margins: {margin_str}"
                ),
                detail="Still winning, but margins tightening on balance.",
                strength=1, franchise_ids=(fid,),
            ))
    return angles


# ── Detector 38: SECOND_HALF_SURGE_COLLAPSE ──────────────────────────


def detect_second_half_surge_collapse(
    score_payloads: list[dict], target_week: int,
    *, change_threshold: float = 0.15,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 38: Scoring avg drops/rises 15%+ between season halves."""
    if target_week < 8:
        return []  # need enough weeks for a meaningful split

    midpoint = target_week // 2

    # Franchise weekly totals (starters only)
    fid_weeks: dict[str, dict[int, float]] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid:
            if fid not in fid_weeks:
                fid_weeks[fid] = {}
            fid_weeks[fid][week] = fid_weeks[fid].get(week, 0.0) + score

    angles: list[NarrativeAngle] = []
    for fid in sorted(fid_weeks.keys()):
        first_half = [s for w, s in fid_weeks[fid].items() if 1 <= w <= midpoint and s > 0]
        second_half = [s for w, s in fid_weeks[fid].items() if midpoint < w <= target_week and s > 0]
        if len(first_half) < 3 or len(second_half) < 3:
            continue

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        if avg_first < 1.0:
            continue

        change = (avg_second - avg_first) / avg_first
        if change <= -change_threshold:
            angles.append(NarrativeAngle(
                category="SECOND_HALF_SURGE_COLLAPSE",
                headline=(
                    f"{fname(fid)} averaged {avg_first:.1f} in weeks 1-{midpoint} "
                    f"but just {avg_second:.1f} in weeks {midpoint + 1}-{target_week} "
                    f"— a {abs(change):.0%} decline"
                ),
                detail="", strength=1, franchise_ids=(fid,),
            ))
        elif change >= change_threshold:
            angles.append(NarrativeAngle(
                category="SECOND_HALF_SURGE_COLLAPSE",
                headline=(
                    f"{fname(fid)} averaged {avg_first:.1f} in weeks 1-{midpoint} "
                    f"and {avg_second:.1f} in weeks {midpoint + 1}-{target_week} "
                    f"— a {change:.0%} surge"
                ),
                detail="", strength=1, franchise_ids=(fid,),
            ))

    return angles


# ── Detector 40: FRANCHISE_ALLTIME_SCORING ───────────────────────────


def detect_franchise_alltime_scoring(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    *, tenure_map: dict[str, int] | None = None,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 40: Total franchise scoring across seasons (tenure-scoped)."""
    filtered = _tenure_filter(all_matchups, current_season, target_week, tenure_map)
    if len({m.season for m in filtered}) < 2:
        return []

    # Sum points-for per franchise
    pf: dict[str, float] = {}
    for m in filtered:
        pf[m.winner_id] = pf.get(m.winner_id, 0.0) + m.winner_score
        pf[m.loser_id] = pf.get(m.loser_id, 0.0) + m.loser_score

    if len(pf) < 3:
        return []

    best_fid = max(pf, key=lambda f: pf[f])
    best_pts = pf[best_fid]
    tenure_label = ""
    if tenure_map and best_fid in tenure_map:
        tenure_label = " under current ownership"

    return [NarrativeAngle(
        category="FRANCHISE_ALLTIME_SCORING",
        headline=(
            f"{fname(best_fid)} has scored {best_pts:,.0f} total points{tenure_label} "
            f"— the most of any franchise"
        ),
        detail="", strength=1, franchise_ids=(best_fid,),
    )]


# ── Detector 43: WEEKLY_SCORING_RANK_DOMINANCE ──────────────────────


def detect_weekly_scoring_rank_dominance(
    score_payloads: list[dict], target_week: int,
    *, min_weeks_on_top: int = 4,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 43: Franchise finishes as top or bottom scorer unusually often."""
    # Weekly franchise totals (starters)
    fid_weeks: dict[str, dict[int, float]] = {}
    for p in score_payloads:
        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week > target_week or not p.get("is_starter"):
            continue
        fid = str(p.get("franchise_id", "")).strip()
        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            continue
        if fid:
            if fid not in fid_weeks:
                fid_weeks[fid] = {}
            fid_weeks[fid][week] = fid_weeks[fid].get(week, 0.0) + score

    if len(fid_weeks) < 3:
        return []

    # Count top-scorer finishes per franchise
    top_counts: dict[str, int] = {fid: 0 for fid in fid_weeks}
    all_weeks: set = set()
    for fid in fid_weeks:
        all_weeks.update(fid_weeks[fid].keys())

    for wk in all_weeks:
        week_scores = [(fid, fid_weeks[fid].get(wk, 0.0)) for fid in fid_weeks]
        week_scores.sort(key=lambda x: (-x[1], x[0]))
        if week_scores:
            top_counts[week_scores[0][0]] = top_counts.get(week_scores[0][0], 0) + 1

    best_fid = max(top_counts, key=lambda f: top_counts[f])
    best_count = top_counts[best_fid]
    others_max = max((c for f, c in top_counts.items() if f != best_fid), default=0)

    angles: list[NarrativeAngle] = []
    if best_count >= min_weeks_on_top and best_count >= others_max * 2:
        angles.append(NarrativeAngle(
            category="WEEKLY_SCORING_RANK_DOMINANCE",
            headline=(
                f"{fname(best_fid)} has finished as the week's top scorer "
                f"{best_count} times this season"
            ),
            detail=f"No other team has more than {others_max}.",
            strength=1, franchise_ids=(best_fid,),
        ))
    return angles


# ── Detector 44: SCHEDULE_STRENGTH ───────────────────────────────────


def detect_schedule_strength(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 44: Opponents' combined winning percentage."""
    # Current season W-L
    wins: dict[str, int] = {}
    losses: dict[str, int] = {}
    for m in all_matchups:
        if m.season != current_season or m.week > target_week or m.is_tie:
            continue
        wins[m.winner_id] = wins.get(m.winner_id, 0) + 1
        losses[m.loser_id] = losses.get(m.loser_id, 0) + 1

    all_fids = set(wins.keys()) | set(losses.keys())
    if len(all_fids) < 5:
        return []

    def _wpct(fid: str) -> float:
        w = wins.get(fid, 0)
        lo = losses.get(fid, 0)
        return w / (w + lo) if (w + lo) > 0 else 0.5

    # Opponents per franchise
    opponents: dict[str, list[str]] = {}
    for m in all_matchups:
        if m.season != current_season or m.week > target_week or m.is_tie:
            continue
        if m.winner_id not in opponents:
            opponents[m.winner_id] = []
        opponents[m.winner_id].append(m.loser_id)
        if m.loser_id not in opponents:
            opponents[m.loser_id] = []
        opponents[m.loser_id].append(m.winner_id)

    # Compute opponent strength per franchise
    opp_strength: dict[str, float] = {}
    for fid, opps in opponents.items():
        if not opps:
            continue
        opp_strength[fid] = sum(_wpct(o) for o in opps) / len(opps)

    if not opp_strength:
        return []

    toughest_fid = max(opp_strength, key=lambda f: opp_strength[f])
    easiest_fid = min(opp_strength, key=lambda f: opp_strength[f])

    angles: list[NarrativeAngle] = []
    if opp_strength[toughest_fid] - opp_strength[easiest_fid] >= 0.10:
        angles.append(NarrativeAngle(
            category="SCHEDULE_STRENGTH",
            headline=(
                f"{fname(toughest_fid)}'s opponents have a combined "
                f".{round(opp_strength[toughest_fid] * 1000):03d} winning percentage "
                f"— the toughest schedule"
            ),
            detail="", strength=1, franchise_ids=(toughest_fid,),
        ))
    return angles


# ── Detector 47: POINTS_AGAINST_LUCK ────────────────────────────────


def detect_points_against_luck(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    *, min_times: int = 3,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 47: Franchise faced opponent's season-high unusually often."""
    # Find each franchise's season-high score
    season_highs: dict[str, float] = {}
    for m in all_matchups:
        if m.season != current_season or m.week > target_week:
            continue
        for fid, score in [(m.winner_id, m.winner_score), (m.loser_id, m.loser_score)]:
            if fid not in season_highs or score > season_highs[fid]:
                season_highs[fid] = score

    # Count how many times each franchise faced an opponent's season-high
    faced_high: dict[str, int] = {}
    for m in all_matchups:
        if m.season != current_season or m.week > target_week or m.is_tie:
            continue
        # Did the winner score their season high against the loser?
        if season_highs.get(m.winner_id) == m.winner_score:
            faced_high[m.loser_id] = faced_high.get(m.loser_id, 0) + 1
        if season_highs.get(m.loser_id) == m.loser_score:
            faced_high[m.winner_id] = faced_high.get(m.winner_id, 0) + 1

    angles: list[NarrativeAngle] = []
    for fid in sorted(faced_high.keys()):
        if faced_high[fid] >= min_times:
            angles.append(NarrativeAngle(
                category="POINTS_AGAINST_LUCK",
                headline=(
                    f"{fname(fid)} has faced their opponent's season-best performance "
                    f"{faced_high[fid]} times"
                ),
                detail="The most in the league.",
                strength=1, franchise_ids=(fid,),
            ))
    return angles


# ── Detector 48: REPEAT_MATCHUP_PATTERN ──────────────────────────────


def detect_repeat_matchup_pattern(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    *, high_combined_threshold: float = 230.0, min_meetings: int = 4,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 48: Two franchises consistently produce high combined scores."""
    # Group meetings by franchise pair (all-time)
    pair_scores: dict[tuple[str, str], list[float]] = {}
    for m in all_matchups:
        if m.season > current_season or (m.season == current_season and m.week > target_week):
            continue
        ids = sorted([m.winner_id, m.loser_id])
        pair: tuple[str, str] = (ids[0], ids[1])
        combined = m.winner_score + m.loser_score
        if pair not in pair_scores:
            pair_scores[pair] = []
        pair_scores[pair].append(combined)

    angles: list[NarrativeAngle] = []
    for pair, scores in sorted(pair_scores.items()):
        if len(scores) < min_meetings:
            continue
        high_count = sum(1 for s in scores if s >= high_combined_threshold)
        if high_count >= len(scores) * 0.75 and high_count >= min_meetings:
            fid_a, fid_b = pair
            angles.append(NarrativeAngle(
                category="REPEAT_MATCHUP_PATTERN",
                headline=(
                    f"Every time {fid_a} and {fid_b} meet, the combined score "
                    f"exceeds {high_combined_threshold:.0f} — {high_count} of "
                    f"{len(scores)} meetings"
                ),
                detail="", strength=1, franchise_ids=pair,
            ))
    return angles


# ── Detector 39: CHAMPIONSHIP_HISTORY ────────────────────────────────


def detect_championship_history(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 39: Playoff and championship appearance counts.

    Only surfaces during playoff weeks of the current season.
    Playoff weeks are identified deterministically: weeks where the
    number of matchups is fewer than the regular-season mode.
    """
    # Check if this week IS a playoff week
    current_week_matchups = [
        m for m in all_matchups
        if m.season == current_season and m.week == target_week
    ]
    regular_count = _regular_season_matchup_count(all_matchups, current_season)
    if regular_count == 0 or len(current_week_matchups) >= regular_count:
        return []  # not a playoff week

    # Count championship appearances per franchise across all completed seasons
    champ_appearances: dict[str, int] = {}
    playoff_appearances: dict[str, int] = {}
    completed_seasons = {m.season for m in all_matchups if m.season < current_season}

    for s in completed_seasons:
        s_regular = _regular_season_matchup_count(all_matchups, s)
        if s_regular == 0:
            continue

        # Find championship week: last week with exactly 1 matchup (or fewest)
        season_matchups = [m for m in all_matchups if m.season == s]
        playoff_weeks = [m for m in season_matchups if len([
            x for x in season_matchups if x.week == m.week
        ]) < s_regular]

        # Track playoff participants
        for m in playoff_weeks:
            playoff_appearances[m.winner_id] = playoff_appearances.get(m.winner_id, 0) + 1
            playoff_appearances[m.loser_id] = playoff_appearances.get(m.loser_id, 0) + 1

        # Championship: the week with the fewest matchups (usually 1)
        if playoff_weeks:
            week_counts: dict[int, int] = {}
            for m in playoff_weeks:
                week_counts[m.week] = week_counts.get(m.week, 0) + 1
            champ_week = min(week_counts, key=lambda w: (week_counts[w], -w))
            champ_matchups = [m for m in playoff_weeks if m.week == champ_week]
            for m in champ_matchups:
                for fid in (m.winner_id, m.loser_id):
                    champ_appearances[fid] = champ_appearances.get(fid, 0) + 1

    if not champ_appearances:
        return []

    angles: list[NarrativeAngle] = []
    # Report franchises with most championship appearances
    best_fid = max(champ_appearances, key=lambda f: champ_appearances[f])
    best_count = champ_appearances[best_fid]
    if best_count >= 2:
        total_seasons = len(completed_seasons)
        angles.append(NarrativeAngle(
            category="CHAMPIONSHIP_HISTORY",
            headline=(
                f"{fname(best_fid)} has appeared in the championship matchup "
                f"{best_count} times in {total_seasons} seasons"
            ),
            detail="", strength=2, franchise_ids=(best_fid,),
        ))

    # Report franchise that never appeared
    all_fids = set()
    for m in all_matchups:
        all_fids.add(m.winner_id)
        all_fids.add(m.loser_id)
    never_champ = [f for f in sorted(all_fids) if f not in champ_appearances]
    if never_champ and len(completed_seasons) >= 3:
        for fid in never_champ[:1]:  # just report one
            angles.append(NarrativeAngle(
                category="CHAMPIONSHIP_HISTORY",
                headline=f"{fname(fid)} has never appeared in a championship matchup",
                detail=f"Across {len(completed_seasons)} seasons.",
                strength=1, franchise_ids=(fid,),
            ))

    return angles


# ── Detector 45: REGULAR_SEASON_VS_PLAYOFF ───────────────────────────


def detect_regular_season_vs_playoff(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 45: Regular season vs playoff record diverges.

    Only surfaces during playoff weeks.
    """
    current_week_matchups = [
        m for m in all_matchups
        if m.season == current_season and m.week == target_week
    ]
    regular_count = _regular_season_matchup_count(all_matchups, current_season)
    if regular_count == 0 or len(current_week_matchups) >= regular_count:
        return []

    # Split all historical matchups into regular season vs playoff
    reg_wins: dict[str, int] = {}
    reg_losses: dict[str, int] = {}
    playoff_wins: dict[str, int] = {}
    playoff_losses: dict[str, int] = {}

    completed_seasons = {m.season for m in all_matchups if m.season < current_season}
    for s in completed_seasons:
        s_regular = _regular_season_matchup_count(all_matchups, s)
        for m in all_matchups:
            if m.season != s or m.is_tie:
                continue
            season_week_count = len([x for x in all_matchups if x.season == s and x.week == m.week])
            if season_week_count >= s_regular:
                # Regular season
                reg_wins[m.winner_id] = reg_wins.get(m.winner_id, 0) + 1
                reg_losses[m.loser_id] = reg_losses.get(m.loser_id, 0) + 1
            else:
                # Playoff
                playoff_wins[m.winner_id] = playoff_wins.get(m.winner_id, 0) + 1
                playoff_losses[m.loser_id] = playoff_losses.get(m.loser_id, 0) + 1

    angles: list[NarrativeAngle] = []
    all_fids = set(reg_wins.keys()) | set(reg_losses.keys())

    for fid in sorted(all_fids):
        rw = reg_wins.get(fid, 0)
        rl = reg_losses.get(fid, 0)
        pw = playoff_wins.get(fid, 0)
        pl = playoff_losses.get(fid, 0)
        if (rw + rl) < 10 or (pw + pl) < 3:
            continue

        reg_pct = rw / (rw + rl)
        play_pct = pw / (pw + pl)
        if abs(reg_pct - play_pct) >= 0.20:
            angles.append(NarrativeAngle(
                category="REGULAR_SEASON_VS_PLAYOFF",
                headline=(
                    f"{fname(fid)} is {rw}-{rl} in the regular season "
                    f"but {pw}-{pl} in playoff games"
                ),
                detail="", strength=1, franchise_ids=(fid,),
            ))

    return angles


# ── Detector 50: THE_ALMOST ──────────────────────────────────────────


def detect_the_almost(
    all_matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    *, min_times: int = 3,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detector 50: Finished one game out of the playoffs multiple times.

    Only surfaces during playoff weeks. Identifies franchises that were
    one win away from a playoff spot in multiple seasons.
    """
    current_week_matchups = [
        m for m in all_matchups
        if m.season == current_season and m.week == target_week
    ]
    regular_count = _regular_season_matchup_count(all_matchups, current_season)
    if regular_count == 0 or len(current_week_matchups) >= regular_count:
        return []

    num_teams = regular_count * 2
    # Typical playoff field: top half makes playoffs (or top 6 of 10, etc.)
    # Use top half as approximation
    playoff_cutoff = num_teams // 2

    completed_seasons = {m.season for m in all_matchups if m.season < current_season}
    almost_counts: dict[str, int] = {}

    for s in completed_seasons:
        s_regular = _regular_season_matchup_count(all_matchups, s)
        # Build regular season standings
        wins: dict[str, int] = {}
        for m in all_matchups:
            if m.season != s or m.is_tie:
                continue
            season_week_count = len([x for x in all_matchups if x.season == s and x.week == m.week])
            if season_week_count >= s_regular:
                wins[m.winner_id] = wins.get(m.winner_id, 0) + 1

        if len(wins) < playoff_cutoff + 1:
            continue

        # Sort by wins descending
        ranked = sorted(wins.items(), key=lambda x: (-x[1], x[0]))
        if len(ranked) > playoff_cutoff:
            # The team just outside the playoff cutoff
            cutoff_wins = ranked[playoff_cutoff - 1][1]  # last playoff team's wins
            just_missed = ranked[playoff_cutoff]  # first team out
            if just_missed[1] == cutoff_wins - 1:
                almost_counts[just_missed[0]] = almost_counts.get(just_missed[0], 0) + 1

    angles: list[NarrativeAngle] = []
    for fid in sorted(almost_counts.keys()):
        if almost_counts[fid] >= min_times:
            angles.append(NarrativeAngle(
                category="THE_ALMOST",
                headline=(
                    f"{fname(fid)} has finished one game out of the playoffs "
                    f"{almost_counts[fid]} times in {len(completed_seasons)} seasons"
                ),
                detail="", strength=1, franchise_ids=(fid,),
            ))
    return angles


# ── Helpers ──────────────────────────────────────────────────────────


def _regular_season_matchup_count(
    matchups: Sequence[HistoricalMatchup], season: int,
) -> int:
    """Determine the regular-season matchup count for a season.

    Returns the most common (mode) number of matchups per week.
    In a 10-team league this is 5. Weeks with fewer matchups are playoffs.
    Returns 0 if no data.
    """
    week_counts: dict[int, int] = {}
    for m in matchups:
        if m.season == season:
            week_counts[m.week] = week_counts.get(m.week, 0) + 1
    if not week_counts:
        return 0
    # Mode: most common count
    count_freq: dict[int, int] = {}
    for cnt in week_counts.values():
        count_freq[cnt] = count_freq.get(cnt, 0) + 1
    return max(count_freq, key=lambda c: count_freq[c])


def _tenure_filter(
    matchups: Sequence[HistoricalMatchup],
    current_season: int, target_week: int,
    tenure_map: dict[str, int] | None,
) -> list[HistoricalMatchup]:
    """Filter matchups to tenure scope and through current week."""
    out = []
    for m in matchups:
        if tenure_map:
            t_w = tenure_map.get(m.winner_id)
            t_l = tenure_map.get(m.loser_id)
            if t_w and m.season < t_w:
                continue
            if t_l and m.season < t_l:
                continue
        if m.season < current_season or (m.season == current_season and m.week <= target_week):
            out.append(m)
    return out


def _season_final_record(
    matchups: Sequence[HistoricalMatchup], franchise_id: str, season: int,
) -> tuple[int, int] | None:
    """Get final W-L record for a franchise in a season."""
    wins = losses = 0
    for m in matchups:
        if m.season != season or m.is_tie:
            continue
        if m.winner_id == franchise_id:
            wins += 1
        elif m.loser_id == franchise_id:
            losses += 1
    if wins + losses == 0:
        return None
    return (wins, losses)


# ── Public API ───────────────────────────────────────────────────────


def detect_franchise_deep_angles_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    tenure_map: dict[str, int] | None = None,
    pname: NameFn = _identity,
    fname: NameFn = _identity,
) -> list[NarrativeAngle]:
    """Detect all Dimension 7-9 franchise deep angles for a given week.

    Returns angles sorted by strength descending then category ascending.
    Returns empty list when insufficient data exists.
    """
    score_payloads = _load_season_player_scores_flat(db_path, league_id, season)
    all_matchups = _load_all_matchups_flat(db_path, league_id)
    positions = _load_player_positions(db_path, league_id, season)

    all_angles: list[NarrativeAngle] = []

    # ── Dimension 7: Franchise Scoring Patterns ──
    if score_payloads:
        all_angles.extend(detect_scoring_concentration(score_payloads, week, pname=pname, fname=fname))
        all_angles.extend(detect_scoring_volatility(score_payloads, week, fname=fname))
        all_angles.extend(detect_star_explosion_count(score_payloads, week, pname=pname, fname=fname))
        all_angles.extend(detect_second_half_surge_collapse(score_payloads, week, fname=fname))
        all_angles.extend(detect_weekly_scoring_rank_dominance(score_payloads, week, fname=fname))
        if positions:
            all_angles.extend(detect_positional_strength(score_payloads, positions, week, fname=fname))

    # ── Dimension 8: Bench & Lineup Decisions ──
    if score_payloads and all_matchups:
        all_angles.extend(detect_bench_cost_game(score_payloads, all_matchups, season, week, fname=fname, pname=pname))
    if score_payloads:
        all_angles.extend(detect_chronic_bench_mismanagement(score_payloads, week, fname=fname))
        all_angles.extend(detect_perfect_lineup_week(score_payloads, week, fname=fname))

    # ── Dimension 9: Franchise History & Identity ──
    if all_matchups:
        all_angles.extend(detect_close_game_record(
            all_matchups, season, week, tenure_map=tenure_map, fname=fname))
        all_angles.extend(detect_season_trajectory_match(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_lucky_record(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_scoring_momentum_in_streak(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_franchise_alltime_scoring(
            all_matchups, season, week, tenure_map=tenure_map, fname=fname))
        all_angles.extend(detect_schedule_strength(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_points_against_luck(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_repeat_matchup_pattern(all_matchups, season, week, fname=fname))
        # Playoff-dependent detectors (only fire during playoff weeks)
        all_angles.extend(detect_championship_history(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_regular_season_vs_playoff(all_matchups, season, week, fname=fname))
        all_angles.extend(detect_the_almost(all_matchups, season, week, fname=fname))
        if score_payloads:
            all_angles.extend(detect_the_bridesmaid(
                score_payloads, all_matchups, season, week, fname=fname))

    # Detector 41 (TRANSACTION_VOLUME_IDENTITY) disabled.
    # Aggregate transaction counts are unverifiable by league members and
    # the model also counts individual facts bullets to produce its own
    # aggregates, which are wrong. Per governance: silence over fabrication.
    # FAAB spending in the writer room context captures spending patterns.
    # Individual transaction bullets in the facts block cover specific moves.
    # Re-enable only if verified per-team weekly counts can be produced.

    # Deterministic sort
    all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))
    return all_angles
