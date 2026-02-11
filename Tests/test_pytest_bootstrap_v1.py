from __future__ import annotations

import sys
from pathlib import Path


def test_pytest_bootstrap_imports_available() -> None:
    """
    Guardrail test:
    Ensures pytest bootstrap correctly exposes src-layout packages.
    """

    # Should import without ModuleNotFoundError
    import squadvault  # noqa: F401
    import pfl  # noqa: F401

    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"

    sys_path_strs = [str(p) for p in sys.path]

    # src/ must be present for src-layout imports
    assert str(src_root) in sys_path_strs

    # repo root must be present for scripts.* imports
    assert str(repo_root) in sys_path_strs
