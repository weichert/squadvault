#!/usr/bin/env python3
"""Generate (or regenerate) A1's Hall of Fame & Shame archive.

This script wires the aggregation + render layers (per A1 spec
`_observations/OBSERVATIONS_2026_05_11_PHASE_11_A1_SPECIFICATION.md`
§§4.3 / 5.1 / 5.4) into one operational unit:

  load_all_matchups (substrate)
    → compute_championship_roll / compute_all_season_records /
      compute_blowouts_hall (aggregation)
    → render_*_markdown (presentation)
    → archive/hall_of_fame_and_shame/*.md (operational truth)

Per spec §5.4 the *commit* of the regenerated archive is the
commissioner's approval event; this script does not require a
paste-confirm prompt (unlike `scripts/distribute_recap.py`'s
group-text-channel distribution which is league-facing). The
commissioner reviews the regenerated files via `git diff` before
`git commit`.

Default invocation:
  ./scripts/py scripts/generate_hall_of_fame_archive.py

This script imports from `squadvault.core` and must be run through the
`./scripts/py` shim, which sets `PYTHONPATH=src` (and is CWD-independent).
Running the file directly (`./scripts/generate_hall_of_fame_archive.py`)
fails with `ModuleNotFoundError` because the script does no `sys.path`
manipulation of its own.

Default settings target PFL Buddies (league_id = 70985) against
`.local_squadvault.sqlite`. Override per spec §6.4 layout invariants
remain enforced regardless of `--archive-root`.

Exit codes
----------
0   success (or successful dry run)
2   database file does not exist or contains no matchups for the league
3   aggregation returned empty results (no data to render)
130 commissioner aborted via Ctrl-C (POSIX SIGINT convention)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    compute_all_season_records,
    compute_blowouts_hall,
    compute_championship_roll,
)
from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
    build_season_scoped_name_map,
    load_all_matchups,
)
from squadvault.core.recaps.render.hall_of_fame_render_v1 import (
    render_blowouts_hall_markdown,
    render_championship_roll_markdown,
    render_index_markdown,
    render_worst_seasons_markdown,
)

DEFAULT_LEAGUE_ID: Final[str] = "70985"
DEFAULT_DB_PATH: Final[str] = ".local_squadvault.sqlite"
DEFAULT_ARCHIVE_ROOT: Final[str] = "archive/hall_of_fame_and_shame"
DEFAULT_TOP_N: Final[int] = 10

INDEX_FILENAME: Final[str] = "index.md"
CHAMPIONSHIP_ROLL_FILENAME: Final[str] = "championship_roll.md"
WORST_SEASONS_FILENAME: Final[str] = "worst_seasons.md"
BLOWOUTS_HALL_FILENAME: Final[str] = "blowouts_hall.md"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate the A1 Hall of Fame & Shame archive.",
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
            "Number of rows to render for worst-seasons and blowouts-hall "
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
    """Load, aggregate, and render. Returns filename → markdown content."""
    matchups = load_all_matchups(db_path=db_path, league_id=league_id)
    if not matchups:
        return {}

    name_map = build_cross_season_name_resolver(
        db_path=db_path, league_id=league_id,
    )
    season_map = build_season_scoped_name_map(
        db_path=db_path, league_id=league_id,
    )

    champ_roll = compute_championship_roll(matchups)
    season_records = compute_all_season_records(matchups)
    blowouts = compute_blowouts_hall(matchups, top_n=top_n)

    return {
        INDEX_FILENAME: render_index_markdown(),
        CHAMPIONSHIP_ROLL_FILENAME: render_championship_roll_markdown(
            champ_roll, season_map,
        ),
        WORST_SEASONS_FILENAME: render_worst_seasons_markdown(
            season_records, name_map, top_n=top_n,
        ),
        BLOWOUTS_HALL_FILENAME: render_blowouts_hall_markdown(
            blowouts, name_map,
        ),
    }


def _write_archive(archive_root: Path, pages: dict[str, str]) -> None:
    """Write pages to disk under archive_root. Creates the dir if absent."""
    archive_root.mkdir(parents=True, exist_ok=True)
    for filename, content in pages.items():
        target = archive_root / filename
        target.write_text(content, encoding="utf-8")


def _print_summary(pages: dict[str, str], *, dry_run: bool, archive_root: Path) -> None:
    """Print a human-readable summary of what was generated."""
    label = "DRY RUN — would write" if dry_run else "Wrote"
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
            f"ERROR: no matchups found for league {args.league_id} "
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
