#!/usr/bin/env python3
"""Generate (or regenerate) E2-light's Weekly Recap Archive.

Reads all APPROVED WEEKLY_RECAP artifacts from recap_artifacts and produces:

  archive/recaps/{season}/index.html  -- per-season browseable recap archive
  archive/recaps/index.html           -- top-level season index

Per spec section 5:
  _observations/OBSERVATIONS_2026_05_14_PHASE_11_E2_LIGHT_SPECIFICATION.md

Read-only against the database. Idempotent: re-running overwrites index.html
files only; existing per-week Track A files are never touched.

Default invocation:
  ./scripts/py scripts/generate_weekly_recap_archive.py

This script imports from squadvault.core and must be run through the
./scripts/py shim, which sets PYTHONPATH=src.

Exit codes
----------
0   success (or successful dry run)
2   database file does not exist
3   no APPROVED WEEKLY_RECAP artifacts found
130 aborted via Ctrl-C
"""

from __future__ import annotations

import argparse
import html as html_mod
import sys
from collections import defaultdict
from pathlib import Path
from typing import Final

from squadvault.core.exports.season_html_export_v1 import (
    WeekRecapData,
    extract_shareable_parts,
    render_season_html,
)
from squadvault.core.storage.session import DatabaseSession

DEFAULT_DB_PATH: Final = ".local_squadvault.sqlite"
DEFAULT_LEAGUE_ID: Final = "70985"
DEFAULT_LEAGUE_NAME: Final = "PFL Buddies"
DEFAULT_ARCHIVE_ROOT: Final = "archive/recaps"


def _fetch_approved_recaps(db_path: str, league_id: str) -> list[dict]:
    """Fetch latest APPROVED WEEKLY_RECAP per (season, week_index)."""
    with DatabaseSession(db_path) as conn:
        rows = conn.execute(
            """
            SELECT season, week_index, version, state,
                   window_start, window_end,
                   approved_by, approved_at, rendered_text
            FROM recap_artifacts
            WHERE league_id = ?
              AND artifact_type = 'WEEKLY_RECAP'
              AND state = 'APPROVED'
            ORDER BY season ASC, week_index ASC, version DESC
            """,
            (league_id,),
        ).fetchall()
    # Deduplicate: keep only the latest version per (season, week_index).
    seen: set[tuple[int, int]] = set()
    result = []
    for row in rows:
        key = (row[0], row[1])
        if key not in seen:
            seen.add(key)
            result.append({
                "season": row[0],
                "week_index": row[1],
                "version": row[2],
                "state": row[3],
                "window_start": row[4],
                "window_end": row[5],
                "approved_by": row[6],
                "approved_at": row[7],
                "rendered_text": row[8] or "",
            })
    return result


def _fmt_date(iso: str | None) -> str:
    """Format ISO datetime to YYYY-MM-DD, or dash if absent."""
    return iso[:10] if iso else "\u2014"


def _build_week_data(row: dict) -> WeekRecapData:
    """Build WeekRecapData, injecting window/approval metadata as bullets."""
    narrative, bullets = extract_shareable_parts(row["rendered_text"])
    em = "\u2014"
    approved_by = row["approved_by"] or em
    meta = [
        f"Window: {_fmt_date(row['window_start'])} to {_fmt_date(row['window_end'])}",
        f"Approved by: {approved_by} on {_fmt_date(row['approved_at'])}",
    ]
    return WeekRecapData(
        week=row["week_index"],
        narrative=narrative,
        bullets=meta + bullets,
        version=row["version"],
        state=row["state"],
    )


def _render_top_level_index(summaries: list[dict], league_name: str) -> str:
    """Render archive/recaps/index.html listing all seasons."""
    esc = html_mod.escape
    items = "".join(
        f'<li><a href="{s["season"]}/index.html">{esc(str(s["season"]))} Season</a>'
        f' &mdash; {s["week_count"]} weeks'
        f'<span class="meta"> {esc(s["date_range"])}</span></li>\n'
        for s in summaries
    )
    css = (
        ":root{--bg:#fafaf9;--fg:#1c1917;--accent:#dc2626;--muted:#78716c;"
        "--border:#e7e5e4;}\n"
        "@media(prefers-color-scheme:dark){:root{--bg:#1c1917;--fg:#fafaf9;"
        "--accent:#f87171;--muted:#a8a29e;--border:#44403c;}}\n"
        "*{margin:0;padding:0;box-sizing:border-box;}\n"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;"
        "background:var(--bg);color:var(--fg);line-height:1.65;padding:2rem 1rem;"
        "max-width:680px;margin:0 auto;}\n"
        "header{text-align:center;margin-bottom:2rem;padding-bottom:1.5rem;"
        "border-bottom:2px solid var(--accent);}\n"
        "header h1{font-size:1.75rem;font-weight:700;letter-spacing:-0.02em;}\n"
        "header .subtitle{color:var(--muted);font-size:0.95rem;margin-top:0.25rem;}\n"
        "ul{list-style:none;margin-top:1rem;}\n"
        "li{padding:0.75rem 0;border-bottom:1px solid var(--border);}\n"
        "a{color:var(--accent);text-decoration:none;font-weight:600;}\n"
        "a:hover{text-decoration:underline;}\n"
        ".meta{color:var(--muted);font-size:0.9rem;}\n"
        "footer{text-align:center;margin-top:2rem;padding-top:1rem;"
        "border-top:1px solid var(--border);font-size:0.8rem;color:var(--muted);}\n"
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(league_name)} &mdash; Recap Archive</title>\n"
        f"<style>\n{css}</style>\n</head>\n<body>\n"
        f"<header>\n<h1>{esc(league_name)}</h1>\n"
        '<div class="subtitle">Weekly Recap Archive</div>\n</header>\n'
        f"<ul>\n{items}</ul>\n"
        "<footer>Generated by SquadVault &middot; "
        "Facts are canonical, narratives are derived</footer>\n"
        "</body>\n</html>\n"
    )


def _season_summary(season: int, rows: list[dict]) -> dict:
    starts = [r["window_start"] for r in rows if r["window_start"]]
    ends = [r["window_end"] for r in rows if r["window_end"]]
    start = _fmt_date(min(starts)) if starts else "\u2014"
    end = _fmt_date(max(ends)) if ends else "\u2014"
    return {
        "season": season,
        "week_count": len(rows),
        "date_range": f"{start} \u2013 {end}",
    }


def _render_all(rows: list[dict], league_name: str) -> dict[str, str]:
    by_season: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_season[row["season"]].append(row)

    pages: dict[str, str] = {}
    summaries = []
    for season in sorted(by_season):
        season_rows = by_season[season]
        week_data = [_build_week_data(r) for r in season_rows]
        pages[f"{season}/index.html"] = render_season_html(
            week_data, league_name=league_name, season=season,
        )
        summaries.append(_season_summary(season, season_rows))

    pages["index.html"] = _render_top_level_index(summaries, league_name)
    return pages


def _write_pages(archive_root: Path, pages: dict[str, str]) -> None:
    for rel_path, content in pages.items():
        target = archive_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _print_summary(
    pages: dict[str, str], *, dry_run: bool, archive_root: Path,
) -> None:
    label = "DRY RUN -- would write" if dry_run else "Wrote"
    print(f"{label} {len(pages)} files to {archive_root}:")
    for rel_path in sorted(pages):
        content = pages[rel_path]
        print(f"  {rel_path}: {content.count(chr(10)) + 1} lines, {len(content)} chars")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate E2-light Weekly Recap Archive.")
    p.add_argument("--db-path", default=DEFAULT_DB_PATH)
    p.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    p.add_argument("--league-name", default=DEFAULT_LEAGUE_NAME)
    p.add_argument("--archive-root", default=DEFAULT_ARCHIVE_ROOT)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        return 2
    try:
        rows = _fetch_approved_recaps(str(db_path), args.league_id)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130
    if not rows:
        print(
            f"ERROR: no APPROVED WEEKLY_RECAP artifacts found for "
            f"league {args.league_id} in {db_path}",
            file=sys.stderr,
        )
        return 3
    pages = _render_all(rows, league_name=args.league_name)
    archive_root = Path(args.archive_root)
    if not args.dry_run:
        _write_pages(archive_root, pages)
    _print_summary(pages, dry_run=args.dry_run, archive_root=archive_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
