"""Tests for scripts/sync_to_supabase.py -- engine-recaps precheck only.

Narrow, hermetic coverage of the built-DB precondition added to the forward
sync (engine APPROVED recaps -> Supabase). The precheck sits before the
Supabase client build and returns 1, so these tests make no network calls.

This module imports ``supabase`` at top level (unlike the bridge, which lazy-
imports it), so the whole module is unimportable without that dependency, which
is not declared in requirements. The tests therefore importorskip("supabase"):
they run where the dep is installed (the operator's machine, where the sync is
actually used) and skip cleanly anywhere it is absent (a fresh CI runner).

The script imports _env_bootstrap from scripts/ and defines @dataclass types
under `from __future__ import annotations`, so the loader puts scripts/ on
sys.path and registers the module in sys.modules before exec (dataclass field
resolution looks the module up via sys.modules[cls.__module__]).
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
from pathlib import Path

import pytest

pytest.importorskip("supabase")

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
_SCRIPT_PATH = os.path.join(_SCRIPTS_DIR, "sync_to_supabase.py")
_SCHEMA_PATH = os.path.join(
    _REPO_ROOT, "src", "squadvault", "core", "storage", "schema.sql"
)

LEAGUE = "70985"


def _load_sync():
    if _SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SCRIPTS_DIR)
    spec = importlib.util.spec_from_file_location("sync_to_supabase_under_test", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _schema_db(tmp_path, name="engine.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(_SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _unbuilt_db(tmp_path, name="unbuilt.sqlite"):
    db_path = str(tmp_path / name)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE unrelated (x INTEGER)")
    con.close()
    return db_path


class TestEngineRecapsReady:
    def test_ready_on_schema_db(self, tmp_path):
        mod = _load_sync()
        assert mod._engine_recaps_ready(Path(_schema_db(tmp_path))) is True

    def test_not_ready_on_unbuilt_db(self, tmp_path):
        mod = _load_sync()
        assert mod._engine_recaps_ready(Path(_unbuilt_db(tmp_path))) is False

    def test_not_ready_on_missing_file_and_does_not_create_it(self, tmp_path):
        mod = _load_sync()
        missing = tmp_path / "nope.sqlite"
        assert mod._engine_recaps_ready(missing) is False
        assert not missing.exists()


class TestSyncPreflight:
    def test_unbuilt_db_dry_run_returns_1(self, tmp_path):
        mod = _load_sync()
        db = _unbuilt_db(tmp_path)
        assert mod.main(["--dry-run", "--db", db, "--league-canonical-id", LEAGUE]) == 1

    def test_unbuilt_db_live_returns_1_before_client(self, tmp_path):
        # Pre-flight returns before _build_client(), so no Supabase creds/network
        # are needed even without --dry-run.
        mod = _load_sync()
        db = _unbuilt_db(tmp_path)
        assert mod.main(["--db", db, "--league-canonical-id", LEAGUE]) == 1

    def test_missing_db_returns_1(self, tmp_path):
        mod = _load_sync()
        missing = str(tmp_path / "nope.sqlite")
        assert mod.main(["--dry-run", "--db", missing, "--league-canonical-id", LEAGUE]) == 1
