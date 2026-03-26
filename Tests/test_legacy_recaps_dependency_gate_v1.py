"""Gate — Legacy Recaps Table Fully Retired.

The legacy `recaps` table has been removed from schema.sql and all consumers deleted.
No source file should contain SQL referencing it.
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

# Legacy files that have been deleted — gate verifies they stay deleted
RETIRED_FILES = [
    "core/recaps/recap_store.py",
    "consumers/recap_week_init.py",
    "consumers/recap_week_write_artifact.py",
    "consumers/recap_week_status.py",
    "consumers/recap_week_render_facts.py",
    "consumers/recap_week_selection_check.py",
    "consumers/recap_week_materialize_version.py",
    "consumers/recap_generate_weeks.py",
]


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


class TestLegacyRecapsTableRetired:
    """The recaps table is fully retired. No source file should reference it."""

    def test_no_source_file_references_recaps_table(self):
        """No Python file in src/ should contain SQL against the recaps table."""
        violations = []
        for filepath in _py_files_in(SRC):
            rel = os.path.relpath(filepath, SRC)
            if _has_recaps_table_reference(filepath):
                violations.append(rel)

        assert violations == [], (
            "Legacy recaps table reference detected — this table has been "
            "removed from schema.sql:\n" +
            "\n".join(f"  {v}" for v in violations)
        )

    def test_recaps_table_not_in_schema(self):
        """schema.sql must not define the legacy recaps table."""
        schema_path = os.path.join(SRC, "core", "storage", "schema.sql")
        with open(schema_path, encoding="utf-8") as f:
            schema_text = f.read()

        # Look for CREATE TABLE ... recaps that isn't recap_artifacts/recap_runs/etc.
        for line in schema_text.split("\n"):
            lower = line.strip().lower()
            if not lower.startswith("create table"):
                continue
            # Only flag bare "recaps" — not recap_artifacts, recap_runs, etc.
            if " recaps " in lower or " recaps(" in lower or lower.endswith(" recaps"):
                pytest.fail(
                    f"schema.sql still defines the legacy recaps table: {line.strip()}"
                )

    def test_retired_files_stay_deleted(self):
        """Legacy consumer files must not reappear."""
        reappeared = []
        for rel_path in RETIRED_FILES:
            full_path = os.path.join(SRC, rel_path)
            if os.path.exists(full_path):
                reappeared.append(rel_path)

        assert reappeared == [], (
            "Retired legacy files have reappeared:\n" +
            "\n".join(f"  {v}" for v in reappeared)
        )
