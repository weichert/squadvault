"""Hall of Fame & Shame Render v1 — A1 surface's markdown rendering.

Pure rendering functions for A1's archive presentation per A1 specification
(`_observations/OBSERVATIONS_2026_05_11_PHASE_11_A1_SPECIFICATION.md`)
§§3.5 / 3.6 / 3.7 / 5.1.

Each render function takes the output of a `hall_of_fame_aggregations_v1`
derivation function plus a `name_map: dict[str, str]` (franchise_id →
display name) and returns a markdown string. No I/O; no file writes.
The companion script `scripts/generate_hall_of_fame_archive.py` wires
loading + name resolution + rendering + file writing into an operational
unit.

Contract (per A1 spec §§3.6, 6.2):

- Every rendered markdown file declares its scope at the top via
  `SCOPE_DECLARATION_LINE`. Per §6.2 surface-specific invariant: A1's
  surface displays the scope-declaration line per §3.6.
- Per §3.7 normalization: worst-seasons renders absolute W-L-T as the
  primary record column, with `FORMAT_SHIFT_FOOTNOTE` acknowledging
  the 2021 14-→-15-game format change. Optional secondary columns
  (win-%, per-game PF) help cross-era comparison without forcing
  era-aware reading.
- Per §3.5: A1's push events at notable moments are surfaced
  operationally by the push script, not by the archive's markdown
  content. This module's outputs are the browse-cadenced archive
  shape, not the push-event shape.

Governance:

- Pure functions. Deterministic. No I/O. No side effects.
- No commissioner-curated labels per §6.1 D3-Alpha invariant: every
  rendered value traces to an aggregation output's field, which in
  turn traces to a canonical event per the aggregation module's
  contract.
- Markdown structure is the layout-invariant contract that
  `Tests/test_hall_of_fame_archive_layout_v1.py` enforces when the
  archive exists.
"""

from __future__ import annotations

from collections.abc import Sequence

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    ChampionshipResult,
)
from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    SeasonRecord,
)

# ── Module-level constants ───────────────────────────────────────────

#: Scope-declaration line displayed at the top of every A1 archive page.
#: Per spec §3.6: A1 must declare its temporal scope honestly. The
#: invariant the layout test enforces: every archive markdown file
#: contains this line (or its substantive equivalent after a future
#: revision-point copy edit per §7 Governance).
SCOPE_DECLARATION_LINE = (
    "The Digital Archive: PFL Buddies, 2010 – 2025. "
    "The league has been running continuously since 1983; "
    "the archive begins where the digital records begin."
)

#: Footnote text appended to the worst-seasons page per spec §3.7
#: normalization disposition. Acknowledges the 2021 format shift
#: without normalizing absolute counts away.
FORMAT_SHIFT_FOOTNOTE = (
    "*Regular-season game count per franchise: 14 games per season "
    "(2010-2020); 15 games per season (2021+). The 2021 format shift "
    "expanded the regular season by one game; absolute win/loss totals "
    "are not strictly comparable across the boundary. The Win % and "
    "PF/Game columns are era-stable.*"
)

#: H1 titles, used by render functions and tested for presence in the
#: rendered markdown.
TITLE_INDEX = "PFL Buddies — Hall of Fame & Shame"
TITLE_CHAMPIONSHIP_ROLL = "Championship Roll"
TITLE_WORST_SEASONS = "Worst-Season Tracking"
TITLE_BLOWOUTS_HALL = "Blowouts Hall"


# ── Helpers ──────────────────────────────────────────────────────────


def _resolve(name_map: dict[str, str], franchise_id: str) -> str:
    """Resolve a franchise_id to its display name.

    Falls back to the franchise_id itself if the resolver lacks an
    entry — per the existing pattern in
    `league_history_v1.resolve_franchise_name_any_season` (return raw
    ID if not found). This is conservative: A1 displays what the
    substrate provides; missing names stay missing.
    """
    return name_map.get(franchise_id, franchise_id)


def _format_record(wins: int, losses: int, ties: int) -> str:
    """Format a W-L-T record as 'W-L-T'. Hides ties when zero."""
    if ties == 0:
        return f"{wins}-{losses}"
    return f"{wins}-{losses}-{ties}"


def _win_pct(record: SeasonRecord) -> float:
    """Compute win % for a SeasonRecord. Ties count half per convention."""
    total_games = record.wins + record.losses + record.ties
    if total_games == 0:
        return 0.0
    return (record.wins + 0.5 * record.ties) / total_games


def _pf_per_game(record: SeasonRecord) -> float:
    """Compute PF per game for a SeasonRecord. Returns 0.0 if no games."""
    total_games = record.wins + record.losses + record.ties
    if total_games == 0:
        return 0.0
    return record.points_for / total_games


def _scope_block() -> str:
    """Standard scope-declaration block prefixed to every page."""
    return f"{SCOPE_DECLARATION_LINE}\n"


# ── Rendering: Championship Roll ─────────────────────────────────────


def render_championship_roll_markdown(
    results: Sequence[ChampionshipResult],
    name_map: dict[str, str],
) -> str:
    """Render the Championship Roll sub-shape per spec §3.3 / §5.1.

    Produces a markdown page with:
    - H1 title and scope-declaration line.
    - Per-season championship table (sorted ascending by season per
      `compute_championship_roll`'s contract): Season, Champion,
      Runner-Up, Championship Week, Score.
    - Aggregate per-franchise title counts, sorted by titles
      descending.

    Args:
        results: Aggregation output from `compute_championship_roll`.
            Expected sort: season ascending.
        name_map: franchise_id → display name. Missing entries fall
            back to the raw franchise_id.

    Returns:
        Markdown string. Empty `results` produces a "no data" page;
        the scope-declaration and title still render.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_CHAMPIONSHIP_ROLL}")
    lines.append("")
    lines.append(_scope_block())

    if not results:
        lines.append("*No championship data available.*")
        lines.append("")
        return "\n".join(lines)

    # Per-season table.
    lines.append("## Champions by Season")
    lines.append("")
    lines.append("| Season | Champion | Runner-Up | Week | Score |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        champ = _resolve(name_map, r.champion_id)
        runner = _resolve(name_map, r.runner_up_id)
        score = (
            f"{r.champion_score:.2f} to {r.runner_up_score:.2f}"
            if not r.is_tie
            else f"{r.champion_score:.2f}-{r.runner_up_score:.2f} (tie)"
        )
        lines.append(
            f"| {r.season} | {champ} | {runner} | {r.championship_week} | {score} |"
        )
    lines.append("")

    # Aggregate per-franchise title counts.
    title_counts: dict[str, int] = {}
    for r in results:
        title_counts[r.champion_id] = title_counts.get(r.champion_id, 0) + 1

    lines.append("## Titles by Franchise")
    lines.append("")
    lines.append("| Franchise | Titles | Seasons |")
    lines.append("|---|---|---|")
    # Sort: titles desc, then franchise display name asc for stability.
    ordered_fids = sorted(
        title_counts.keys(),
        key=lambda fid: (-title_counts[fid], _resolve(name_map, fid)),
    )
    for fid in ordered_fids:
        seasons_won = sorted(r.season for r in results if r.champion_id == fid)
        seasons_str = ", ".join(str(s) for s in seasons_won)
        lines.append(
            f"| {_resolve(name_map, fid)} | {title_counts[fid]} | {seasons_str} |"
        )
    lines.append("")

    return "\n".join(lines)


# ── Rendering: Worst-Season Tracking ─────────────────────────────────


def render_worst_seasons_markdown(
    records: Sequence[SeasonRecord],
    name_map: dict[str, str],
    top_n: int = 10,
) -> str:
    """Render the Worst-Season Tracking sub-shape per spec §3.3 / §5.1 / §3.7.

    Produces a markdown page with:
    - H1 title and scope-declaration line.
    - Top-N worst-season records: Rank, Franchise, Season, W-L-T,
      PF, Win %, PF/Game. Per §3.7 normalization disposition:
      absolute counts primary; win % and PF/game secondary for
      cross-era comparison.
    - Format-shift footnote acknowledging the 2021 14-→-15-game
      change (per §3.7 invariant).

    Args:
        records: Aggregation output from `compute_all_season_records`.
            Expected sort: worst-first (most losses; ties broken by
            ascending PF).
        name_map: franchise_id → display name. Missing entries fall
            back to the raw franchise_id.
        top_n: Number of worst-season rows to render. Defaults to 10.
            Must be non-negative.

    Returns:
        Markdown string. Empty `records` produces a "no data" page.

    Raises:
        ValueError: if `top_n` is negative.
    """
    if top_n < 0:
        raise ValueError(f"top_n must be non-negative; got {top_n}")

    lines: list[str] = []
    lines.append(f"# {TITLE_WORST_SEASONS}")
    lines.append("")
    lines.append(_scope_block())

    if not records:
        lines.append("*No season-record data available.*")
        lines.append("")
        return "\n".join(lines)

    selected = list(records[:top_n])

    lines.append("| Rank | Franchise | Season | Record | PF | Win % | PF/Game |")
    lines.append("|---|---|---|---|---|---|---|")
    for rank, r in enumerate(selected, start=1):
        franchise = _resolve(name_map, r.franchise_id)
        record_str = _format_record(r.wins, r.losses, r.ties)
        win_pct = _win_pct(r)
        pf_per_game = _pf_per_game(r)
        lines.append(
            f"| {rank} | {franchise} | {r.season} | {record_str} | "
            f"{r.points_for:.2f} | {win_pct:.3f} | {pf_per_game:.2f} |"
        )
    lines.append("")
    lines.append(FORMAT_SHIFT_FOOTNOTE)
    lines.append("")

    return "\n".join(lines)


# ── Rendering: Blowouts Hall ─────────────────────────────────────────


def render_blowouts_hall_markdown(
    matchups: Sequence[HistoricalMatchup],
    name_map: dict[str, str],
) -> str:
    """Render the Blowouts Hall sub-shape per spec §3.3 / §5.1.

    Produces a markdown page with:
    - H1 title and scope-declaration line.
    - Top-N matchup rows: Rank, Season, Week, Winner, Score, Loser,
      Score, Margin. Per §3.7: no normalization needed (margin is
      era-stable).

    Args:
        matchups: Aggregation output from `compute_blowouts_hall`.
            Expected sort: margin descending.
        name_map: franchise_id → display name. Missing entries fall
            back to the raw franchise_id.

    Returns:
        Markdown string. Empty `matchups` produces a "no data" page.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_BLOWOUTS_HALL}")
    lines.append("")
    lines.append(_scope_block())

    if not matchups:
        lines.append("*No matchup data available.*")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        "| Rank | Season | Week | Winner | Score | Loser | Score | Margin |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for rank, m in enumerate(matchups, start=1):
        winner = _resolve(name_map, m.winner_id)
        loser = _resolve(name_map, m.loser_id)
        lines.append(
            f"| {rank} | {m.season} | {m.week} | {winner} | "
            f"{m.winner_score:.2f} | {loser} | {m.loser_score:.2f} | "
            f"{m.margin:.2f} |"
        )
    lines.append("")

    return "\n".join(lines)


# ── Rendering: Index page ────────────────────────────────────────────


def render_index_markdown() -> str:
    """Render the index page per spec §5.1 / §6.4 layout invariant.

    The index is the entry point. It declares the archive's scope
    and links to the three sub-shape pages. The index does not embed
    aggregation content — that lives on the per-sub-shape pages.

    Per §6.4 layout invariant: `index.md` is the entry point and
    contains the scope-declaration header.

    Returns:
        Markdown string. Always non-empty; does not depend on
        substrate data.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_INDEX}")
    lines.append("")
    lines.append(_scope_block())
    lines.append("This archive surfaces three views of the digital era:")
    lines.append("")
    lines.append(
        f"- [{TITLE_CHAMPIONSHIP_ROLL}](./championship_roll.md) — "
        "per-season league champions; aggregate title counts."
    )
    lines.append(
        f"- [{TITLE_WORST_SEASONS}](./worst_seasons.md) — "
        "the league's worst-record seasons, top-N."
    )
    lines.append(
        f"- [{TITLE_BLOWOUTS_HALL}](./blowouts_hall.md) — "
        "the league's largest single-week margins, top-N."
    )
    lines.append("")
    lines.append(
        "Content is regenerated from canonical league events at the "
        "commissioner's election; the regeneration is operationally "
        "deterministic, and the git history is the archive's "
        "version history."
    )
    lines.append("")

    return "\n".join(lines)
