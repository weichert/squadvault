"""Tests for scripts/set_pfl_voice.py.

The operator script lives under ``scripts/`` (not on the package path), so it
is loaded by file location via ``importlib`` to keep the test hermetic -- no
``sys.path`` mutation. The script installs the curated PFL Buddies voice as the
live engine row; these tests pin its governance behaviour: idempotency,
non-clobber, --force, --dry-run, and the load-bearing approved_by stamp that
keeps the Supabase bridge's non-clobber/engine-authoritative guards correct.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3

from squadvault.core.tone.voice_profile_v1 import (
    PFL_BUDDIES_VOICE_PROFILE,
    get_voice_profile,
    set_voice_profile,
)

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SCRIPT_PATH = os.path.join(_REPO_ROOT, "scripts", "set_pfl_voice.py")
_SCHEMA_PATH = os.path.join(
    _REPO_ROOT, "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "70985"


def _load_script():
    spec = importlib.util.spec_from_file_location("set_pfl_voice_under_test", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fresh_db(tmp_path, name="engine.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(_SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _row_count(db_path, league_id):
    con = sqlite3.connect(db_path)
    n = con.execute(
        "SELECT COUNT(*) FROM league_voice_profiles WHERE league_id=?",
        (league_id,),
    ).fetchone()[0]
    con.close()
    return n


class TestSetPflVoiceInstall:
    def test_install_into_fresh_db(self, tmp_path):
        db = _fresh_db(tmp_path)
        mod = _load_script()
        rc = mod.main(["--db", db, "--league-id", LEAGUE])
        assert rc == 0
        assert get_voice_profile(db, LEAGUE) == PFL_BUDDIES_VOICE_PROFILE.strip()
        assert _row_count(db, LEAGUE) == 1

    def test_install_stamps_commissioner_not_founding(self, tmp_path):
        # Load-bearing: approved_by must NOT start with "founding-session", or the
        # Supabase bridge's non-clobber (D5a) / engine-authoritative (D7b) guards
        # would no longer protect this row.
        db = _fresh_db(tmp_path)
        mod = _load_script()
        assert mod.main(["--db", db, "--league-id", LEAGUE]) == 0
        con = sqlite3.connect(db)
        approved_by = con.execute(
            "SELECT approved_by FROM league_voice_profiles WHERE league_id=?",
            (LEAGUE,),
        ).fetchone()[0]
        con.close()
        assert approved_by == "commissioner"
        assert not approved_by.startswith("founding-session")


class TestSetPflVoiceIdempotency:
    def test_second_run_is_noop(self, tmp_path):
        db = _fresh_db(tmp_path)
        mod = _load_script()
        assert mod.main(["--db", db, "--league-id", LEAGUE]) == 0
        assert mod.main(["--db", db, "--league-id", LEAGUE]) == 0
        assert _row_count(db, LEAGUE) == 1
        assert get_voice_profile(db, LEAGUE) == PFL_BUDDIES_VOICE_PROFILE.strip()


class TestSetPflVoiceNonClobber:
    def test_refuses_differing_row_without_force(self, tmp_path):
        db = _fresh_db(tmp_path)
        set_voice_profile(db, LEAGUE, "a hand-edited profile", approved_by="commissioner")
        mod = _load_script()
        rc = mod.main(["--db", db, "--league-id", LEAGUE])
        assert rc == 3
        # Existing row is preserved untouched.
        assert get_voice_profile(db, LEAGUE) == "a hand-edited profile"

    def test_force_replaces_differing_row(self, tmp_path):
        db = _fresh_db(tmp_path)
        set_voice_profile(db, LEAGUE, "a hand-edited profile", approved_by="commissioner")
        mod = _load_script()
        rc = mod.main(["--db", db, "--league-id", LEAGUE, "--force"])
        assert rc == 0
        assert get_voice_profile(db, LEAGUE) == PFL_BUDDIES_VOICE_PROFILE.strip()
        assert _row_count(db, LEAGUE) == 1


class TestSetPflVoiceDryRun:
    def test_dry_run_writes_nothing(self, tmp_path):
        db = _fresh_db(tmp_path)
        mod = _load_script()
        rc = mod.main(["--db", db, "--league-id", LEAGUE, "--dry-run"])
        assert rc == 0
        assert get_voice_profile(db, LEAGUE) is None
        assert _row_count(db, LEAGUE) == 0

    def test_dry_run_reports_refusal_for_differing_row(self, tmp_path):
        db = _fresh_db(tmp_path)
        set_voice_profile(db, LEAGUE, "a hand-edited profile", approved_by="commissioner")
        mod = _load_script()
        rc = mod.main(["--db", db, "--league-id", LEAGUE, "--dry-run"])
        assert rc == 0
        # Dry-run reports but does not mutate.
        assert get_voice_profile(db, LEAGUE) == "a hand-edited profile"


class TestSetPflVoiceMissingDb:
    def test_missing_db_exits_2(self, tmp_path):
        db = str(tmp_path / "does_not_exist.sqlite")
        mod = _load_script()
        assert mod.main(["--db", db, "--league-id", LEAGUE]) == 2
