from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional
from squadvault.core.recaps.selection.recap_selection_store import (
    get_stored_selection,
    insert_selection_if_missing,
    is_stale,
)

def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def get_latest_recap_version(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[int]:
    """
    Returns the highest recap_version for this week, or None if no recaps exist.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT MAX(recap_version)
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=?;
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()

    return row[0] if row and row[0] is not None else None


def insert_recap(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    recap_version: int,
    selection_fingerprint: str,
    window_start: Optional[str],
    window_end: Optional[str],
    status: str = "ACTIVE",
) -> None:
    """
    Inserts a recap metadata row.
    Does NOT overwrite anything.
    """
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO recaps (
              league_id, season, week_index,
              recap_version, selection_version,
              selection_fingerprint,
              window_start, window_end,
              status, created_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?);
            """,
            (
                league_id,
                season,
                week_index,
                recap_version,
                selection_fingerprint,
                window_start,
                window_end,
                status,
                _now_utc_iso(),
            ),
        )
        con.commit()
    finally:
        con.close()

def recap_exists(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> bool:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT 1
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=?
            LIMIT 1;
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()
    return row is not None

def insert_recap_v1_if_missing(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    selection_fingerprint: str,
    window_start: Optional[str],
    window_end: Optional[str],
) -> bool:
    """
    Insert recap_version=1 if no recap exists for this week.
    Returns True if inserted, False if already existed.
    """
    if recap_exists(db_path, league_id, season, week_index):
        return False

    insert_recap(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        recap_version=1,
        selection_fingerprint=selection_fingerprint,
        window_start=window_start,
        window_end=window_end,
        status="ACTIVE",
    )
    return True

from typing import Tuple  # add near top if not present


def get_latest_recap_row(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[tuple]:
    """
    Returns (recap_version, selection_fingerprint, status) for the latest recap, or None.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT recap_version, selection_fingerprint, status
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=?
            ORDER BY recap_version DESC
            LIMIT 1;
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()
    return row

def upsert_selection_if_stale(db_path: str, league_id: str, season: int, sel) -> str:
    """
    Persist selection deterministically:
    - INSERT if missing
    - UPDATE fingerprint + computed_at if stale
    - NOOP if fresh

    Returns: "INSERTED" | "UPDATED" | "NOOP"
    """
    from datetime import datetime, timezone
    import sqlite3

    stored = get_stored_selection(db_path, league_id, season, sel.week_index)

    if stored is None:
        insert_selection_if_missing(db_path, league_id, season, sel)
        return "INSERTED"

    if is_stale(stored, sel):
        con = sqlite3.connect(db_path)
        try:
            con.execute(
                """
                UPDATE recap_selections
                SET fingerprint = ?, computed_at = ?
                WHERE league_id = ? AND season = ? AND week_index = ?
                """,
                (
                    sel.fingerprint,
                    datetime.now(timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z"),
                    league_id,
                    season,
                    sel.week_index,
                ),
            )
            con.commit()
        finally:
            con.close()

        return "UPDATED"

    return "NOOP"

def update_recap_status(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    recap_version: int,
    status: str,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            UPDATE recaps
            SET status=?
            WHERE league_id=? AND season=? AND week_index=? AND recap_version=?;
            """,
            (status, league_id, season, week_index, recap_version),
        )
        con.commit()
    finally:
        con.close()


def mark_latest_stale_if_needed(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    current_fingerprint: str,
) -> bool:
    """
    If latest recap exists and fingerprint differs, mark it STALE.
    Returns True if marked stale, else False.
    """
    latest = get_latest_recap_row(db_path, league_id, season, week_index)
    if latest is None:
        return False

    latest_version, latest_fp, latest_status = int(latest[0]), str(latest[1]), str(latest[2])
    if latest_fp == current_fingerprint:
        return False

    # Only mark stale if it isn't already stale/superseded
    if latest_status != "STALE":
        update_recap_status(db_path, league_id, season, week_index, latest_version, "STALE")
    return True


def insert_regenerated_recap(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    current_fingerprint: str,
    window_start: Optional[str],
    window_end: Optional[str],
) -> int:
    """
    Inserts a new recap version (latest+1) as ACTIVE and marks previous ACTIVE/STALE as SUPERSEDED.
    Returns new recap_version.
    """
    latest = get_latest_recap_row(db_path, league_id, season, week_index)
    new_version = 1 if latest is None else int(latest[0]) + 1

    # Mark *all* existing recaps for this week as SUPERSEDED (simple v1 rule)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            UPDATE recaps
            SET status='SUPERSEDED'
            WHERE league_id=? AND season=? AND week_index=?;
            """,
            (league_id, season, week_index),
        )
        con.commit()
    finally:
        con.close()

    insert_recap(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        recap_version=new_version,
        selection_fingerprint=current_fingerprint,
        window_start=window_start,
        window_end=window_end,
        status="ACTIVE",
    )
    return new_version

def set_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    recap_version: int,
    artifact_path: str,
    artifact_json: str,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            UPDATE recaps
            SET artifact_path=?, artifact_json=?
            WHERE league_id=? AND season=? AND week_index=? AND recap_version=?;
            """,
            (artifact_path, artifact_json, league_id, season, week_index, recap_version),
        )
        con.commit()
    finally:
        con.close()

ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"


def ensure_weekly_recap_artifact_row_if_missing(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    *,
    state: str,
    selection_fingerprint: str,
    window_start: Optional[str],
    window_end: Optional[str],
    created_by: str = "system:write",
) -> bool:
    """
    Insert-only bridge into recap_artifacts for recap_week_render.py.

    Returns True if inserted, False if already existed.

    IMPORTANT:
    - Does NOT overwrite existing recap_artifacts rows.
    - Does NOT mutate lifecycle fields (approval/supersedence/etc.) on conflict.
    """
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO recap_artifacts (
              league_id, season, week_index,
              artifact_type, version,
              state,
              selection_fingerprint, window_start, window_end,
              rendered_text,
              created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            ON CONFLICT(league_id, season, week_index, artifact_type, version)
            DO NOTHING;
            """,
            (
                league_id,
                season,
                week_index,
                ARTIFACT_TYPE_WEEKLY_RECAP,
                version,
                state,
                selection_fingerprint,
                window_start,
                window_end,
                created_by,
            ),
        )
        con.commit()
        return (cur.rowcount or 0) > 0
    finally:
        con.close()

