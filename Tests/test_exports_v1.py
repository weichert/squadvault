"""Tests for squadvault.core.exports.approved_weekly_recap_export_v1.

Covers: fetch_latest_approved, export bundle writing, edge cases.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.exports.approved_weekly_recap_export_v1 import (
    ApprovedRecapArtifact,
    ExportManifest,
    fetch_latest_approved_weekly_recap,
    write_approved_weekly_recap_export_bundle,
    _pick_rendered_text,
    _payload_from_row,
)
from squadvault.core.recaps.recap_artifacts import (
    create_recap_artifact_draft_idempotent,
    approve_recap_artifact,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024
WEEK = 1
FP = "a" * 64
RENDERED = "# Week 1 Recap\n\nSome narrative text."


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


def _create_and_approve(db_path, week=WEEK, rendered="Test text", fp=FP):
    v, _ = create_recap_artifact_draft_idempotent(
        db_path, LEAGUE, SEASON, week, fp,
        "2024-09-05T12:00:00Z", "2024-09-12T12:00:00Z",
        rendered,
    )
    approve_recap_artifact(db_path, LEAGUE, SEASON, week, v, "founder")
    return v


# ── fetch_latest_approved_weekly_recap ───────────────────────────────

class TestFetchLatestApproved:
    def test_fetches_approved(self, db):
        _create_and_approve(db, rendered=RENDERED)
        artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, WEEK)
        assert artifact.state == "APPROVED"
        assert artifact.rendered_text == RENDERED
        assert artifact.league_id == LEAGUE
        assert artifact.season == SEASON
        assert artifact.week_index == WEEK

    def test_no_approved_raises(self, db):
        # Only a DRAFT exists
        create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, FP, None, None, "draft",
        )
        with pytest.raises(RuntimeError, match="No APPROVED"):
            fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, WEEK)

    def test_empty_db_raises(self, db):
        with pytest.raises(RuntimeError, match="No APPROVED"):
            fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, WEEK)

    def test_specific_version(self, db):
        v = _create_and_approve(db, rendered="V1 text")
        artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, WEEK, version=v)
        assert artifact.version == v

    def test_latest_when_multiple(self, db):
        v1 = _create_and_approve(db, rendered="V1", fp="a" * 64)
        # Force a second version
        v2, _ = create_recap_artifact_draft_idempotent(
            db, LEAGUE, SEASON, WEEK, "b" * 64,
            None, None, "V2", force=True,
        )
        approve_recap_artifact(db, LEAGUE, SEASON, WEEK, v2, "founder")
        artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, WEEK)
        assert artifact.version == v2


# ── write_approved_weekly_recap_export_bundle ────────────────────────

class TestWriteExportBundle:
    def _make_artifact(self, rendered="Test text"):
        return ApprovedRecapArtifact(
            league_id=LEAGUE,
            season=SEASON,
            week_index=WEEK,
            version=1,
            artifact_type="WEEKLY_RECAP",
            state="APPROVED",
            selection_fingerprint=FP,
            window_start="2024-09-05T12:00:00Z",
            window_end="2024-09-12T12:00:00Z",
            approved_by="founder",
            approved_at="2024-09-12T14:00:00Z",
            rendered_text=rendered,
            payload_json={"rendered_text": rendered},
        )

    def test_writes_three_files(self, tmp_path):
        out_dir = tmp_path / "export"
        artifact = self._make_artifact()
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir)

        assert Path(manifest.recap_md).exists()
        assert Path(manifest.recap_json).exists()
        assert Path(manifest.metadata_json).exists()

    def test_recap_md_content(self, tmp_path):
        out_dir = tmp_path / "export"
        artifact = self._make_artifact(rendered="Hello recap")
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir)

        content = Path(manifest.recap_md).read_text()
        assert "Hello recap" in content

    def test_metadata_json_content(self, tmp_path):
        out_dir = tmp_path / "export"
        artifact = self._make_artifact()
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir)

        meta = json.loads(Path(manifest.metadata_json).read_text())
        assert meta["league_id"] == LEAGUE
        assert meta["state"] == "APPROVED"
        assert meta["export_format"] == "bundle_v1"

    def test_deterministic_no_timestamp(self, tmp_path):
        out_dir = tmp_path / "export"
        artifact = self._make_artifact()
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir, deterministic=True)

        meta = json.loads(Path(manifest.metadata_json).read_text())
        assert "exported_at" not in meta

    def test_non_deterministic_has_timestamp(self, tmp_path):
        out_dir = tmp_path / "export"
        artifact = self._make_artifact()
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir, deterministic=False)

        meta = json.loads(Path(manifest.metadata_json).read_text())
        assert "exported_at" in meta

    def test_empty_rendered_text(self, tmp_path):
        out_dir = tmp_path / "export"
        artifact = self._make_artifact(rendered="")
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir)
        content = Path(manifest.recap_md).read_text()
        assert content.strip() == ""


# ── end-to-end: create → approve → export ────────────────────────────

class TestEndToEnd:
    def test_full_pipeline(self, db, tmp_path):
        _create_and_approve(db, rendered=RENDERED)
        artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, WEEK)
        out_dir = tmp_path / "export"
        manifest = write_approved_weekly_recap_export_bundle(artifact, out_dir)

        assert Path(manifest.recap_md).exists()
        content = Path(manifest.recap_md).read_text()
        assert "Week 1 Recap" in content

        meta = json.loads(Path(manifest.metadata_json).read_text())
        assert meta["approved_by"] == "founder"
