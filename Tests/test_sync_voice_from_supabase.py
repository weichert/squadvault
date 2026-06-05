"""Tests for scripts/sync_voice_from_supabase.py -- engine-table precheck only.

This is the bridge's first test. It is deliberately narrow: it covers only the
built-DB precondition added to harden the bridge against an unbuilt/unmigrated
engine DB. Full bridge-flow coverage (Supabase reads, decision core wiring,
sync_log) remains deferred until a Supabase-mocking approach is chosen -- that
deferral is why the bridge had no tests. The precheck is reachable without any
Supabase involvement: it sits before the Supabase client load and returns
EXIT_NOT_BUILT, so these tests are hermetic and make no network calls.

The bridge imports _env_bootstrap from scripts/, so the loader puts scripts/ on
sys.path before importing the module by file location.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
_BRIDGE_PATH = os.path.join(_SCRIPTS_DIR, "sync_voice_from_supabase.py")
_SCHEMA_PATH = os.path.join(
    _REPO_ROOT, "src", "squadvault", "core", "storage", "schema.sql"
)

# A non-engine-authoritative league id so main() advances past the
# ENGINE_AUTHORITATIVE early-return and reaches the precheck.
LEAGUE = "99999"


def _load_bridge():
    if _SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SCRIPTS_DIR)
    spec = importlib.util.spec_from_file_location("sync_voice_bridge_under_test", _BRIDGE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the bridge defines @dataclass types under
    # `from __future__ import annotations`, and dataclass field resolution looks
    # the module up via sys.modules[cls.__module__]. Without this it is None.
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


class TestEngineVoiceTableReady:
    def test_ready_on_schema_db(self, tmp_path):
        mod = _load_bridge()
        assert mod.engine_voice_table_ready(_schema_db(tmp_path)) is True

    def test_not_ready_on_unbuilt_db(self, tmp_path):
        mod = _load_bridge()
        assert mod.engine_voice_table_ready(_unbuilt_db(tmp_path)) is False

    def test_not_ready_on_missing_file_and_does_not_create_it(self, tmp_path):
        mod = _load_bridge()
        missing = str(tmp_path / "nope.sqlite")
        assert mod.engine_voice_table_ready(missing) is False
        # D8a: the readiness check must not create the file.
        assert not os.path.exists(missing)


class TestBridgePrecheck:
    def test_unbuilt_db_exits_not_built(self, tmp_path):
        mod = _load_bridge()
        db = _unbuilt_db(tmp_path)
        assert mod.main(["--league-id", LEAGUE, "--db", db]) == mod.EXIT_NOT_BUILT

    def test_unbuilt_db_dry_run_exits_not_built(self, tmp_path):
        # The regression motivating this precheck: --dry-run must report the
        # missing table, not advance to a "would write" decision.
        mod = _load_bridge()
        db = _unbuilt_db(tmp_path)
        assert mod.main(["--league-id", LEAGUE, "--db", db, "--dry-run"]) == mod.EXIT_NOT_BUILT

    def test_missing_db_file_exits_not_built(self, tmp_path):
        mod = _load_bridge()
        missing = str(tmp_path / "nope.sqlite")
        assert mod.main(["--league-id", LEAGUE, "--db", missing]) == mod.EXIT_NOT_BUILT
