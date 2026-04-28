"""Tests for the distribution archive layout (operational, not Platform).

These tests are vacuous when no archive entries exist. As the archive
fills, they enforce:

- Filename pattern: ``week_NN__vV.md`` (and matching ``.json``).
- Pairing: every ``.md`` has a matching ``.json``.
- Frontmatter: starts with ``---``, ends with ``---``, has all required
  keys.
- Season-directory consistency: the parent directory name matches the
  season recorded in frontmatter.

The append-only invariant cannot be verified from filesystem state
alone; that is enforced at write time inside ``scripts/distribute_recap.py``.

The test surface is intentionally small. It catches structural drift,
not content drift; content quality is governed by the Recap Review
Heuristic, not by these tests.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_RECAPS = REPO_ROOT / "archive" / "recaps"

_FILENAME_RE = re.compile(r"^week_(\d{2})__v(\d+)\.md$")

_REQUIRED_FRONTMATTER_KEYS = (
    "recap_artifact_id",
    "league_id",
    "season",
    "week_index",
    "artifact_type",
    "version",
    "state",
    "selection_fingerprint",
    "approved_by",
    "approved_at",
    "distributed_at",
    "distributed_to",
    "channel",
)


def _iter_md_files() -> list[Path]:
    if not ARCHIVE_RECAPS.exists():
        return []
    return sorted(ARCHIVE_RECAPS.glob("*/week_*__v*.md"))


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal frontmatter parser for the emitter's known schema.

    The emitter writes top-level ``key: value`` lines and one nested
    block (``companion_files:`` followed by indented ``  sub: value``
    lines). This parser captures the top-level keys, which is enough
    for structural assertions; nested keys are intentionally not
    surfaced.
    """
    if not text.startswith("---\n"):
        raise AssertionError("frontmatter does not start with '---'")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("frontmatter has no closing '---'")
    body = text[4:end]
    out: dict[str, str] = {}
    for line in body.splitlines():
        if not line or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def test_archive_recaps_files_match_naming_and_pairing() -> None:
    """Every .md is paired with a .json and matches the naming pattern."""
    for md_path in _iter_md_files():
        assert _FILENAME_RE.match(md_path.name), (
            f"unexpected archive filename: {md_path}"
        )
        json_path = md_path.with_suffix(".json")
        assert json_path.exists(), f"missing companion .json for {md_path}"


def test_archive_recaps_frontmatter_has_required_keys() -> None:
    """Every .md carries the contracted top-level frontmatter keys."""
    for md_path in _iter_md_files():
        meta = _parse_frontmatter(md_path.read_text(encoding="utf-8"))
        for key in _REQUIRED_FRONTMATTER_KEYS:
            assert key in meta, (
                f"frontmatter for {md_path} is missing required key: {key}"
            )


def test_archive_recaps_season_directory_matches_frontmatter() -> None:
    """The parent directory name matches the season in frontmatter."""
    for md_path in _iter_md_files():
        meta = _parse_frontmatter(md_path.read_text(encoding="utf-8"))
        season_in_path = md_path.parent.name
        season_in_meta = meta["season"].strip()
        assert season_in_path == season_in_meta, (
            f"season mismatch for {md_path}: path={season_in_path}, "
            f"frontmatter={season_in_meta}"
        )


def test_archive_recaps_filename_week_and_version_match_frontmatter() -> None:
    """Filename `week_NN__vV.md` agrees with frontmatter week_index/version."""
    for md_path in _iter_md_files():
        match = _FILENAME_RE.match(md_path.name)
        assert match is not None  # guarded by the naming test above
        week_in_name = int(match.group(1))
        version_in_name = int(match.group(2))
        meta = _parse_frontmatter(md_path.read_text(encoding="utf-8"))
        assert int(meta["week_index"]) == week_in_name, (
            f"week mismatch for {md_path}: "
            f"name={week_in_name}, frontmatter={meta['week_index']}"
        )
        assert int(meta["version"]) == version_in_name, (
            f"version mismatch for {md_path}: "
            f"name={version_in_name}, frontmatter={meta['version']}"
        )
