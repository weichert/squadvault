"""Per-matchup current-state anchors for the weekly recap prompt.

Surfaces the derived facts the model otherwise fabricates -- this pair's
all-time head-to-head, each side's current streak, each side's season-to-date
record -- scoped to the week's matchups, as-of-week, with explicit absence so
the model cites rather than invents. Pure render over league_history_v1
computations; creates no new facts.

Source-of-truth contract: H2H and current streak come from league_history_v1
(compute_head_to_head, compute_current_streaks). Callers MUST pass `matchups`
already scoped as-of-week -- e.g. league_history_v1.load_all_matchups(
as_of_season=season, as_of_week=week) -- which is inclusive of the as-of week,
matching the verifier's matchup window. This renderer does no scoping itself,
so the values it emits equal what the verifier computes over the same window.
"""
from __future__ import annotations

from collections.abc import Sequence

from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    compute_current_streaks,
    compute_head_to_head,
)


def _season_record_asof(
    matchups: Sequence[HistoricalMatchup], franchise_id: str, season: int
) -> tuple[int, int, int]:
    """Wins-losses-ties for a franchise in `season` from the (as-of-scoped)
    matchups -- a plain tally; future weeks are already excluded upstream."""
    w = ls = t = 0
    for m in matchups:
        if m.season != season:
            continue
        if franchise_id not in (m.winner_id, m.loser_id):
            continue
        if m.is_tie:
            t += 1
        elif m.winner_id == franchise_id:
            w += 1
        else:
            ls += 1
    return w, ls, t


def _streak_phrase(streak: tuple[str, int]) -> str:
    kind, n = streak
    if kind == "none" or n <= 0:
        return "no active streak"
    return f"a {n}-game {'winning' if kind == 'win' else 'losing'} streak"


def render_matchup_anchors_for_prompt(
    *,
    matchups: Sequence[HistoricalMatchup],
    week_pairs: Sequence[tuple[str, str]],
    current_season: int,
    week: int,
    name_map: dict[str, str] | None = None,
) -> str:
    """Render a per-matchup anchor block, or "" when there are no pairs.

    `matchups` MUST be as-of-week scoped (inclusive). `week_pairs` is the
    franchise-id pairs playing this week. All values are through the as-of week.
    """
    if not week_pairs:
        return ""

    def nm(fid: str) -> str:
        if name_map and fid in name_map:
            return name_map[fid]
        return fid

    streaks = compute_current_streaks(matchups)

    lines: list[str] = [
        f"Per-matchup anchors (through week {week}) -- cite these exactly; do "
        "not infer, round, or invent. Where a value reads 'no active streak', "
        "'no prior meetings', or '0-0', say so or stay silent -- never invent "
        "a streak, record, or series history that is not stated here:",
    ]

    for a, b in week_pairs:
        lines.append(f"- {nm(a)} vs {nm(b)}:")

        h2h = compute_head_to_head(matchups, a, b)
        mt = h2h.total_meetings
        mt_str = f"{mt} meeting" + ("s" if mt != 1 else "")
        if mt == 0:
            lines.append("    - All-time head-to-head: no prior meetings.")
        elif h2h.a_wins == h2h.b_wins:
            tie_suffix = f"-{h2h.ties}" if h2h.ties else ""
            lines.append(
                f"    - All-time head-to-head: tied {h2h.a_wins}-{h2h.b_wins}"
                f"{tie_suffix} ({mt_str})."
            )
        else:
            if h2h.a_wins > h2h.b_wins:
                leader, lw, ll = a, h2h.a_wins, h2h.b_wins
            else:
                leader, lw, ll = b, h2h.b_wins, h2h.a_wins
            tie_suffix = f"-{h2h.ties}" if h2h.ties else ""
            lines.append(
                f"    - All-time head-to-head: {nm(leader)} leads {lw}-{ll}"
                f"{tie_suffix} ({mt_str})."
            )

        for fid in (a, b):
            w, ls, t = _season_record_asof(matchups, fid, current_season)
            if w == 0 and ls == 0 and t == 0:
                rec = "0-0 (no games yet this season)"
            else:
                rec = f"{w}-{ls}" + (f"-{t}" if t else "")
            lines.append(
                f"    - {nm(fid)}: season {rec}; current "
                f"{_streak_phrase(streaks.get(fid, ('none', 0)))} "
                f"(through week {week})."
            )

    return "\n".join(lines) + "\n\n"
