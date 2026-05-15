"""Tests for the Weekly Recap Archive layout (E2-light, operational).

These tests are vacuous when no E2-light archive has been generated. As the
archive fills (after the founder runs
`scripts/generate_weekly_recap_archive.py` and commits the output), they
enforce per E2-light spec section 6 layout invariants:

- Top-level archive/recaps/index.html exists.
- Each season subdirectory contains index.html.
- Every index.html is valid HTML (starts with <!DOCTYPE html>).
- Season index pages reference the league name.
- Season index pages contain at least one Week entry.
- Top-level index links to each season's page.

The APPROVED-only invariant is enforced at generation time by the script's
SQL query (state = 'APPROVED') and is not verifiable from filesystem state.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_RECAPS = REPO_ROOT / "archive" / "recaps"
LEAGUE_NAME = "PFL Buddies"
_DOCTYPE = "<!DOCTYPE html>"


def _season_index_files() -> list[Path]:
    if not ARCHIVE_RECAPS.exists():
        return []
    return sorted(ARCHIVE_RECAPS.glob("*/index.html"))


def _top_level_index() -> Path:
    return ARCHIVE_RECAPS / "index.html"


def test_weekly_recap_archive_top_level_index_exists() -> None:
    """Top-level index.html exists when the archive has been generated."""
    if not _season_index_files():
        return  # vacuous: archive not yet generated
    assert _top_level_index().exists(), (
        "archive/recaps/index.html missing. "
        "Run ./scripts/py scripts/generate_weekly_recap_archive.py to regenerate."
    )


def test_weekly_recap_archive_all_html_files_are_valid_html() -> None:
    """Every index.html starts with <!DOCTYPE html>."""
    files = _season_index_files()
    if not files:
        return  # vacuous
    top = _top_level_index()
    all_files = ([top] if top.exists() else []) + files
    for path in all_files:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(_DOCTYPE), (
            f"{path.relative_to(REPO_ROOT)} does not start with {_DOCTYPE!r}. "
            f"Got: {text[:80]!r}"
        )


def test_weekly_recap_archive_season_pages_contain_league_name() -> None:
    """Season index pages contain the league name."""
    for path in _season_index_files():
        text = path.read_text(encoding="utf-8")
        assert LEAGUE_NAME in text, (
            f"{path.relative_to(REPO_ROOT)} does not contain "
            f"league name {LEAGUE_NAME!r}."
        )


def test_weekly_recap_archive_season_pages_contain_week_entries() -> None:
    """Each season index page contains at least one Week entry."""
    for path in _season_index_files():
        text = path.read_text(encoding="utf-8")
        assert "Week " in text, (
            f"{path.relative_to(REPO_ROOT)} contains no 'Week ' entries. "
            f"The season archive appears empty or malformed."
        )


def test_weekly_recap_archive_top_level_links_to_all_seasons() -> None:
    """Top-level index.html links to each season's archive page."""
    season_indexes = _season_index_files()
    if not season_indexes:
        return  # vacuous
    top = _top_level_index()
    if not top.exists():
        return  # covered by the exists test
    text = top.read_text(encoding="utf-8")
    for season_index in season_indexes:
        season = season_index.parent.name
        assert f"{season}/index.html" in text, (
            f"Top-level index does not link to season {season}. "
            f"Run ./scripts/py scripts/generate_weekly_recap_archive.py to regenerate."
        )
