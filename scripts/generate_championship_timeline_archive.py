#!/usr/bin/env python3
"""Generate (or regenerate) A3's Championship Timeline archive.

This script wires the aggregation + render layers (per A3 spec
`_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_SPECIFICATION.md`
§§3.1 / 5.1 / 5.4) into one operational unit:

  load_all_matchups (substrate)
    → compute_playoff_bracket / compute_cross_season_playoff_records /
      compute_championship_roll → compute_bridesmaids (aggregation)
    → render_*_markdown (presentation)
    → archive/championship_timeline/*.md (operational truth)

`compute_championship_roll` (A1's primitive) is computed once and
threaded into `compute_bridesmaids`; A3 does not re-derive
championships per the §3.1 absorption boundary.

Per spec §5.4 the *commit* of the regenerated archive is the
commissioner's approval event; this script does not require a
paste-confirm prompt (unlike `scripts/distribute_recap.py`'s
group-text-channel distribution which is league-facing). The
commissioner reviews the regenerated files via `git diff` before
`git commit`.

Not a real-time bracket tracker (spec §6.7). This script regenerates
all three sub-shapes from the *completed* playoff substrate, once per
year at the end of the NFL season. There is deliberately no
incremental in-season mode — no per-playoff-round regeneration. The
active-bracket-following experience is the weekly recap's territory
(E1), not A3's; A3's once-per-year retrospective update is the
anti-engagement-loop posture.

Default invocation:
  ./scripts/py scripts/generate_championship_timeline_archive.py

This script imports from `squadvault.core` and must be run through the
`./scripts/py` shim, which sets `PYTHONPATH=src` (and is CWD-independent).
Running the file directly
(`./scripts/generate_championship_timeline_archive.py`) fails with
`ModuleNotFoundError` because the script does no `sys.path`
manipulation of its own.

Default settings target PFL Buddies (league_id = 70985) against
`.local_squadvault.sqlite`. The §6.4 layout invariants remain enforced
regardless of `--archive-root`.

Exit codes
----------
0   success (or successful dry run)
2   database file does not exist or contains no matchups for the league
130 commissioner aborted via Ctrl-C (POSIX SIGINT convention)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

from squadvault.core.recaps.context.championship_timeline_aggregations_v1 import (
    compute_bridesmaids,
    compute_cross_season_playoff_records,
    compute_playoff_bracket,
)
from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    compute_championship_roll,
)
from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
    load_all_matchups,
)
from squadvault.core.recaps.render.championship_timeline_render_v1 import (
    render_bridesmaids_markdown,
    render_index_markdown,
    render_playoff_brackets_markdown,
    render_playoff_records_markdown,
)

DEFAULT_LEAGUE_ID: Final[str] = "70985"
DEFAULT_DB_PATH: Final[str] = ".local_squadvault.sqlite"
DEFAULT_ARCHIVE_ROOT: Final[str] = "archive/championship_timeline"
DEFAULT_TOP_N: Final[int] = 10

INDEX_FILENAME: Final[str] = "index.md"
PLAYOFF_BRACKETS_FILENAME: Final[str] = "playoff_brackets.md"
PLAYOFF_RECORDS_FILENAME: Final[str] = "playoff_records.md"
BRIDESMAIDS_FILENAME: Final[str] = "bridesmaids.md"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate the A3 Championship Timeline archive.",
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
            "Number of rows to render per cross-season-records "
            f"leaderboard (default: {DEFAULT_TOP_N})."
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

    brackets = compute_playoff_bracket(matchups)
    records = compute_cross_season_playoff_records(matchups)
    # A1's primitive, computed once and threaded into Bridesmaids per
    # the spec §3.1 absorption boundary (A3 does not re-derive
    # championships).
    championship_roll = compute_championship_roll(matchups)
    bridesmaids = compute_bridesmaids(championship_roll)

    return {
        INDEX_FILENAME: render_index_markdown(),
        PLAYOFF_BRACKETS_FILENAME: render_playoff_brackets_markdown(
            brackets, name_map,
        ),
        PLAYOFF_RECORDS_FILENAME: render_playoff_records_markdown(
            records, name_map, top_n=top_n,
        ),
        BRIDESMAIDS_FILENAME: render_bridesmaids_markdown(
            bridesmaids, name_map,
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
