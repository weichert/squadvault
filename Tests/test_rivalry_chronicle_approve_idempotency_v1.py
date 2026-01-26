from __future__ import annotations

import sqlite3
from pathlib import Path

from squadvault.consumers.rivalry_chronicle_approve_v1 import ApproveRequest, approve_latest
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1


def _mk_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "t.sqlite")
    con = sqlite3.connect(db_path)
    try:
        # Minimal schema required for this consumer + core approve primitive.
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
                approved_at TEXT,
                approved_by TEXT
            )
            """
        )
        con.commit()
        return db_path
    finally:
        con.close()


def _insert(
    con: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
    artifact_type: str,
    version: int,
    state: str,
) -> None:
    con.execute(
        """
        INSERT INTO recap_artifacts (
            league_id, season, week_index, artifact_type, version, state, approved_at, approved_by
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
        """,
        (league_id, season, week_index, artifact_type, version, state),
    )


def test_rivalry_chronicle_approve_latest_draft_is_idempotent(tmp_path: Path) -> None:
    db = _mk_db(tmp_path)
    league_id = "1"
    season = 2024
    week_index = 6

    con = sqlite3.connect(db)
    try:
        _insert(
            con,
            league_id=league_id,
            season=season,
            week_index=week_index,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=1,
            state="DRAFT",
        )
        _insert(
            con,
            league_id=league_id,
            season=season,
            week_index=week_index,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=2,
            state="DRAFT",
        )
        con.commit()
    finally:
        con.close()

    rc1 = approve_latest(
        ApproveRequest(
            db=db,
            league_id=int(league_id),
            season=season,
            week_index=week_index,
            approved_by="test",
            approved_at_utc="2026-01-25T01:02:03Z",
            require_draft=False,
        )
    )
    assert rc1 == 0

    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            """
            SELECT version, state, approved_by
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
            ORDER BY version
            """,
            (league_id, season, week_index, ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1),
        ).fetchall()
        assert rows == [(1, "DRAFT", None), (2, "APPROVED", "test")]
    finally:
        con.close()

    # Second approve: should be idempotent success (no DRAFT remains; APPROVED exists)
    rc2 = approve_latest(
        ApproveRequest(
            db=db,
            league_id=int(league_id),
            season=season,
            week_index=week_index,
            approved_by="test2",
            approved_at_utc="2026-01-25T01:02:04Z",
            require_draft=False,
        )
    )
    assert rc2 == 0

    con = sqlite3.connect(db)
    try:
        rows2 = con.execute(
            """
            SELECT version, state, approved_by
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
            ORDER BY version
            """,
            (league_id, season, week_index, ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1),
        ).fetchall()
        # Must remain stable (idempotent)
        assert rows2 == [(1, "DRAFT", None), (2, "APPROVED", "test")]
    finally:
        con.close()
