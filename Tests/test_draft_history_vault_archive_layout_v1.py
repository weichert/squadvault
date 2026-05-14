"""Tests for the Draft History Vault archive layout (A2, operational).

These tests are vacuous when no A2 archive entries exist. As the
archive fills (after the founder runs
`scripts/generate_draft_history_vault_archive.py` and commits the
output), they enforce per A2 spec section 6.4 layout invariants:

- Layout root: ``archive/draft_history_vault/`` contains exactly
  four expected markdown files (``index.md`` plus the three sub-
  shape files).
- Scope-declaration invariant per spec section 6.2 / section 3.6:
  every page contains the canonical scope-declaration line.
- H1 invariant: every page starts with an H1 title line.

The append-only invariant is enforced at the git level (regenerations
overwrite content; prior versions are preserved in git history per
spec section 5.4 / section 6.5) and is not verifiable from
filesystem state alone.

Per spec section 6.8 narrative-claim drift invariant: a structural
test asserts that no archive page contains the cautionary "third-
highest bid in league history" phrasing or similar frozen ordinal
claims that would drift across substrate regenerations.

The test surface is intentionally small. It catches structural
drift, not content drift; content quality is governed by the
render-layer unit tests (`test_draft_history_vault_render_v1.py`).
"""
from __future__ import annotations

from pathlib import Path

from squadvault.core.recaps.render.draft_history_vault_render_v1 import (
    SCOPE_DECLARATION_LINE,
    TITLE_BARGAIN_HALL,
    TITLE_BUST_HALL,
    TITLE_INDEX,
    TITLE_MOST_EXPENSIVE,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "archive" / "draft_history_vault"

_EXPECTED_FILES = {
    "index.md": TITLE_INDEX,
    "most_expensive.md": TITLE_MOST_EXPENSIVE,
    "bust_hall.md": TITLE_BUST_HALL,
    "bargain_hall.md": TITLE_BARGAIN_HALL,
}

# Per A2 spec section 6.8: phrasings that would freeze a substrate-
# derived rank claim into the archive markdown at write time. These
# drift across substrate updates and must not appear in archive
# content - the rendered ranks are derived at call time as numeric
# rank columns, not as narrative ordinal claims.
_FORBIDDEN_FROZEN_ORDINAL_PHRASES = (
    "third-highest bid",
    "second-highest bid",
    "fifth-most-expensive",
    "twelfth-worst",
    "the worst auction bust in PFL history",
    "the all-time greatest bargain",
)


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
        f"Unexpected files in A2 archive: {unexpected}. "
        f"The archive should contain exactly: {sorted(expected)}."
    )
    assert not missing, (
        f"Missing files in A2 archive: {missing}. "
        f"The archive should contain exactly: {sorted(expected)}."
    )


def test_each_page_starts_with_h1_title() -> None:
    """Every page begins with the contracted H1 title."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        expected_title = _EXPECTED_FILES.get(path.name)
        assert expected_title is not None, (
            f"Unexpected file in A2 archive: {path.name}"
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
            f"Per spec section 6.2 every A2 archive page must "
            f"contain SCOPE_DECLARATION_LINE."
        )


def test_each_page_is_non_empty() -> None:
    """Every page has substantive content beyond the header."""
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8")
        non_empty_lines = [line for line in text.splitlines() if line.strip()]
        assert len(non_empty_lines) >= 3, (
            f"{path.name} appears empty or near-empty "
            f"({len(non_empty_lines)} non-empty lines). "
            f"Every page should render at minimum a title, scope, "
            f"and either content or a 'no data available' notice."
        )


def test_no_frozen_ordinal_claims_in_archive() -> None:
    """Per spec section 6.8 narrative-claim drift principle:
    archive markdown must not contain frozen ordinal claims that
    would become stale across substrate updates.

    This test is the layout-invariant companion to the render-
    layer's same-named unit test. It enforces the invariant at
    the archive level: even if a future render change inadvertently
    introduces a frozen ordinal, this catches it before it ships.
    """
    for path in _archive_md_files():
        text = path.read_text(encoding="utf-8").lower()
        for phrase in _FORBIDDEN_FROZEN_ORDINAL_PHRASES:
            assert phrase.lower() not in text, (
                f"{path.name} contains forbidden frozen ordinal "
                f"phrase '{phrase}'. Per spec section 6.8 these "
                f"phrasings drift across substrate updates and "
                f"are forbidden in archive markdown."
            )
