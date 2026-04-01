from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path


def _ensure_repo_import_paths() -> None:
    """
    Deterministic test bootstrap:
    - Add repo root for `scripts.*` imports used by some tests
    - Add src/ for src-layout packages (`squadvault`)
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
        # Copy fixture to a temp file so tests never mutate the committed DB.
        # This prevents the persistent "M fixtures/ci_squadvault.sqlite" diff.
        tmp_dir = tempfile.mkdtemp(prefix="squadvault_test_")
        tmp_db = os.path.join(tmp_dir, "ci_squadvault.sqlite")
        shutil.copy2(str(fixture_db), tmp_db)
        os.environ["SQUADVAULT_TEST_DB"] = tmp_db
        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)


def pytest_configure() -> None:
    _ensure_repo_import_paths()
    _ensure_default_test_db_env()

