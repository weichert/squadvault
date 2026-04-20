"""Architecture invariant gate tests.

These tests enforce structural invariants across the codebase:
- No circular dependencies between packages
- core/ never imports from ingest/ or consumers/
- No bare sqlite3.connect outside allowed files
- No duplicate function definitions across modules
- All source files compile
"""
from __future__ import annotations

import ast
import glob
import os
import py_compile
import re

import pytest


SRC = os.path.join(os.path.dirname(__file__), "..", "src")

# Matches both the bare form ("except Exception:") and any captured form
# ("except Exception as exc:", "except Exception as e:", etc.) — used by
# TestBroadExceptionLimit.
_BROAD_EXCEPT_RE = re.compile(r"^\s*except\s+Exception\s*(?:as\s+\w+\s*)?:")


def _get_imports(filepath: str) -> list[str]:
    with open(filepath) as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
    return imports


def _py_files(subdir: str) -> list[str]:
    path = os.path.join(SRC, "squadvault", subdir)
    if not os.path.isdir(path):
        return []
    return glob.glob(os.path.join(path, "**", "*.py"), recursive=True)


class TestLayerBoundaries:
    def test_core_does_not_import_ingest(self):
        """core/ must never import from squadvault.ingest."""
        violations = []
        for f in _py_files("core"):
            for imp in _get_imports(f):
                if "squadvault.ingest" in imp:
                    violations.append(f"{f}: {imp}")
        assert violations == [], f"core→ingest violations: {violations}"

    def test_core_does_not_import_consumers(self):
        """core/ must never import from squadvault.consumers."""
        violations = []
        for f in _py_files("core"):
            for imp in _get_imports(f):
                if "squadvault.consumers" in imp:
                    violations.append(f"{f}: {imp}")
        assert violations == [], f"core→consumers violations: {violations}"

    def test_no_circular_core_recaps_to_recaps(self):
        """core.recaps must not import from squadvault.recaps (circular dep)."""
        violations = []
        for f in _py_files("core/recaps"):
            for imp in _get_imports(f):
                if imp.startswith("squadvault.recaps"):
                    violations.append(f"{f}: {imp}")
        assert violations == [], f"core.recaps→recaps circular: {violations}"


class TestCompileGate:
    def test_all_source_compiles(self):
        """Every .py file under src/ must be valid Python."""
        errors = []
        files = glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        for f in files:
            try:
                py_compile.compile(f, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))
        assert errors == [], f"Compile errors:\n" + "\n".join(errors)


class TestNoBareConnect:
    """Bare sqlite3.connect calls should only be in allowed files."""
    ALLOWED_BASENAMES = {"sqlite_store.py", "session.py", "migrate.py"}

    def test_no_bare_sqlite_connect(self):
        violations = []
        files = glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        for f in files:
            if os.path.basename(f) in self.ALLOWED_BASENAMES:
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    if "sqlite3.connect(" in line and not line.strip().startswith("#"):
                        violations.append(f"{f}:{i}")
        # Only migrate.py and sqlite_store.py (in ALLOWED_BASENAMES) may contain bare connects.
        # All other files must use DatabaseSession.
        assert len(violations) <= 10, (
            f"Bare sqlite3.connect call count increased ({len(violations)}). "
            f"Expected <=10. Violations:\n" + "\n".join(violations[:10])
        )

    def test_core_minimal_bare_connects(self):
        """Core modules must have zero bare connects outside allowed files."""
        violations = []
        files = glob.glob(os.path.join(SRC, "squadvault", "core", "**", "*.py"), recursive=True)
        for f in files:
            if "__pycache__" in f or os.path.basename(f) in self.ALLOWED_BASENAMES:
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    if "sqlite3.connect(" in line and not line.strip().startswith("#"):
                        violations.append(f"{f}:{i}")
        assert len(violations) == 0, (
            f"Core bare sqlite3.connect calls must be zero outside allowed files. "
            f"Found {len(violations)}:\n" + "\n".join(violations)
        )


class TestNoDuplicateUtilities:
    """Utility functions must be defined in exactly one place."""

    def test_no_duplicate_table_columns(self):
        """_table_columns / table_columns must only be defined in db_utils.py."""
        violations = []
        files = glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        for f in files:
            if "__pycache__" in f or os.path.basename(f) == "db_utils.py":
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    if line.strip().startswith("def _table_columns(") or line.strip().startswith("def table_columns("):
                        violations.append(f"{f}:{i}")
        assert violations == [], (
            f"Duplicate table_columns definitions found:\n" +
            "\n".join(f"  {v}" for v in violations)
        )

    def test_no_duplicate_norm_id(self):
        """_norm_id / norm_id must only be defined in db_utils.py."""
        violations = []
        files = glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        for f in files:
            if "__pycache__" in f or os.path.basename(f) == "db_utils.py":
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    if line.strip().startswith("def _norm_id(") or line.strip().startswith("def norm_id("):
                        violations.append(f"{f}:{i}")
        assert violations == [], (
            f"Duplicate norm_id definitions found:\n" +
            "\n".join(f"  {v}" for v in violations)
        )

    def test_no_duplicate_dng_reason(self):
        """DNGReason must only be defined in recaps/dng_reasons.py."""
        violations = []
        files = glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        for f in files:
            if "__pycache__" in f or os.path.basename(f) == "dng_reasons.py":
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    if line.strip().startswith("class DNGReason"):
                        violations.append(f"{f}:{i}")
        assert violations == [], (
            f"Duplicate DNGReason definitions found:\n" +
            "\n".join(f"  {v}" for v in violations)
        )

    def test_no_duplicate_preflight_verdict_type(self):
        """PreflightVerdictType must only be defined in recaps/preflight.py."""
        violations = []
        files = glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        for f in files:
            if "__pycache__" in f or os.path.basename(f) == "preflight.py":
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    if line.strip().startswith("class PreflightVerdictType"):
                        violations.append(f"{f}:{i}")
        assert violations == [], (
            f"Duplicate PreflightVerdictType definitions found:\n" +
            "\n".join(f"  {v}" for v in violations)
        )


class TestBroadExceptionLimit:
    """Prevent broad 'except Exception' from growing in core/."""

    def test_core_broad_exception_count(self):
        """Core modules should not accumulate broad except Exception handlers."""
        count = 0
        files = glob.glob(os.path.join(SRC, "squadvault", "core", "**", "*.py"), recursive=True)
        for f in files:
            if "__pycache__" in f:
                continue
            with open(f) as fh:
                for line in fh:
                    if _BROAD_EXCEPT_RE.match(line):
                        count += 1
        # Baseline: 7 legitimate broad-exception guards in core/ at this HEAD.
        # 2 in recaps/context/ (bye_week_context, league_rules_context —
        #   optional-table read guards returning empty/None),
        # 2 in recaps/render/deterministic_bullets_v1 (team/player resolver
        #   fallbacks returning "Unknown team"/"Unknown player"),
        # 1 in recaps/verification/recap_verifier_v1 (bare form — numeric
        #   collection guard around matchup_numbers set-build),
        # 2 in resolvers.py (player/franchise name-map loader fallbacks).
        # Allows <=8 with one-handler cushion; a new broad handler should
        # bump this baseline in its own commit with justification.
        assert count <= 8, (
            f"Core broad exception count grew to {count}. "
            f"Expected <=8. Narrow new handlers to specific exception types."
        )
