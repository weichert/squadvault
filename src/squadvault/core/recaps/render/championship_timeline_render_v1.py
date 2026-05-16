"""Championship Timeline Render v1 — A3 surface's markdown rendering.

Pure rendering functions for A3's archive presentation per A3
specification
(`_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_SPECIFICATION.md`)
§§3.1 / 3.6 / 5.1.

Each render function takes the output of a
`championship_timeline_aggregations_v1` derivation function plus a
`name_map: dict[str, str]` (franchise_id → display name) and returns a
markdown string. No I/O; no file writes. The companion script
`scripts/generate_championship_timeline_archive.py` wires loading +
name resolution + rendering + file writing into an operational unit.

Contract (per A3 spec §§3.6, 6.1, 6.4):

- Every rendered markdown file declares its scope at the top via
  `SCOPE_DECLARATION_LINE`. Per §3.6: A3's scope declaration is
  explicit and honest about the temporal boundary — it does not claim
  "the league's full playoff history" without the 2010-onward
  qualification, and it does not claim "17 seasons" (the digital era
  is 16 seasons).
- The Per-Season Playoff Bracket page carries the bracket-shape
  framing note (`BRACKET_SHAPE_FRAMING`) per §3.6. Both digital-era
  eras present as a clean 3-round bracket after the W17/W18
  collapse-by-content rule; the regular season expanded from 14 to 15
  games at the 2021 format shift, so the playoff weeks shifted one
  week later. The note describes the bracket *structure*, not specific
  week numbers — the per-season brackets carry the actual weeks from
  the substrate.
- The Per-Season Playoff Bracket page cross-links to A1's
  `championship_roll.md` per the §3.1 absorption-finding boundary:
  A3 surfaces the preliminary and semifinal rounds A1's
  championship-roll column does not; it does not re-render A1's
  championship-week content.
- No commissioner-curated labels per §6.1 D3-Alpha invariant: every
  rendered value traces to an aggregation output's field, which in
  turn traces to a canonical `WEEKLY_MATCHUP_RESULT` event per the
  aggregation module's contract.
- Markdown structure is the layout-invariant contract that
  `Tests/test_championship_timeline_archive_layout_v1.py` enforces
  when the archive exists.

Governance:

- Pure functions. Deterministic. No I/O. No side effects.
- A3 is not a real-time bracket tracker (§6.7): these render functions
  produce the once-per-year retrospective archive shape; they have no
  incremental in-season mode.
"""

from __future__ import annotations

from collections.abc import Sequence

from squadvault.core.recaps.context.championship_timeline_aggregations_v1 import (
    BridesmaidRecord,
    CrossSeasonPlayoffRecords,
    SeasonBracket,
)

# ── Module-level constants ───────────────────────────────────────────

#: Scope-declaration line displayed at the top of every A3 archive
#: page. Per A3 spec §3.6: A3 must declare its temporal scope honestly.
#: The invariant the layout test enforces: every archive markdown file
#: contains this line (or its substantive equivalent after a future
#: revision-point copy edit per §7 Governance). The "16 seasons"
#: phrasing is deliberate — the digital era is 16 seasons, not the
#: legacy "17" approximation.
SCOPE_DECLARATION_LINE = (
    "The Championship Timeline: PFL Buddies' playoff history, "
    "2010 – 2025. Sixteen seasons of digital records; the league has "
    "been running since well before the digital era, and the timeline "
    "begins where the canonical playoff substrate begins."
)

#: Bracket-shape framing note appended to the per-season playoff
#: bracket page per A3 spec §3.6. Notes the two-era distinction
#: (the 2021 regular-season expansion shifted the playoff weeks one
#: week later) and the W17/W18 collapse-by-content rule. It describes
#: the bracket *structure*; the per-season brackets below it carry the
#: actual week numbers from the substrate.
BRACKET_SHAPE_FRAMING = (
    "*Across the digital era, every season's playoffs resolve as a "
    "clean three-round bracket: preliminary, semifinal, championship. "
    "The 2021 format shift expanded the regular season from 14 to 15 "
    "games, so for 2021 and later the playoff weeks fall one week "
    "later on the calendar. For those seasons the canonical substrate "
    "also carries a duplicate, verbatim-identical championship row in "
    "the following week; the timeline collapses that duplicate by "
    "content and presents the single championship round. The week "
    "numbers shown below are the substrate's own.*"
)

#: Rank-derivation note appended to the leaderboard pages. Per A3 spec
#: §6.1 / §6.8: substrate-derived ranks compute at render time. The
#: note acknowledges this to the reader; the rendered ranks are
#: numeric rank columns, not frozen narrative ordinal claims.
RANK_DERIVATION_NOTE = (
    "*Ranks are computed from the current substrate at archive "
    "regeneration. If the substrate changes, the ranks change.*"
)

#: Relative path from `playoff_brackets.md` to A1's championship-roll
#: page. The cross-link target per A3 spec §3.1 / §6.4: A3 does not
#: re-render A1's championship-week content.
CHAMPIONSHIP_ROLL_CROSSLINK = (
    "../hall_of_fame_and_shame/championship_roll.md"
)

#: H1 titles, used by render functions and tested for presence in the
#: rendered markdown.
TITLE_INDEX = "PFL Buddies — Championship Timeline"
TITLE_PLAYOFF_BRACKETS = "Per-Season Playoff Brackets"
TITLE_PLAYOFF_RECORDS = "Cross-Season Playoff Records"
TITLE_BRIDESMAIDS = "Bridesmaids"


# ── Helpers ──────────────────────────────────────────────────────────


def _resolve(name_map: dict[str, str], franchise_id: str) -> str:
    """Resolve a franchise_id to its display name.

    Falls back to the franchise_id itself if the resolver lacks an
    entry — per the existing pattern in
    `league_history_v1.build_cross_season_name_resolver` (raw ID if
    not found). This is conservative: A3 displays what the substrate
    provides; missing names stay missing.
    """
    return name_map.get(franchise_id, franchise_id)


def _resolve_season(
    season_map: dict[tuple[str, int], str],
    franchise_id: str,
    season: int,
) -> str:
    """Resolve a franchise_id to its era-correct display name.

    Uses (franchise_id, season) key so historical results are
    attributed to the name that existed in that season. Falls back
    to the raw franchise_id if not found.
    """
    return season_map.get((franchise_id, season), franchise_id)


def _scope_block() -> str:
    """Standard scope-declaration block prefixed to every page."""
    return f"{SCOPE_DECLARATION_LINE}\n"


def _format_score(winner_score: float, loser_score: float, is_tie: bool) -> str:
    """Format a matchup score string, matching A1's championship-roll style."""
    if is_tie:
        return f"{winner_score:.2f}-{loser_score:.2f} (tie)"
    return f"{winner_score:.2f} to {loser_score:.2f}"


# ── Rendering: Per-Season Playoff Brackets ───────────────────────────


def render_playoff_brackets_markdown(
    brackets: Sequence[SeasonBracket],
    season_map: dict[tuple[str, int], str],
) -> str:
    """Render the Per-Season Playoff Bracket sub-shape per spec §3.1 / §5.1.

    Produces a markdown page with:
    - H1 title and scope-declaration line.
    - The bracket-shape framing note per §3.6.
    - A cross-link to A1's championship-roll page per §3.1 / §6.4.
    - One section per season (ascending), each with its rounds in
      bracket order (preliminary first, championship last); each round
      is a small table of its matchups.

    Args:
        brackets: Aggregation output from `compute_playoff_bracket`.
            Expected sort: season ascending.
        season_map: (franchise_id, season) -> display name. Enables
            era-correct attribution for per-season bracket rows.
            Missing entries fall back to the raw franchise_id.

    Returns:
        Markdown string. Empty `brackets` produces a "no data" page;
        the scope-declaration, title, and framing still render.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_PLAYOFF_BRACKETS}")
    lines.append("")
    lines.append(_scope_block())
    lines.append(BRACKET_SHAPE_FRAMING)
    lines.append("")
    lines.append(
        "For the championship-week result per season — and the "
        "aggregate title counts — see the "
        f"[Championship Roll]({CHAMPIONSHIP_ROLL_CROSSLINK}) in the "
        "Hall of Fame & Shame archive. This page surfaces the full "
        "bracket: the preliminary and semifinal rounds the "
        "Championship Roll does not cover."
    )
    lines.append("")

    if not brackets:
        lines.append("*No playoff bracket data available.*")
        lines.append("")
        return "\n".join(lines)

    for bracket in brackets:
        lines.append(f"## {bracket.season}")
        lines.append("")
        for rnd in bracket.rounds:
            lines.append(f"### {rnd.round_label} (Week {rnd.week})")
            lines.append("")
            lines.append("| Winner | Score | Loser |")
            lines.append("|---|---|---|")
            for m in rnd.matchups:
                winner = _resolve_season(season_map, m.winner_id, bracket.season)
                loser = _resolve_season(season_map, m.loser_id, bracket.season)
                score = _format_score(
                    m.winner_score, m.loser_score, m.is_tie,
                )
                lines.append(f"| {winner} | {score} | {loser} |")
            lines.append("")

    return "\n".join(lines)


# ── Rendering: Cross-Season Playoff Records ──────────────────────────


def render_playoff_records_markdown(
    records: CrossSeasonPlayoffRecords,
    name_map: dict[str, str],
    top_n: int = 10,
) -> str:
    """Render the Cross-Season Playoff Records sub-shape per spec §3.1 / §3.8.

    Produces a markdown page with four leaderboard sections, one per
    dimension (all four ship at v1 per §3.8):
    - Playoff-Season Appearances (per-season set semantics).
    - Championship-Matchup Appearances.
    - Longest Playoff-Active Streak.
    - Longest Playoff-Drought Streak.

    Each section is a top-N table sorted by its own dimension. The
    drought section is shown alongside the active section per §3.8:
    the dense-field fact is part of the league's identity and the
    symmetry is more substrate-honest than showing only the active
    dimension.

    Args:
        records: Aggregation output from
            `compute_cross_season_playoff_records`.
        name_map: franchise_id → display name. Missing entries fall
            back to the raw franchise_id.
        top_n: Number of rows per leaderboard. Defaults to 10. Must be
            non-negative.

    Returns:
        Markdown string. Empty `records.per_franchise` produces a
        "no data" page.

    Raises:
        ValueError: if `top_n` is negative.
    """
    if top_n < 0:
        raise ValueError(f"top_n must be non-negative; got {top_n}")

    lines: list[str] = []
    lines.append(f"# {TITLE_PLAYOFF_RECORDS}")
    lines.append("")
    lines.append(_scope_block())

    if not records.per_franchise:
        lines.append("*No playoff-record data available.*")
        lines.append("")
        return "\n".join(lines)

    n = records.total_seasons
    lines.append(
        f"Across {n} digital-era season{'s' if n != 1 else ''} of "
        "PFL Buddies playoff history."
    )
    lines.append("")

    def _leaderboard(
        title: str,
        sort_key,
        value_fn,
        value_header: str,
    ) -> None:
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"| Rank | Franchise | {value_header} |")
        lines.append("|---|---|---|")
        ordered = sorted(records.per_franchise, key=sort_key)
        for rank, r in enumerate(ordered[:top_n], start=1):
            franchise = _resolve(name_map, r.franchise_id)
            lines.append(f"| {rank} | {franchise} | {value_fn(r)} |")
        lines.append("")

    _leaderboard(
        "Playoff-Season Appearances",
        lambda r: (-r.playoff_season_count, r.franchise_id),
        lambda r: r.playoff_season_count,
        "Playoff Seasons",
    )
    _leaderboard(
        "Championship-Matchup Appearances",
        lambda r: (-r.championship_appearance_count, r.franchise_id),
        lambda r: r.championship_appearance_count,
        "Championship Appearances",
    )
    _leaderboard(
        "Longest Playoff-Active Streak",
        lambda r: (-r.longest_active_streak, r.franchise_id),
        lambda r: r.longest_active_streak,
        "Consecutive Playoff Seasons",
    )
    _leaderboard(
        "Longest Playoff-Drought Streak",
        lambda r: (-r.longest_drought_streak, r.franchise_id),
        lambda r: r.longest_drought_streak,
        "Consecutive Seasons Out",
    )

    lines.append(RANK_DERIVATION_NOTE)
    lines.append("")

    return "\n".join(lines)


# ── Rendering: Bridesmaids ───────────────────────────────────────────


def render_bridesmaids_markdown(
    bridesmaids: Sequence[BridesmaidRecord],
    name_map: dict[str, str],
) -> str:
    """Render the Bridesmaids sub-shape per spec §3.1 / §3.7.

    Produces a markdown page with:
    - H1 title and scope-declaration line.
    - The cross-era championship-runner-up leaderboard: Rank,
      Franchise, Runner-Up Finishes, Seasons, Titles. The Titles column
      surfaces the perennial-bridesmaid archetype — a franchise with
      runner-up finishes and zero titles (§3.7 / §4.5).

    v1 ships the runner-up leg only; the almost leg (D50) is dropped
    from v1 per §3.7 and is not rendered.

    Args:
        bridesmaids: Aggregation output from `compute_bridesmaids`.
            Expected sort: runner-up count descending, then fewer
            titles first.
        name_map: franchise_id → display name. Missing entries fall
            back to the raw franchise_id.

    Returns:
        Markdown string. Empty `bridesmaids` produces a "no data" page.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_BRIDESMAIDS}")
    lines.append("")
    lines.append(_scope_block())
    lines.append(
        "Franchises that reached the championship matchup and came up "
        "short — the close-but-no-cigar leaderboard, counted across "
        "the digital era."
    )
    lines.append("")

    if not bridesmaids:
        lines.append("*No runner-up data available.*")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        "| Rank | Franchise | Runner-Up Finishes | Seasons | Titles |"
    )
    lines.append("|---|---|---|---|---|")
    for rank, r in enumerate(bridesmaids, start=1):
        franchise = _resolve(name_map, r.franchise_id)
        seasons_str = ", ".join(str(s) for s in r.runner_up_seasons)
        lines.append(
            f"| {rank} | {franchise} | {r.runner_up_count} | "
            f"{seasons_str} | {r.championship_count} |"
        )
    lines.append("")
    lines.append(RANK_DERIVATION_NOTE)
    lines.append("")

    return "\n".join(lines)


# ── Rendering: Index page ────────────────────────────────────────────


def render_index_markdown() -> str:
    """Render the index page per spec §5.1 / §6.4 layout invariant.

    The index is the entry point. It declares the archive's scope and
    links to the three sub-shape pages. The index does not embed
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
    lines.append("This archive surfaces three views of the playoff era:")
    lines.append("")
    lines.append(
        f"- [{TITLE_PLAYOFF_BRACKETS}](./playoff_brackets.md) — "
        "the full playoff bracket for every digital-era season: "
        "preliminary, semifinal, and championship rounds."
    )
    lines.append(
        f"- [{TITLE_PLAYOFF_RECORDS}](./playoff_records.md) — "
        "all-time cross-season leaderboards: playoff-season "
        "appearances, championship-matchup appearances, and the "
        "longest active and drought streaks."
    )
    lines.append(
        f"- [{TITLE_BRIDESMAIDS}](./bridesmaids.md) — "
        "the cross-era championship-runner-up leaderboard."
    )
    lines.append("")
    lines.append(
        "Content is regenerated from canonical league events once per "
        "year, at the end of the NFL season, at the commissioner's "
        "election; the regeneration is operationally deterministic, "
        "and the git history is the archive's version history."
    )
    lines.append("")

    return "\n".join(lines)
