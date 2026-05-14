"""Tests for the Championship Timeline archive layout (A3, operational).

These tests are vacuous when no A3 archive entries exist. As the
archive fills (after the founder runs
`scripts/generate_championship_timeline_archive.py` and commits the
output), they enforce per A3 spec section 6.4 layout invariants:

- Layout root: ``archive/championship_timeline/`` contains exactly
  four expected markdown files (``index.md`` plus the three sub-shape
  files).
- Scope-declaration invariant per spec section 6.2 / section 3.6:
  every page contains the canonical scope-declaration line.
- H1 invariant: every page starts with an H1 title line.
- Cross-link invariant per spec section 3.1 / section 6.4:
  ``playoff_brackets.md`` cross-links to A1's
  ``archive/hall_of_fame_and_shame/championship_roll.md`` rather than
  re-rendering A1's championship-week content.

The append-only invariant is enforced at the git level (regenerations
overwrite content; prior versions are preserved in git history per
spec section 5.4 / section 6.5) and is not verifiable from filesystem
state alone.

The test surface is intentionally small. It catches structural drift,
not content drift; content quality is governed by the render-layer
unit tests (`test_championship_timeline_render_v1.py`).
"""
from __future__ import annotations

from pathlib import Path

from squadvault.core.recaps.render.championship_timeline_render_v1 import (
    CHAMPIONSHIP_ROLL_CROSSLINK,
    SCOPE_DECLARATION_LINE,
    TITLE_BRIDESMAIDS,
    TITLE_INDEX,
    TITLE_PLAYOFF_BRACKETS,
    TITLE_PLAYOFF_RECORDS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "archive" / "championship_timeline"

_EXPECTED_FILES = {
    "index.md": TITLE_INDEX,
    "playoff_brackets.md": TITLE_PLAYOFF_BRACKETS,
    "playoff_records.md": TITLE_PLAYOFF_RECORDS,
    "bridesmaids.md": TITLE_BRIDESMAIDS,
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
        f"Unexpected files in A3 archive: {unexpected}. "
        f"The archive should contain exactly: {sorted(expected)}."
    )
    assert not missing, (
        f"Missing files in A3 archive: {missing}. "
        f"The archive should contain exactly: {sorted(expected)}."
    )


def test_each_page_starts_with_h1_title() -> None:
    """Every page begins with the contracted H1 title."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        expected_title = _EXPECTED_FILES.get(path.name)
        assert expected_title is not None, (
            f"Unexpected file in A3 archive: {path.name}"
        )
        assert text.startswith(f"# {expected_title}"), (
            f"{path.name} does not start with '# {expected_title}'. "
            f"Got: {text[:80]!r}"
        )


def test_each_page_contains_scope_declaration() -> None:
    """Every page declares the archive's scope per spec section 6.2 / 3.6."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        assert SCOPE_DECLARATION_LINE in text, (
            f"{path.name} is missing the scope-declaration line. "
            f"Per spec section 6.2 every A3 archive page must contain "
            f"SCOPE_DECLARATION_LINE."
        )


def test_each_page_is_non_empty() -> None:
    """Every page has substantive content beyond the header."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        non_empty_lines = [line for line in text.splitlines() if line.strip()]
        assert len(non_empty_lines) >= 3, (
            f"{path.name} appears empty or near-empty "
            f"({len(non_empty_lines)} non-empty lines). "
            f"Every page should render at minimum a title, scope, and "
            f"either content or a 'no data available' notice."
        )


def test_playoff_brackets_crosslinks_to_championship_roll() -> None:
    """`playoff_brackets.md` cross-links to A1's championship-roll page.

    Per A3 spec section 3.1 / section 6.4: A3 surfaces the preliminary
    and semifinal rounds A1's championship-roll column does not, and
    cross-links to A1 for the championship-week row rather than
    re-rendering A1's content.
    """
    brackets_path = ARCHIVE_ROOT / "playoff_brackets.md"
    if not brackets_path.exists():
        return  # vacuous
    text = brackets_path.read_text(encoding="utf-8")
    assert CHAMPIONSHIP_ROLL_CROSSLINK in text, (
        "playoff_brackets.md is missing the cross-link to A1's "
        "championship_roll.md. Per spec section 3.1 / section 6.4 "
        "A3 cross-links rather than re-rendering A1's "
        "championship-week content."
    )
