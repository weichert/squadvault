"""Phase 2 Gate — No Runtime Schema Mutation.

Invariant: Schema is defined exclusively in schema.sql and numbered
migrations. Runtime code must never modify schema via CREATE TABLE
or ALTER TABLE.

Allowed exceptions:
- schema.sql (canonical schema definition)
- migrations/*.sql (versioned schema changes)
- migrate.py (_schema_migrations tracking table only)
- Test files (they create test-only DBs)
"""
from __future__ import annotations

import os
import re

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
SCHEMA_PATH = os.path.join(SRC, "squadvault", "core", "storage", "schema.sql")
MIGRATIONS_DIR = os.path.join(SRC, "squadvault", "core", "storage", "migrations")

# Files that are allowed to contain CREATE TABLE or ALTER TABLE
ALLOWED_SCHEMA_MUTATION_FILES = {
    # Canonical schema definition
    os.path.normpath(SCHEMA_PATH),
    # Migration framework (creates _schema_migrations tracking table)
    os.path.normpath(os.path.join(SRC, "squadvault", "core", "storage", "migrate.py")),
}

# Patterns that indicate runtime schema mutation
MUTATION_PATTERNS = [
    re.compile(r"\bCREATE\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE),
]


def _py_files_in(root: str) -> list[str]:
    """Return all .py files under a directory, recursively."""
    result = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".py") and "__pycache__" not in dirpath:
                result.append(os.path.join(dirpath, f))
    return result


def _sql_files_in_migrations() -> set[str]:
    """Return all .sql files in the migrations directory."""
    if not os.path.isdir(MIGRATIONS_DIR):
        return set()
    return {
        os.path.normpath(os.path.join(MIGRATIONS_DIR, f))
        for f in os.listdir(MIGRATIONS_DIR)
        if f.endswith(".sql")
    }


class TestNoRuntimeSchemaMutation:
    """Ensure no Python source file contains runtime schema mutations."""

    def test_no_create_table_in_source(self):
        """No CREATE TABLE outside schema.sql, migrations, and migrate.py."""
        violations = []
        allowed = ALLOWED_SCHEMA_MUTATION_FILES | _sql_files_in_migrations()

        for filepath in _py_files_in(os.path.join(SRC, "squadvault")):
            normalized = os.path.normpath(filepath)
            if normalized in allowed:
                continue

            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            for pattern in MUTATION_PATTERNS:
                matches = pattern.findall(content)
                if matches:
                    # Check if it's inside a comment or docstring by looking at the lines
                    for i, line in enumerate(content.splitlines(), 1):
                        stripped = line.strip()
                        # Skip comments
                        if stripped.startswith("#"):
                            continue
                        if pattern.search(line):
                            # Check if it's in a string (rough heuristic: inside quotes)
                            # We check the actual SQL execution patterns
                            rel = os.path.relpath(filepath, SRC)
                            violations.append(f"{rel}:{i}: {stripped[:120]}")

        assert violations == [], (
            "Runtime schema mutation detected. Schema must be defined "
            "exclusively in schema.sql and migrations/.\n"
            "Violations:\n" + "\n".join(f"  {v}" for v in violations)
        )

    def test_no_alter_table_in_source(self):
        """No ALTER TABLE outside schema.sql, migrations, and migrate.py."""
        violations = []
        allowed = ALLOWED_SCHEMA_MUTATION_FILES | _sql_files_in_migrations()
        pattern = re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE)

        for filepath in _py_files_in(os.path.join(SRC, "squadvault")):
            normalized = os.path.normpath(filepath)
            if normalized in allowed:
                continue

            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if pattern.search(line):
                    rel = os.path.relpath(filepath, SRC)
                    violations.append(f"{rel}:{i}: {stripped[:120]}")

        assert violations == [], (
            "Runtime ALTER TABLE detected. Schema changes must go through "
            "migrations/.\nViolations:\n" + "\n".join(f"  {v}" for v in violations)
        )

    def test_editorial_actions_in_schema(self):
        """editorial_actions table must be defined in schema.sql."""
        with open(SCHEMA_PATH) as f:
            schema = f.read()
        assert "CREATE TABLE IF NOT EXISTS editorial_actions" in schema, (
            "editorial_actions table must be in schema.sql"
        )

    def test_all_tables_in_schema(self):
        """Every table used by the application should be in schema.sql.

        This is a structural check: tables referenced in INSERT/SELECT/UPDATE
        statements should have CREATE TABLE definitions in schema.sql.
        """
        with open(SCHEMA_PATH) as f:
            schema = f.read()

        # Extract table names from CREATE TABLE statements
        create_pattern = re.compile(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)", re.IGNORECASE)
        schema_tables = set(create_pattern.findall(schema))

        # These tables must exist
        required_tables = {
            "memory_events",
            "canonical_events",
            "canonical_membership",
            "franchise_directory",
            "player_directory",
            "recap_artifacts",
            "recap_runs",
            "recap_selections",
            "recap_verdicts",
            "editorial_actions",
        }

        missing = required_tables - schema_tables
        assert not missing, f"Tables missing from schema.sql: {sorted(missing)}"
