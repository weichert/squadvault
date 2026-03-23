"""Editorial action persistence for recap review workflows."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Iterable, Tuple


ACTIONS = ("OPEN", "APPROVE", "REGENERATE", "WITHHOLD", "NOTES")


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_editorial_tables(conn: sqlite3.Connection) -> None:
    """Verify editorial action tables exist.

    The editorial_actions table is defined in schema.sql.
    Schema is the sole authority for table structure — no runtime
    DDL permitted (Phase 2: Eliminate Runtime Schema Mutation).
    """
    # No-op: table creation is handled by schema.sql and migrations.
    # Retained as a function to avoid changing all call sites.
    pass


def insert_editorial_action(
    conn: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
    artifact_kind: str,
    artifact_version: int,
    selection_fingerprint: Optional[str],
    action: str,
    actor: str,
    notes_md: Optional[str],
) -> None:
    """Insert an editorial action record."""
    if action not in ACTIONS:
        raise ValueError(f"Invalid action: {action}")

    ensure_editorial_tables(conn)

    conn.execute(
        """
        INSERT INTO editorial_actions (
          league_id, season, week_index, artifact_kind, artifact_version,
          selection_fingerprint, action, actor, notes_md, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            league_id,
            int(season),
            int(week_index),
            artifact_kind,
            int(artifact_version),
            selection_fingerprint,
            action,
            actor,
            notes_md,
            utc_now_iso(),
        ),
    )
    conn.commit()


def fetch_editorial_log(
    conn: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
    artifact_kind: str = "WEEKLY_RECAP",
    limit: int = 200,
) -> Iterable[Tuple]:
    """Fetch editorial action log for a week."""
    ensure_editorial_tables(conn)
    cur = conn.execute(
        """
        SELECT created_at, actor, action, artifact_version, selection_fingerprint, COALESCE(notes_md,'')
        FROM editorial_actions
        WHERE league_id=? AND season=? AND week_index=? AND artifact_kind=?
        ORDER BY id DESC
        LIMIT ?;
        """,
        (league_id, int(season), int(week_index), artifact_kind, int(limit)),
    )
    return cur.fetchall()
