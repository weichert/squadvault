#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from squadvault.core.recaps.recap_artifacts import (
    ARTIFACT_TYPE_WEEKLY_RECAP,
    approve_recap_artifact,
    create_recap_artifact_draft_idempotent,
)

ARTIFACT_TYPE_RIVALRY = "RIVALRY_CHRONICLE_V1"


def _init_schema(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE recap_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id TEXT NOT NULL,
                season INTEGER NOT NULL,
                week_index INTEGER NOT NULL,
                artifact_type TEXT NOT NULL,
                version INTEGER NOT NULL,

                state TEXT NOT NULL,

                selection_fingerprint TEXT,
                window_start TEXT,
                window_end TEXT,
                rendered_text TEXT,

                created_at TEXT,
                created_by TEXT,
                supersedes_version INTEGER,

                approved_at TEXT,
                approved_by TEXT,

                withheld_reason TEXT
            );
            """
        )

        # Not required, but makes intent explicit / closer to prod expectations.
        con.execute(
            """
            CREATE UNIQUE INDEX uq_recap_artifacts_key
            ON recap_artifacts (league_id, season, week_index, artifact_type, version);
            """
        )
        con.commit()
    finally:
        con.close()


def _insert_weekly_row(
    db_path: str,
    *,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    state: str,
    fp: str,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO recap_artifacts (
              league_id, season, week_index,
              artifact_type, version,
              state,
              selection_fingerprint, window_start, window_end,
              rendered_text,
              created_at, created_by,
              supersedes_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026-01-01T00:00:00.000Z', 'test', NULL)
            """,
            (
                league_id,
                season,
                week_index,
                ARTIFACT_TYPE_WEEKLY_RECAP,
                version,
                state,
                fp,
                "2026-01-01T00:00:00Z",
                "2026-01-02T00:00:00Z",
                f"weekly v{version}",
            ),
        )
        con.commit()
    finally:
        con.close()


def _fetch_rows(db_path: str):
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, league_id, season, week_index, artifact_type, version, state, approved_at, approved_by
            FROM recap_artifacts
            ORDER BY id ASC
            """
        )
        return cur.fetchall()
    finally:
        con.close()


@pytest.mark.parametrize("force", [False])
def test_rivalry_chronicle_v1_artifact_type_persistence_and_approval(force: bool) -> None:
    league_id = "70985"
    season = 2024
    week_index = 1

    # Hermetic temp DB
    with tempfile.TemporaryDirectory() as td:
        db_path = str(Path(td) / "test.sqlite")
        _init_schema(db_path)

        # Seed WEEKLY_RECAP artifacts so we can prove Rivalry isn't "shadowed" by weekly namespace.
        _insert_weekly_row(
            db_path,
            league_id=league_id,
            season=season,
            week_index=week_index,
            version=1,
            state="APPROVED",
            fp="weekly_fp_v1",
        )
        _insert_weekly_row(
            db_path,
            league_id=league_id,
            season=season,
            week_index=week_index,
            version=2,
            state="DRAFT",
            fp="weekly_fp_v2",
        )

        # Create Rivalry draft: should be version=1 in the Rivalry namespace (NOT 3, NOT blocked by weekly guards).
        rivalry_fp = "rivalry_fp_v1"
        v, created_new = create_recap_artifact_draft_idempotent(
            db_path,
            league_id,
            season,
            week_index,
            rivalry_fp,
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            rendered_text="rivalry text v1",
            artifact_type=ARTIFACT_TYPE_RIVALRY,
            created_by="test",
            force=force,
        )

        assert v == 1, "Rivalry Chronicle should start at version=1 for its artifact_type namespace"
        assert created_new is True

        # Approve the Rivalry draft, explicitly passing artifact_type.
        approve_recap_artifact(
            db_path,
            league_id,
            season,
            week_index,
            version=1,
            approved_by="test",
            artifact_type=ARTIFACT_TYPE_RIVALRY,
        )

        rows = _fetch_rows(db_path)

        # Find the Rivalry row
        rivalry = [r for r in rows if r[4] == ARTIFACT_TYPE_RIVALRY and r[5] == 1]
        assert len(rivalry) == 1
        rivalry_row = rivalry[0]
        assert rivalry_row[6] == "APPROVED"
        assert rivalry_row[7] is not None  # approved_at
        assert rivalry_row[8] == "test"    # approved_by

        # Weekly rows should be unchanged (still one APPROVED, one DRAFT)
        weekly = [r for r in rows if r[4] == ARTIFACT_TYPE_WEEKLY_RECAP]
        assert len(weekly) == 2
        weekly_states = sorted([r[6] for r in weekly])
        assert weekly_states == ["APPROVED", "DRAFT"], "Approving Rivalry must not affect WEEKLY_RECAP rows"


def test_rivalry_chronicle_v1_idempotent_same_fingerprint_no_new_version() -> None:
    league_id = "70985"
    season = 2024
    week_index = 1

    with tempfile.TemporaryDirectory() as td:
        db_path = str(Path(td) / "test.sqlite")
        _init_schema(db_path)

        rivalry_fp = "rivalry_fp_v1"

        v1, created1 = create_recap_artifact_draft_idempotent(
            db_path,
            league_id,
            season,
            week_index,
            rivalry_fp,
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            rendered_text="rivalry text v1",
            artifact_type=ARTIFACT_TYPE_RIVALRY,
            created_by="test",
            force=False,
        )
        assert (v1, created1) == (1, True)

        # Same fingerprint again => should return same version, created_new=False
        v2, created2 = create_recap_artifact_draft_idempotent(
            db_path,
            league_id,
            season,
            week_index,
            rivalry_fp,
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            rendered_text="rivalry text v1 (rerun)",
            artifact_type=ARTIFACT_TYPE_RIVALRY,
            created_by="test",
            force=False,
        )
        assert (v2, created2) == (1, False)

        # And prove only one Rivalry row exists.
        con = sqlite3.connect(db_path)
        try:
            cur = con.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM recap_artifacts WHERE artifact_type=?",
                (ARTIFACT_TYPE_RIVALRY,),
            )
            assert cur.fetchone()[0] == 1
        finally:
            con.close()
