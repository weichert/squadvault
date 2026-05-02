"""Tests for voice_variants_v1 and DatabaseSession.

voice_variants: VoiceSpec lookup, format_variant_block, unknown voice.
session: context manager, commit/rollback, row_factory.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.render.voice_variants_v1 import (
    VOICE_IDS,
    VoiceSpec,
    format_variant_block,
    get_voice_spec,
)
from squadvault.core.storage.session import DatabaseSession

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"


# ── VoiceSpec ────────────────────────────────────────────────────────

class TestGetVoiceSpec:
    def test_all_known_voices(self):
        for vid in VOICE_IDS:
            spec = get_voice_spec(vid)
            assert isinstance(spec, VoiceSpec)
            assert spec.voice_id == vid

    def test_case_insensitive(self):
        spec = get_voice_spec("NEUTRAL")
        assert spec.voice_id == "neutral"

    def test_strips_whitespace(self):
        spec = get_voice_spec("  playful  ")
        assert spec.voice_id == "playful"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown voice_id"):
            get_voice_spec("epic")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            get_voice_spec("")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            get_voice_spec(None)


class TestFormatVariantBlock:
    def test_contains_header(self):
        result = format_variant_block(voice_id="neutral", body="Hello world")
        assert "NON-CANONICAL VARIANT" in result
        assert "NEUTRAL" in result
        assert "Hello world" in result

    def test_strips_body(self):
        result = format_variant_block(voice_id="dry", body="  text  ")
        assert result.endswith("text\n")


# ── DatabaseSession ──────────────────────────────────────────────────

class TestDatabaseSession:
    def test_creates_connection(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")
        # Create DB first
        sqlite3.connect(db_path).close()
        with DatabaseSession(db_path) as con:
            assert con is not None
            con.execute("CREATE TABLE t (x TEXT)")

    def test_auto_commits_on_success(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")
        con0 = sqlite3.connect(db_path)
        con0.execute("CREATE TABLE t (x TEXT)")
        con0.commit()
        con0.close()

        with DatabaseSession(db_path) as con:
            con.execute("INSERT INTO t VALUES ('hello')")

        # Verify committed
        con2 = sqlite3.connect(db_path)
        row = con2.execute("SELECT x FROM t").fetchone()
        con2.close()
        assert row[0] == "hello"

    def test_no_commit_on_exception(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")
        con0 = sqlite3.connect(db_path)
        con0.execute("CREATE TABLE t (x TEXT)")
        con0.commit()
        con0.close()

        with pytest.raises(RuntimeError):
            with DatabaseSession(db_path) as con:
                con.execute("INSERT INTO t VALUES ('fail')")
                raise RuntimeError("boom")

        con2 = sqlite3.connect(db_path)
        row = con2.execute("SELECT COUNT(*) FROM t").fetchone()
        con2.close()
        assert row[0] == 0

    def test_row_factory_set(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")
        sqlite3.connect(db_path).close()
        with DatabaseSession(db_path) as con:
            assert con.row_factory == sqlite3.Row

    def test_works_with_schema(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")
        con0 = sqlite3.connect(db_path)
        con0.executescript(SCHEMA_PATH.read_text())
        con0.close()

        with DatabaseSession(db_path) as con:
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            assert "memory_events" in tables
            assert "recap_artifacts" in tables
