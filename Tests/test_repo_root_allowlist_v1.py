"""Gate test: only expected files may exist in the repo root.

Prevents accumulation of phantom files, delivery scripts, and
accidental shell output. See Defect 3 (phantom root files) and
the delivery script archival policy.
"""
from __future__ import annotations

from pathlib import Path

import pytest


# These are the ONLY files that should be tracked at repo root.
# Delivery scripts (apply_*.py) should be archived after use.
ALLOWED_ROOT_FILES = {
    ".gitignore",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
}

# Directories expected at repo root
ALLOWED_ROOT_DIRS = {
    ".git",
    "artifacts",
    "fixtures",
    "scripts",
    "src",
    "Tests",
    "docs",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


class TestRepoRootAllowlist:
    """Only expected files and directories should exist at repo root."""

    def test_no_unexpected_files(self):
        """No tracked file at repo root should be outside the allowlist.

        This catches:
        - Phantom files from shell accidents (cd, echo, fi, etc.)
        - Delivery scripts that weren't archived (apply_*.py)
        - Accidental file creation from heredoc/redirect errors
        """
        root = _repo_root()

        unexpected = []
        for entry in sorted(root.iterdir()):
            name = entry.name
            if entry.is_dir():
                if name not in ALLOWED_ROOT_DIRS and not name.startswith("."):
                    unexpected.append(f"dir: {name}")
            elif entry.is_file():
                if name not in ALLOWED_ROOT_FILES and not name.startswith("."):
                    unexpected.append(f"file: {name}")

        assert not unexpected, (
            f"Unexpected entries at repo root (archive or delete): {unexpected}"
        )

    def test_no_apply_scripts_in_root(self):
        """Delivery scripts should be archived after use, not left in root."""
        root = _repo_root()
        apply_scripts = sorted(root.glob("apply_*.py"))
        assert not apply_scripts, (
            f"Delivery scripts should be archived to scripts/_archive/delivery/: "
            f"{[p.name for p in apply_scripts]}"
        )
