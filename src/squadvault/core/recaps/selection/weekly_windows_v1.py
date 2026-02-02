#!/usr/bin/env python3
"""
Weekly windowing (v1)

Primary mode:
- LOCK_TO_LOCK
  Window is [start_lock, next_lock)

End-of-season fallback (deterministic, safe):
- LOCK_TO_SEASON_END
  Window is [start_lock, season_end)
- LOCK_PLUS_7D_CAP
  Window is [start_lock, start_lock + 7 days)

If no safe boundary can be computed, the window is UNSAFE.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import sqlite3
from typing import Optional, List


LOCK_EVENT_TYPE = "TRANSACTION_LOCK_ALL_PLAYERS"

# Deterministic UNSAFE reason codes (stable, finite set)
WINDOW_MISSING_LOCKS = "WINDOW_MISSING_LOCKS"
WINDOW_INCONSISTENT_LOCK_ORDER = "WINDOW_INCONSISTENT_LOCK_ORDER"
WINDOW_UNSAFE_TO_COMPUTE = "WINDOW_UNSAFE_TO_COMPUTE"


@dataclass(frozen=True)
class WeeklyWindow:
    mode: str  # LOCK_TO_LOCK | LOCK_TO_SEASON_END | LOCK_PLUS_7D_CAP | UNSAFE
    week_index: int
    window_start: Optional[str]
    window_end: Optional[str]
    start_lock: Optional[str]
    next_lock: Optional[str]
    reason: Optional[str] = None


def _db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_iso_z(s: str) -> dt.datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def _to_iso_z(t: dt.datetime) -> str:
    return (
        t.astimezone(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _fetch_lock_times(conn: sqlite3.Connection, league_id: str, season: int) -> List[str]:
    # IMPORTANT: MFL can emit multiple lock events at the same timestamp (e.g. per division).
    # Weekly windows must be computed off UNIQUE lock times or week_index will drift.
    rows = conn.execute(
        """
        SELECT DISTINCT occurred_at
        FROM canonical_events
        WHERE league_id=? AND season=? AND event_type=?
          AND occurred_at IS NOT NULL
        ORDER BY occurred_at
        """,
        (league_id, season, LOCK_EVENT_TYPE),
    ).fetchall()
    return [str(r["occurred_at"]) for r in rows]


def window_for_week_index(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    *,
    season_end: Optional[str] = None,
) -> WeeklyWindow:
    """
    Compute a deterministic weekly window.

    Mapping:
    - week_index 1 → first lock
    - week_index 2 → second lock
    - ...

    End boundary:
    - next lock if present
    - else season_end if provided
    - else +7 days from start_lock
    """

    if week_index <= 0:
        return WeeklyWindow(
            mode="UNSAFE",
            week_index=week_index,
            window_start=None,
            window_end=None,
            start_lock=None,
            next_lock=None,
            reason=WINDOW_UNSAFE_TO_COMPUTE,
        )

    conn = _db_connect(db_path)
    try:
        locks = _fetch_lock_times(conn, str(league_id), int(season))
    finally:
        conn.close()

    if len(locks) < week_index:
        return WeeklyWindow(
            mode="UNSAFE",
            week_index=week_index,
            window_start=None,
            window_end=None,
            start_lock=None,
            next_lock=None,
            reason=WINDOW_MISSING_LOCKS,
        )

    start_lock = locks[week_index - 1]
    next_lock = locks[week_index] if len(locks) >= week_index + 1 else None

    # HARDENING: If the next lock is not strictly after the start lock,
    # treat this as an unsafe/degenerate window.
    # (ISO-8601 Z timestamps compare lexicographically in chronological order.)
    if next_lock is not None and next_lock <= start_lock:
        return WeeklyWindow(
            mode="UNSAFE",
            week_index=week_index,
            window_start=None,
            window_end=None,
            start_lock=start_lock,
            next_lock=next_lock,
            reason=WINDOW_INCONSISTENT_LOCK_ORDER,
        )

    # Normal case: lock-to-lock
    if next_lock:
        return WeeklyWindow(
            mode="LOCK_TO_LOCK",
            week_index=week_index,
            window_start=start_lock,
            window_end=next_lock,
            start_lock=start_lock,
            next_lock=next_lock,
        )

    # End-of-season explicit cap
    if season_end:
        try:
            _parse_iso_z(season_end)
        except Exception:
            return WeeklyWindow(
                mode="UNSAFE",
                week_index=week_index,
                window_start=None,
                window_end=None,
                start_lock=start_lock,
                next_lock=None,
                reason=WINDOW_UNSAFE_TO_COMPUTE,
            )

        return WeeklyWindow(
            mode="LOCK_TO_SEASON_END",
            week_index=week_index,
            window_start=start_lock,
            window_end=season_end,
            start_lock=start_lock,
            next_lock=None,
            reason="capped_to_season_end",
        )

    # Deterministic fallback: +7 days
    start_dt = _parse_iso_z(start_lock)
    end_dt = start_dt + dt.timedelta(days=7)

    return WeeklyWindow(
        mode="LOCK_PLUS_7D_CAP",
        week_index=week_index,
        window_start=start_lock,
        window_end=_to_iso_z(end_dt),
        start_lock=start_lock,
        next_lock=None,
        reason="capped_plus_7_days",
    )
