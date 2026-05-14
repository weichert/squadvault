#!/usr/bin/env python3
"""Generate (or regenerate) A2's Draft History Vault archive.

This script wires the aggregation + render layers (per A2 spec
`_observations/OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md`
sections 4.3 / 5.1 / 5.2) into one operational unit:

  load_all_auction_picks + load_player_season_scoring (substrate)
    -> compute_auction_most_expensive_v1 / compute_auction_bust_hall_v1 /
       compute_auction_bargain_hall_v1 (aggregation)
    -> render_*_markdown (presentation)
    -> archive/draft_history_vault/*.md (operational truth)

Per A2 spec section 5.2 two-phase update rhythm:
- Auction-night triggers most-expensive regeneration (late August).
- End-of-NFL-season triggers bust and bargain regeneration (February).
This script regenerates all four pages at every invocation; the
commissioner runs it at the appropriate substrate-event moments.

Per spec section 5.4 the *commit* of the regenerated archive is the
commissioner's approval event; this script does not require a
paste-confirm prompt. The commissioner reviews the regenerated
files via `git diff` before `git commit`.

Default invocation:
  ./scripts/py scripts/generate_draft_history_vault_archive.py

This script imports from `squadvault.core` and must be run through the
`./scripts/py` shim, which sets `PYTHONPATH=src` (and is CWD-independent).
Running the file directly (`./scripts/generate_draft_history_vault_archive.py`)
fails with `ModuleNotFoundError` because the script does no `sys.path`
manipulation of its own.

Default settings target PFL Buddies (league_id = 70985) against
`.local_squadvault.sqlite`. Override per spec section 6.4 layout
invariants remain enforced regardless of `--archive-root`.

Exit codes
----------
0   success (or successful dry run)
2   database file does not exist or contains no auction picks
3   aggregation returned empty results (no data to render)
130 commissioner aborted via Ctrl-C (POSIX SIGINT convention)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    load_all_auction_picks,
    load_player_season_scoring,
)
from squadvault.core.recaps.context.draft_history_vault_aggregations_v1 import (
    compute_auction_bargain_hall_v1,
    compute_auction_bust_hall_v1,
    compute_auction_most_expensive_v1,
)
from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
)
from squadvault.core.recaps.render.draft_history_vault_render_v1 import (
    render_bargain_hall_markdown,
    render_bust_hall_markdown,
    render_index_markdown,
    render_most_expensive_markdown,
)
from squadvault.core.resolvers import build_player_name_map

DEFAULT_LEAGUE_ID: Final[str] = "70985"
DEFAULT_DB_PATH: Final[str] = ".local_squadvault.sqlite"
DEFAULT_ARCHIVE_ROOT: Final[str] = "archive/draft_history_vault"
DEFAULT_TOP_N: Final[int] = 20

INDEX_FILENAME: Final[str] = "index.md"
MOST_EXPENSIVE_FILENAME: Final[str] = "most_expensive.md"
BUST_HALL_FILENAME: Final[str] = "bust_hall.md"
BARGAIN_HALL_FILENAME: Final[str] = "bargain_hall.md"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate the A2 Draft History Vault archive.",
    )
    p.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"SQLite database path (default: {DEFAULT_DB_PATH}).",
    )
    p.add_argument(
        "--league-id",
        default=DEFAULT_LEAGUE_ID,
        help=f"League ID to render (default: {DEFAULT_LEAGUE_ID}).",
    )
    p.add_argument(
        "--archive-root",
        default=DEFAULT_ARCHIVE_ROOT,
        help=(
            "Archive output directory relative to repo root "
            f"(default: {DEFAULT_ARCHIVE_ROOT})."
        ),
    )
    p.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help=(
            "Number of rows to render for bust-hall and bargain-hall "
            f"(default: {DEFAULT_TOP_N})."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Render the four pages and print a summary; do not write "
            "files. Useful for first-time inspection."
        ),
    )
    return p


def _render_all_pages(
    *, db_path: str, league_id: str, top_n: int,
) -> dict[str, str]:
    """Load, aggregate, and render. Returns filename to markdown content."""
    picks = load_all_auction_picks(db_path, league_id)
    if not picks:
        return {}

    # current_season=0 means no per-week filtering - load all-season
    # totals for cross-era aggregation per the loader's contract.
    scoring = load_player_season_scoring(
        db_path, league_id, current_season=0, target_week=99,
    )

    franchise_names = build_cross_season_name_resolver(
        db_path=db_path, league_id=league_id,
    )
    player_names = build_player_name_map(db_path, league_id)

    most_expensive = compute_auction_most_expensive_v1(picks)
    bust_entries = compute_auction_bust_hall_v1(picks, scoring, top_n=top_n)
    bargain_entries = compute_auction_bargain_hall_v1(
        picks, scoring, top_n=top_n,
    )

    return {
        INDEX_FILENAME: render_index_markdown(),
        MOST_EXPENSIVE_FILENAME: render_most_expensive_markdown(
            most_expensive, franchise_names, player_names,
        ),
        BUST_HALL_FILENAME: render_bust_hall_markdown(
            bust_entries, franchise_names, player_names,
        ),
        BARGAIN_HALL_FILENAME: render_bargain_hall_markdown(
            bargain_entries, franchise_names, player_names,
        ),
    }


def _write_archive(archive_root: Path, pages: dict[str, str]) -> None:
    """Write pages to disk under archive_root. Creates the dir if absent."""
    archive_root.mkdir(parents=True, exist_ok=True)
    for filename, content in pages.items():
        target = archive_root / filename
        target.write_text(content, encoding="utf-8")


def _print_summary(
    pages: dict[str, str], *, dry_run: bool, archive_root: Path,
) -> None:
    """Print a human-readable summary of what was generated."""
    label = "DRY RUN - would write" if dry_run else "Wrote"
    print(f"{label} {len(pages)} files to {archive_root}:")
    for filename, content in pages.items():
        line_count = content.count("\n") + 1
        char_count = len(content)
        print(f"  {filename}: {line_count} lines, {char_count} chars")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(
            f"ERROR: database file does not exist: {db_path}",
            file=sys.stderr,
        )
        return 2

    try:
        pages = _render_all_pages(
            db_path=str(db_path),
            league_id=args.league_id,
            top_n=args.top_n,
        )
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130

    if not pages:
        print(
            f"ERROR: no auction picks found for league {args.league_id} "
            f"in {db_path}",
            file=sys.stderr,
        )
        return 2

    archive_root = Path(args.archive_root)
    if not args.dry_run:
        _write_archive(archive_root, pages)

    _print_summary(pages, dry_run=args.dry_run, archive_root=archive_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
