"""Phase 3 Gate — Legacy Recaps Table Dependency Tracker.

Tracks which source files still reference the legacy `recaps` table.
The canonical lifecycle (generate_weekly_recap_draft, approve, etc.)
must NOT depend on the recaps table.

Legacy consumers that still read from recaps are enumerated here.
As they are retired (Phase 3C), they should be removed from the
KNOWN_LEGACY_CONSUMERS set until it is empty.
"""
from __future__ import annotations

import os
import re

import pytest


SRC = os.path.join(os.path.dirname(__file__), "..", "src", "squadvault")

# SQL patterns that indicate direct recaps table usage
# (not recap_artifacts, recap_runs, recap_selections, recap_verdicts)
RECAPS_TABLE_PATTERNS = [
    re.compile(r"\bFROM\s+recaps\b", re.IGNORECASE),
    re.compile(r"\bINTO\s+recaps\b", re.IGNORECASE),
    re.compile(r"\bUPDATE\s+recaps\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\s+recaps\b", re.IGNORECASE),
]

# Files that are KNOWN to still reference the legacy recaps table.
# As each is retired, remove it from this set.
# When this set is empty, the recaps table can be dropped.
KNOWN_LEGACY_CONSUMERS = {
    "core/recaps/recap_store.py",         # Full CRUD bridge (deprecated)
    "consumers/recap_week_status.py",     # CLI status display
    "consumers/recap_week_render.py",     # CLI recap rendering
    "recaps/weekly_recap_lifecycle.py",   # Legacy fallback path (deprecated)
}

# Files that must NEVER reference the recaps table
CANONICAL_LIFECYCLE_FILES = {
    "core/recaps/recap_artifacts.py",
    "core/recaps/recap_runs.py",
    "core/recaps/selection/recap_selection_store.py",
    "core/recaps/selection/weekly_selection_v1.py",
    "core/recaps/render/render_recap_text_v1.py",
    "core/recaps/render/render_deterministic_facts_block_v1.py",
    "core/recaps/render/deterministic_bullets_v1.py",
    "core/eal/editorial_attunement_v1.py",
    "core/eal/eal_calibration_v1.py",
}


def _py_files_in(root: str) -> list[str]:
    """Return all .py files under a directory, recursively."""
    result = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".py") and "__pycache__" not in dirpath:
                result.append(os.path.join(dirpath, f))
    return result


def _has_recaps_table_reference(filepath: str) -> bool:
    """Check if a file contains SQL referencing the legacy recaps table."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    for pattern in RECAPS_TABLE_PATTERNS:
        if pattern.search(content):
            return True
    return False


class TestLegacyRecapsTableDependencies:
    """Track and enforce boundaries around legacy recaps table usage."""

    def test_canonical_lifecycle_never_queries_recaps_table(self):
        """Core lifecycle files must never contain SQL against the recaps table."""
        violations = []
        for rel_path in CANONICAL_LIFECYCLE_FILES:
            full_path = os.path.join(SRC, rel_path)
            if not os.path.exists(full_path):
                continue
            if _has_recaps_table_reference(full_path):
                violations.append(rel_path)

        assert violations == [], (
            "Canonical lifecycle files must not reference the legacy recaps table.\n"
            f"Violations: {violations}"
        )

    def test_no_new_legacy_consumers(self):
        """No file outside KNOWN_LEGACY_CONSUMERS should reference the recaps table."""
        violations = []
        for filepath in _py_files_in(SRC):
            rel = os.path.relpath(filepath, SRC)
            if rel in KNOWN_LEGACY_CONSUMERS:
                continue
            if _has_recaps_table_reference(filepath):
                violations.append(rel)

        assert violations == [], (
            "New legacy recaps table dependency detected. These files are NOT "
            "in KNOWN_LEGACY_CONSUMERS:\n" +
            "\n".join(f"  {v}" for v in violations)
        )

    def test_known_legacy_consumers_still_exist(self):
        """Each known legacy consumer should still exist (or be removed from the set)."""
        stale = []
        for rel_path in KNOWN_LEGACY_CONSUMERS:
            full_path = os.path.join(SRC, rel_path)
            if not os.path.exists(full_path):
                stale.append(rel_path)

        assert stale == [], (
            f"Stale entries in KNOWN_LEGACY_CONSUMERS (files no longer exist): {stale}"
        )
