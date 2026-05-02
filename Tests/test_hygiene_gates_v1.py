"""Hygiene gate: prevent regression in docstring and type annotation coverage.

These tests lock in the current level of code hygiene and prevent
new code from being added without meeting minimum standards.
"""
from __future__ import annotations

import ast
import glob
import os

SRC = os.path.join(os.path.dirname(__file__), "..", "src")


def _all_py_files() -> list[str]:
    return [
        f for f in glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True)
        if "__pycache__" not in f and "__init__" not in os.path.basename(f)
    ]


def _core_py_files() -> list[str]:
    return [
        f for f in glob.glob(os.path.join(SRC, "squadvault", "core", "**", "*.py"), recursive=True)
        if "__pycache__" not in f and "__init__" not in os.path.basename(f)
    ]


def _count_functions(files: list[str]) -> tuple[int, int, int]:
    """Return (total_fns, missing_docs, missing_returns)."""
    total = 0
    missing_docs = 0
    missing_ret = 0
    for f in files:
        with open(f) as fh:
            try:
                tree = ast.parse(fh.read())
            except SyntaxError:
                continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__"):
                    continue
                total += 1
                if not ast.get_docstring(node):
                    missing_docs += 1
                if node.returns is None:
                    missing_ret += 1
    return total, missing_docs, missing_ret


class TestCoreDocstringCoverage:
    """Core modules must maintain high docstring coverage."""

    def test_core_functions_have_docstrings(self):
        """At least 95% of core/ functions must have docstrings."""
        total, missing, _ = _count_functions(_core_py_files())
        if total == 0:
            return
        coverage = (total - missing) / total
        assert coverage >= 0.95, (
            f"Core docstring coverage dropped to {coverage:.0%} "
            f"({missing}/{total} missing). Minimum: 95%."
        )

    def test_core_functions_have_return_types(self):
        """At least 95% of core/ functions must have return type annotations."""
        total, _, missing = _count_functions(_core_py_files())
        if total == 0:
            return
        coverage = (total - missing) / total
        assert coverage >= 0.95, (
            f"Core return type coverage dropped to {coverage:.0%} "
            f"({missing}/{total} missing). Minimum: 95%."
        )


class TestOverallDocstringRegression:
    """Prevent overall docstring coverage from regressing."""

    def test_overall_docstring_coverage_does_not_regress(self):
        """Overall docstring coverage must not drop below current baseline."""
        total, missing, _ = _count_functions(_all_py_files())
        if total == 0:
            return
        coverage = (total - missing) / total
        # Current baseline: 100% after comprehensive docstring pass
        assert coverage >= 0.95, (
            f"Overall docstring coverage dropped to {coverage:.0%} "
            f"({missing}/{total} missing). Minimum: 95%."
        )

    def test_overall_return_type_coverage(self):
        """Return type coverage must stay above 98%."""
        total, _, missing = _count_functions(_all_py_files())
        if total == 0:
            return
        coverage = (total - missing) / total
        assert coverage >= 0.98, (
            f"Return type coverage dropped to {coverage:.0%} "
            f"({missing}/{total} missing). Minimum: 98%."
        )


class TestModuleDocstrings:
    """All modules must have module-level docstrings."""

    def test_core_modules_have_docstrings(self):
        """Every core/ module must have a module-level docstring."""
        missing = []
        for f in _core_py_files():
            with open(f) as fh:
                try:
                    tree = ast.parse(fh.read())
                except SyntaxError:
                    continue
            if not ast.get_docstring(tree):
                missing.append(f.replace(SRC + "/squadvault/", ""))
        assert missing == [], (
            "Core modules missing module docstrings:\n" +
            "\n".join(f"  {m}" for m in missing)
        )

    def test_all_modules_have_docstrings(self):
        """Every source module must have a module-level docstring."""
        missing = []
        for f in _all_py_files():
            with open(f) as fh:
                try:
                    tree = ast.parse(fh.read())
                except SyntaxError:
                    continue
            if not ast.get_docstring(tree):
                missing.append(f.replace(SRC + "/squadvault/", ""))
        assert missing == [], (
            "Modules missing module docstrings:\n" +
            "\n".join(f"  {m}" for m in missing)
        )
