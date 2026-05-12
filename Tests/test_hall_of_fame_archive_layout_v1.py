"""Tests for the Hall of Fame & Shame archive layout (A1, operational).

These tests are vacuous when no A1 archive entries exist. As the archive
fills (after the founder runs `scripts/generate_hall_of_fame_archive.py`
and commits the output), they enforce per A1 spec §6.4 layout invariants:

- Layout root: ``archive/hall_of_fame_and_shame/`` contains exactly four
  expected markdown files (``index.md`` plus the three sub-shape files).
- Scope-declaration invariant per spec §6.2 / §3.6: every page contains
  the canonical scope-declaration line.
- H1 invariant: every page starts with an H1 title line.

The append-only invariant is enforced at the git level (regenerations
overwrite content; prior versions are preserved in git history per
spec §5.4 / §6.5) and is not verifiable from filesystem state alone.

The test surface is intentionally small. It catches structural drift,
not content drift; content quality is governed by the render-layer
unit tests (`test_hall_of_fame_render_v1.py`).
"""
from __future__ import annotations

from pathlib import Path

from squadvault.core.recaps.render.hall_of_fame_render_v1 import (
    SCOPE_DECLARATION_LINE,
    TITLE_BLOWOUTS_HALL,
    TITLE_CHAMPIONSHIP_ROLL,
    TITLE_INDEX,
    TITLE_WORST_SEASONS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "archive" / "hall_of_fame_and_shame"

_EXPECTED_FILES = {
    "index.md": TITLE_INDEX,
    "championship_roll.md": TITLE_CHAMPIONSHIP_ROLL,
    "worst_seasons.md": TITLE_WORST_SEASONS,
    "blowouts_hall.md": TITLE_BLOWOUTS_HALL,
}


def _archive_md_files() -> list[Path]:
    if not ARCHIVE_ROOT.exists():
        return []
    return sorted(ARCHIVE_ROOT.glob("*.md"))


def test_archive_contains_only_expected_files() -> None:
    """If the archive exists, it contains only the four expected files."""
    md_files = _archive_md_files()
    if not md_files:
        return  # vacuous
    actual = {p.name for p in md_files}
    expected = set(_EXPECTED_FILES.keys())
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    assert not unexpected, (
        f"Unexpected files in A1 archive: {unexpected}. "
        f"The archive should contain exactly: {sorted(expected)}."
    )
    assert not missing, (
        f"Missing files in A1 archive: {missing}. "
        f"The archive should contain exactly: {sorted(expected)}."
    )


def test_each_page_starts_with_h1_title() -> None:
    """Every page begins with the contracted H1 title."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        expected_title = _EXPECTED_FILES.get(path.name)
        assert expected_title is not None, (
            f"Unexpected file in A1 archive: {path.name}"
        )
        assert text.startswith(f"# {expected_title}"), (
            f"{path.name} does not start with '# {expected_title}'. "
            f"Got: {text[:80]!r}"
        )


def test_each_page_contains_scope_declaration() -> None:
    """Every page declares the archive's scope per spec §6.2 / §3.6."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        assert SCOPE_DECLARATION_LINE in text, (
            f"{path.name} is missing the scope-declaration line. "
            f"Per spec §6.2 every A1 archive page must contain "
            f"SCOPE_DECLARATION_LINE."
        )


def test_each_page_is_non_empty() -> None:
    """Every page has substantive content beyond the header."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        # Expect at minimum: H1 + blank + scope line + at least one more line.
        non_empty_lines = [line for line in text.splitlines() if line.strip()]
        assert len(non_empty_lines) >= 3, (
            f"{path.name} appears empty or near-empty "
            f"({len(non_empty_lines)} non-empty lines). "
            f"Every page should render at minimum a title, scope, and "
            f"either content or a 'no data available' notice."
        )
