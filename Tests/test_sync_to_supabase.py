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


class TestDocketIdGrammar:
    """docket_id grammar regression guard (closed 2026-06-09).

    Multi-season chronicles carry a synthetic week_index dedup key
    (end_season*100 + start_season, >= _SYNTHETIC_CHRONICLE_WEEK_FLOOR), not a
    real week. The docket must drop the W-token for them so the synthetic key
    never leaks into a public docket id (the W204510 leak). Single-season
    chronicles and weekly recaps keep their real-week W-token.
    """

    @staticmethod
    def _artifact(mod, *, season, week_index, artifact_type, version):
        return mod.EngineArtifact(
            id=1,
            league_id=LEAGUE,
            season=season,
            week_index=week_index,
            artifact_type=artifact_type,
            version=version,
            selection_fingerprint="fp",
            window_start=None,
            window_end=None,
            rendered_text="x",
            approved_at=None,
            created_at="2026-01-01T00:00:00Z",
        )

    def test_multi_season_chronicle_drops_w_token(self):
        mod = _load_sync()
        art = self._artifact(
            mod,
            season=2025,
            week_index=204510,
            artifact_type=mod.ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=3,
        )
        assert art.docket_id == "SV-2025-CHRONICLE-V03"
        assert "204510" not in art.docket_id
        assert "-W" not in art.docket_id

    def test_single_season_chronicle_keeps_w_token(self):
        mod = _load_sync()
        art = self._artifact(
            mod,
            season=2024,
            week_index=17,
            artifact_type=mod.ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1,
        )
        assert art.docket_id == "SV-2024-W17-CHRONICLE-V01"

    def test_floor_boundary_below_keeps_token(self):
        mod = _load_sync()
        art = self._artifact(
            mod,
            season=2024,
            week_index=mod._SYNTHETIC_CHRONICLE_WEEK_FLOOR - 1,
            artifact_type=mod.ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=2,
        )
        assert art.docket_id == "SV-2024-W99-CHRONICLE-V02"

    def test_floor_boundary_at_floor_drops_token(self):
        mod = _load_sync()
        art = self._artifact(
            mod,
            season=2025,
            week_index=mod._SYNTHETIC_CHRONICLE_WEEK_FLOOR,
            artifact_type=mod.ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=8,
        )
        assert art.docket_id == "SV-2025-CHRONICLE-V08"

    def test_weekly_recap_unaffected(self):
        mod = _load_sync()
        art = self._artifact(
            mod,
            season=2025,
            week_index=7,
            artifact_type=mod.ENGINE_ARTIFACT_TYPE_WEEKLY_RECAP,
            version=27,
        )
        assert art.docket_id == "SV-2025-W07-V27"
