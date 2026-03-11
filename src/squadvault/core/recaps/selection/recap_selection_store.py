"""Selection persistence: store and compare weekly selection fingerprints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import sqlite3
from datetime import datetime, timezone

from squadvault.core.recaps.selection.weekly_selection_v1 import SelectionResult
from squadvault.core.storage.session import DatabaseSession


@dataclass(frozen=True)
class StoredSelection:
    league_id: str
    season: int
    week_index: int
    selection_version: int
    window_mode: str
    window_start: Optional[str]
    window_end: Optional[str]
    event_count: int
    fingerprint: str
    computed_at: str


def _now_utc_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_stored_selection(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    selection_version: int = 1,
) -> Optional[StoredSelection]:
    """Retrieve stored selection record for a week, or None."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """
            SELECT league_id, season, week_index, selection_version,
                   window_mode, window_start, window_end,
                   event_count, fingerprint, computed_at
            FROM recap_selections
            WHERE league_id=? AND season=? AND week_index=? AND selection_version=?;
            """,
            (league_id, season, week_index, selection_version),
        ).fetchone()

    if not row:
        return None

    return StoredSelection(
        league_id=str(row[0]),
        season=int(row[1]),
        week_index=int(row[2]),
        selection_version=int(row[3]),
        window_mode=str(row[4]),
        window_start=row[5],
        window_end=row[6],
        event_count=int(row[7]),
        fingerprint=str(row[8]),
        computed_at=str(row[9]),
    )


def insert_selection_if_missing(
    db_path: str,
    league_id: str,
    season: int,
    sel: SelectionResult,
    selection_version: int = 1,
) -> bool:
    """
    Insert-only for immutability vibes:
    - returns True if inserted
    - returns False if already existed (does not overwrite)
    """
    with DatabaseSession(db_path) as con:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO recap_selections (
              league_id, season, week_index, selection_version,
              window_mode, window_start, window_end,
              event_count, fingerprint, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                league_id,
                season,
                sel.week_index,
                selection_version,
                sel.window.mode,
                sel.window.window_start,
                sel.window.window_end,
                len(sel.canonical_ids),
                sel.fingerprint,
                _now_utc_iso(),
            ),
        )
        con.commit()
        return cur.rowcount == 1


def is_stale(stored: Optional[StoredSelection], current: SelectionResult) -> bool:
    """Return True if stored selection differs from computed selection."""
    if stored is None:
        return False
    return stored.fingerprint != current.fingerprint

