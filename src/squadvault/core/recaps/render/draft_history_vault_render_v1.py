"""Draft History Vault Render v1 - A2 surface's markdown rendering.

Pure rendering functions for A2's archive presentation per A2
specification (`_observations/OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md`)
sections 3.1 / 3.6 / 3.7 / 3.8 / 5.1 / 6.4 / 6.8.

Each render function takes the output of a
`draft_history_vault_aggregations_v1` derivation function plus
franchise/player name maps and returns a markdown string. No I/O;
no file writes. The companion script
`scripts/generate_draft_history_vault_archive.py` wires loading,
name resolution, aggregation, rendering, and file writing into an
operational unit.

Contract (per A2 spec sections 3.6, 6.2, 6.8):

- Every rendered markdown file declares its scope at the top via
  `SCOPE_DECLARATION_LINE`. Per section 6.2 surface-specific
  invariant: A2's surface displays the scope-declaration line per
  section 3.6.
- The auction era's substrate window is 2018-2025 with the 2021
  gap acknowledged honestly per section 3.6. The 2021 gap framing
  is "not represented" per section 2.3 silence-over-speculation;
  cause is uncharacterized at v1 per section 8.6.
- Per section 6.8 narrative-claim drift principle: rank ordering
  computes at render time. NO frozen ordinal claims like
  "the third-highest bid in league history" are baked into the
  markdown at write time. The rendered ordinals (rank 1, rank 2,
  rank 3) are computed from the aggregation's current sort order
  at each archive regeneration; if the substrate changes, the
  ranks change.
- Per section 3.8: the most-expensive view exposes the overall
  record AND the per-position records (top-1 per position at v1;
  spec admits top-3 per position as a revision-point expansion).

Governance:

- Pure functions. Deterministic. No I/O. No side effects.
- No commissioner-curated labels per section 6.1 D3-Alpha invariant:
  every rendered value traces to an aggregation output's field,
  which in turn traces to a canonical event per the aggregation
  module's contract.
- Markdown structure is the layout-invariant contract that
  `Tests/test_draft_history_vault_archive_layout_v1.py` enforces
  when the archive exists.
"""

from __future__ import annotations

from collections.abc import Sequence

from squadvault.core.recaps.context.draft_history_vault_aggregations_v1 import (
    BargainEntry,
    BustEntry,
    MostExpensiveResult,
)

# -- Module-level constants ------------------------------------------

#: Scope-declaration line displayed at the top of every A2 archive
#: page. Per A2 spec section 3.6: A2 must declare its auction-era
#: scope honestly, acknowledging the 2021 gap. Per section 8.6 the
#: 2021 gap cause is uncharacterized; the framing is "not
#: represented" per section 2.3 silence-over-speculation.
SCOPE_DECLARATION_LINE = (
    "The Draft History Vault: PFL Buddies auction era, 2018 - 2025. "
    "The 2021 auction is not represented in the digital substrate. "
    "Leaderboards cover seven seasons: 2018, 2019, 2020, 2022, 2023, "
    "2024, 2025."
)

#: Rank-derivation note appended to leaderboard pages. Per A2 spec
#: section 6.8 narrative-claim drift principle: substrate-derived
#: ranks compute at render time. The note acknowledges this to the
#: reader; the absence of frozen ordinal claims in the markdown
#: itself is the structural guarantee.
RANK_DERIVATION_NOTE = (
    "*Ranks are computed from the current substrate at archive "
    "regeneration. If the substrate changes, the ranks change.*"
)

#: H1 titles, used by render functions and tested for presence in
#: the rendered markdown.
TITLE_INDEX = "PFL Buddies - Draft History Vault"
TITLE_MOST_EXPENSIVE = "Auction-Most-Expensive History"
TITLE_BUST_HALL = "Auction-Bust Hall"
TITLE_BARGAIN_HALL = "Auction-Bargain Hall"


# -- Helpers ---------------------------------------------------------


def _resolve_franchise(name_map: dict[str, str], franchise_id: str) -> str:
    """Resolve a franchise_id to its display name.

    Falls back to the franchise_id itself if the resolver lacks an
    entry - per the existing pattern in
    `league_history_v1.resolve_franchise_name_any_season`. This is
    conservative: A2 displays what the substrate provides; missing
    names stay missing.
    """
    return name_map.get(franchise_id, franchise_id)


def _resolve_player(name_map: dict[str, str], player_id: str) -> str:
    """Resolve a player_id to its display name.

    Falls back to the player_id itself if not found, matching the
    franchise-resolution pattern.
    """
    return name_map.get(player_id, player_id)


def _scope_block() -> str:
    """Standard scope-declaration block prefixed to every page."""
    return f"{SCOPE_DECLARATION_LINE}\n"


# -- Rendering: Auction-Most-Expensive History -----------------------


def render_most_expensive_markdown(
    result: MostExpensiveResult,
    franchise_names: dict[str, str],
    player_names: dict[str, str],
) -> str:
    """Render the Auction-Most-Expensive History sub-shape.

    Per A2 spec section 3.1 / section 3.8 / section 5.1. Produces a
    markdown page with:
    - H1 title and scope-declaration line.
    - Overall record: the single all-time most-expensive auction
      pick across positions.
    - Per-position records: the all-time most-expensive pick per
      position present in the substrate, top-1 per position
      (section 3.8 v1 default).

    Per section 6.8: no frozen ordinal claims like "the third-highest
    bid in league history" are written. The rendered values are
    the substrate-derived records at the moment of rendering; a
    future archive regeneration may surface different records.

    Args:
        result: Aggregation output from
            `compute_auction_most_expensive_v1`.
        franchise_names: franchise_id to display name. Missing
            entries fall back to the raw franchise_id.
        player_names: player_id to display name. Missing entries
            fall back to the raw player_id.

    Returns:
        Markdown string. If `result.overall` is None, produces a
        "no data" page; the scope-declaration and title still
        render.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_MOST_EXPENSIVE}")
    lines.append("")
    lines.append(_scope_block())

    if result.overall is None:
        lines.append("*No auction-pick data available.*")
        lines.append("")
        return "\n".join(lines)

    # Overall record section.
    overall = result.overall
    lines.append("## Overall Record")
    lines.append("")
    lines.append(
        "The all-time most-expensive single pick across the auction era:"
    )
    lines.append("")
    franchise = _resolve_franchise(franchise_names, overall.franchise_id)
    player = _resolve_player(player_names, overall.player_id)
    position_str = (
        f" ({overall.position})" if overall.position else ""
    )
    lines.append(
        f"- **{franchise}** spent **${overall.bid_amount:.0f}** on "
        f"**{player}**{position_str} in **{overall.season}**."
    )
    lines.append("")

    # Per-position records.
    if result.per_position:
        lines.append("## Per-Position Records")
        lines.append("")
        lines.append(
            "The most-expensive pick at each position present in the "
            "substrate:"
        )
        lines.append("")
        lines.append(
            "| Position | Franchise | Player | Bid | Season |"
        )
        lines.append("|---|---|---|---|---|")
        for r in result.per_position:
            f_name = _resolve_franchise(franchise_names, r.franchise_id)
            p_name = _resolve_player(player_names, r.player_id)
            lines.append(
                f"| {r.position} | {f_name} | {p_name} | "
                f"${r.bid_amount:.0f} | {r.season} |"
            )
        lines.append("")

    lines.append(RANK_DERIVATION_NOTE)
    lines.append("")

    return "\n".join(lines)


# -- Rendering: Auction-Bust Hall ------------------------------------


def render_bust_hall_markdown(
    entries: Sequence[BustEntry],
    franchise_names: dict[str, str],
    player_names: dict[str, str],
) -> str:
    """Render the Auction-Bust Hall sub-shape.

    Per A2 spec section 3.1 / section 5.1. Produces a markdown page
    with:
    - H1 title and scope-declaration line.
    - Leaderboard of cross-era busts ranked by severity signal.

    Per section 6.8: no frozen ordinal claims. The rendered ranks
    are derived at call time from the entries' sort order.

    Args:
        entries: Aggregation output from `compute_auction_bust_hall_v1`,
            expected pre-sorted by severity descending.
        franchise_names: franchise_id to display name. Missing
            entries fall back to the raw franchise_id.
        player_names: player_id to display name. Missing entries
            fall back to the raw player_id.

    Returns:
        Markdown string. Empty `entries` produces a "no data" page.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_BUST_HALL}")
    lines.append("")
    lines.append(_scope_block())

    if not entries:
        lines.append("*No bust entries meet the inclusion thresholds.*")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        "Picks ranked by the combined severity signal "
        "`(league_starter_avg - player_avg) * bid_amount`. Inclusion "
        "requires at least 4 starter weeks and a player-average below "
        "half the season league starter average."
    )
    lines.append("")
    lines.append(
        "| Rank | Season | Franchise | Player | Bid | "
        "Player Avg | League Avg | Starts | Severity |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for rank, e in enumerate(entries, start=1):
        franchise = _resolve_franchise(franchise_names, e.franchise_id)
        player = _resolve_player(player_names, e.player_id)
        lines.append(
            f"| {rank} | {e.season} | {franchise} | {player} | "
            f"${e.bid_amount:.0f} | {e.player_avg:.2f} | "
            f"{e.league_starter_avg:.2f} | {e.starter_weeks} | "
            f"{e.severity_signal:.1f} |"
        )
    lines.append("")
    lines.append(RANK_DERIVATION_NOTE)
    lines.append("")

    return "\n".join(lines)


# -- Rendering: Auction-Bargain Hall ---------------------------------


def render_bargain_hall_markdown(
    entries: Sequence[BargainEntry],
    franchise_names: dict[str, str],
    player_names: dict[str, str],
) -> str:
    """Render the Auction-Bargain Hall sub-shape.

    Per A2 spec section 3.1 / section 5.1. Produces a markdown page
    with:
    - H1 title and scope-declaration line.
    - Leaderboard of cross-era bargains ranked by dollars-per-point
      ascending.

    Per section 6.8: no frozen ordinal claims. The rendered ranks
    are derived at call time from the entries' sort order.

    Args:
        entries: Aggregation output from
            `compute_auction_bargain_hall_v1`, expected pre-sorted
            by dollar_per_point ascending.
        franchise_names: franchise_id to display name. Missing
            entries fall back to the raw franchise_id.
        player_names: player_id to display name. Missing entries
            fall back to the raw player_id.

    Returns:
        Markdown string. Empty `entries` produces a "no data" page.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_BARGAIN_HALL}")
    lines.append("")
    lines.append(_scope_block())

    if not entries:
        lines.append("*No bargain entries meet the inclusion thresholds.*")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        "Picks ranked by dollars-per-point ascending (lower is a "
        "better bargain). Inclusion requires a minimum production "
        "threshold of 50 total points to filter out near-zero-point "
        "picks whose ratios would otherwise rank artificially "
        "favorably."
    )
    lines.append("")
    lines.append(
        "| Rank | Season | Franchise | Player | Bid | "
        "Total Points | Per Point |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for rank, e in enumerate(entries, start=1):
        franchise = _resolve_franchise(franchise_names, e.franchise_id)
        player = _resolve_player(player_names, e.player_id)
        lines.append(
            f"| {rank} | {e.season} | {franchise} | {player} | "
            f"${e.bid_amount:.0f} | {e.total_points:.1f} | "
            f"${e.dollar_per_point:.3f} |"
        )
    lines.append("")
    lines.append(RANK_DERIVATION_NOTE)
    lines.append("")

    return "\n".join(lines)


# -- Rendering: Index page -------------------------------------------


def render_index_markdown() -> str:
    """Render the index page per A2 spec section 5.1 / section 6.4
    layout invariant.

    The index is the entry point. It declares the archive's scope
    and links to the three sub-shape pages. The index does not
    embed aggregation content - that lives on the per-sub-shape
    pages.

    Per section 6.4 layout invariant: `index.md` is the entry point
    and contains the scope-declaration header.

    Returns:
        Markdown string. Always non-empty; does not depend on
        substrate data.
    """
    lines: list[str] = []
    lines.append(f"# {TITLE_INDEX}")
    lines.append("")
    lines.append(_scope_block())
    lines.append("This archive surfaces three views of the auction era:")
    lines.append("")
    lines.append(
        f"- [{TITLE_MOST_EXPENSIVE}](./most_expensive.md) - "
        "the all-time most-expensive auction pick across positions, "
        "plus per-position records."
    )
    lines.append(
        f"- [{TITLE_BUST_HALL}](./bust_hall.md) - "
        "the league's worst-performing auction picks across the "
        "auction era, ranked by severity."
    )
    lines.append(
        f"- [{TITLE_BARGAIN_HALL}](./bargain_hall.md) - "
        "the league's best-value auction picks across the auction "
        "era, ranked by dollars-per-point."
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
