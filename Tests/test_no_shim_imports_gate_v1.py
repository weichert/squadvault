"""Phase 4 Gate — No Imports Through Deprecated Shim Paths.

All shims now emit DeprecationWarning. No source or test file should
import through shim paths — they must use canonical paths directly.
"""
from __future__ import annotations

import ast
import os

import pytest


SRC = os.path.join(os.path.dirname(__file__), "..", "src", "squadvault")
TESTS = os.path.dirname(__file__)

DEPRECATED_IMPORT_PATHS = {
    "squadvault.core_engine.editorial_attunement_v1": "squadvault.core.eal.editorial_attunement_v1",
    "squadvault.core_engine": "squadvault.core.eal",
    "squadvault.eal.consume_v1": "squadvault.core.eal.consume_v1",
    "squadvault.recaps.deterministic_bullets_v1": "squadvault.core.recaps.render.deterministic_bullets_v1",
    "squadvault.recaps.select_weekly_recap_events_v1": "squadvault.core.recaps.selection.weekly_selection_v1",
    "squadvault.core.recaps.weekly_recap_lifecycle": "squadvault.recaps.weekly_recap_lifecycle",
    "squadvault.core.canonicalize.run_ingest_then_canonicalize": "squadvault.ops.run_ingest_then_canonicalize",
}

SHIM_FILES = {
    os.path.normpath(os.path.join(SRC, "..", "squadvault", "core_engine", "editorial_attunement_v1.py")),
    os.path.normpath(os.path.join(SRC, "..", "squadvault", "eal", "consume_v1.py")),
    os.path.normpath(os.path.join(SRC, "..", "squadvault", "recaps", "deterministic_bullets_v1.py")),
    os.path.normpath(os.path.join(SRC, "..", "squadvault", "recaps", "select_weekly_recap_events_v1.py")),
    os.path.normpath(os.path.join(SRC, "..", "squadvault", "core", "recaps", "weekly_recap_lifecycle.py")),
    os.path.normpath(os.path.join(SRC, "..", "squadvault", "core", "canonicalize", "run_ingest_then_canonicalize.py")),
}


def _get_imports(filepath):
    with open(filepath, encoding="utf-8") as f:
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


def _py_files_in(root):
    result = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".py") and "__pycache__" not in dirpath:
                result.append(os.path.join(dirpath, f))
    return result


class TestNoShimImports:
    def test_no_shim_imports_in_source(self):
        violations = []
        for filepath in _py_files_in(SRC):
            normalized = os.path.normpath(filepath)
            if normalized in SHIM_FILES:
                continue
            for imp in _get_imports(filepath):
                for deprecated in DEPRECATED_IMPORT_PATHS:
                    if imp == deprecated or imp.startswith(deprecated + "."):
                        canonical = DEPRECATED_IMPORT_PATHS[deprecated]
                        rel = os.path.relpath(filepath, os.path.join(SRC, ".."))
                        violations.append(f"{rel}: imports '{imp}' -> use '{canonical}'")
        assert violations == [], "Source files importing through deprecated shim paths:\n" + "\n".join(f"  {v}" for v in violations)

    def test_no_shim_imports_in_tests(self):
        violations = []
        for filepath in _py_files_in(TESTS):
            for imp in _get_imports(filepath):
                for deprecated in DEPRECATED_IMPORT_PATHS:
                    if imp == deprecated or imp.startswith(deprecated + "."):
                        canonical = DEPRECATED_IMPORT_PATHS[deprecated]
                        rel = os.path.relpath(filepath, TESTS)
                        violations.append(f"{rel}: imports '{imp}' -> use '{canonical}'")
        assert violations == [], "Test files importing through deprecated shim paths:\n" + "\n".join(f"  {v}" for v in violations)

    def test_shim_files_contain_deprecation_warning(self):
        missing_warning = []
        for shimpath in SHIM_FILES:
            if not os.path.exists(shimpath):
                continue
            with open(shimpath, encoding="utf-8") as f:
                content = f.read()
            if "DeprecationWarning" not in content and "DEPRECATED" not in content:
                rel = os.path.relpath(shimpath, os.path.join(SRC, ".."))
                missing_warning.append(rel)
        assert missing_warning == [], f"Shim files missing deprecation warning: {missing_warning}"
