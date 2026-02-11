from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_repo_import_paths() -> None:
    """
    Deterministic test bootstrap:
    - Add repo root for `scripts.*` imports used by some tests
    - Add src/ for src-layout packages (`squadvault`, `pfl`)
    """
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"

    # Prepend so local code wins over anything installed in site-packages.
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))


def _ensure_default_test_db_env() -> None:
    # Respect explicit caller configuration (CI or local overrides).
    if os.environ.get("SQUADVAULT_TEST_DB"):
        return

    repo_root = Path(__file__).resolve().parents[1]
    fixture_db = repo_root / "fixtures" / "ci_squadvault.sqlite"
    if fixture_db.exists():
        os.environ["SQUADVAULT_TEST_DB"] = str(fixture_db)


def pytest_configure() -> None:
    _ensure_repo_import_paths()
    _ensure_default_test_db_env()

