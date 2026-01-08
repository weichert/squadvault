# src/squadvault/core/recaps/selection/weekly_windows_v1.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal
import sqlite3


WindowMode = Literal["LOCK_TO_LOCK", "UNAVAILABLE"]


@dataclass(frozen=True)
class LockMarker:
    week_index: int          # 1-based index in chronological lock order (deduped by lock_time)
    lock_time: str           # ISO8601 UTC string from memory_events.occurred_at
    canonical_id: int        # canonical_events.id
    memory_id: int           # canonical_events.best_memory_event_id


@dataclass(frozen=True)
class RecapWindow:
    mode: WindowMode
    week_index: int
    window_start: Optional[str]  # ISO8601 UTC string
    window_end: Optional[str]    # ISO8601 UTC string
    start_lock: Optional[LockMarker]
    end_lock: Optional[LockMarker]


_LOCKS_SQL = """
SELECT
  ce.id AS canonical_id,
  ce.best_memory_event_id AS memory_id,
  me.occurred_at AS lock_time
FROM canonical_events ce
JOIN memory_events me ON me.id = ce.best_memory_event_id
WHERE ce.league_id = ?
  AND ce.season = ?
  AND ce.event_type = 'TRANSACTION_LOCK_ALL_PLAYERS'
  AND me.occurred_at IS NOT NULL
ORDER BY me.occurred_at ASC, ce.id ASC;
"""


def list_lock_markers(db_path: str, league_id: str, season: int) -> List[LockMarker]:
    """
    Returns lock markers in deterministic chronological order.

    IMPORTANT v1 rule:
    - Deduplicate by lock_time (keep first occurrence by canonical_id due to ORDER BY).
      This prevents zero-length windows when MFL emits multiple lock events at the same timestamp.

    week_index is 1-based and refers to the deduped lock list.
    """
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(_LOCKS_SQL, (league_id, season))
        rows: List[Tuple[int, int, str]] = cur.fetchall()
    finally:
        con.close()

    # Deduplicate by lock_time (rows are already ordered by lock_time ASC, canonical_id ASC)
    dedup: List[Tuple[int, int, str]] = []
    last_time: Optional[str] = None
    for canonical_id, memory_id, lock_time in rows:
        lt = str(lock_time)
        if last_time == lt:
            continue
        dedup.append((int(canonical_id), int(memory_id), lt))
        last_time = lt

    locks: List[LockMarker] = []
    for i, (canonical_id, memory_id, lock_time) in enumerate(dedup, start=1):
        locks.append(
            LockMarker(
                week_index=i,
                lock_time=lock_time,
                canonical_id=canonical_id,
                memory_id=memory_id,
            )
        )
    return locks


def window_for_week_index(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> RecapWindow:
    """
    Computes a lock-to-lock recap window:

      window = [locks[week_index-1], locks[week_index]) using 1-based indexing.

    Conservative v1 behavior:
    - If fewer than 2 locks exist, returns UNAVAILABLE.
    - If week_index is out of range or points to the last lock (no next lock), returns UNAVAILABLE.
    - No guessing about end times in v1.
    """
    if week_index < 1:
        raise ValueError(f"week_index must be >= 1, got {week_index}")

    locks = list_lock_markers(db_path, league_id, season)

    # Need at least two locks to define one complete week window
    if len(locks) < 2:
        return RecapWindow(
            mode="UNAVAILABLE",
            week_index=week_index,
            window_start=None,
            window_end=None,
            start_lock=None,
            end_lock=None,
        )

    # With N locks, there are N-1 full windows. Valid week_index: 1..N-1
    if week_index > len(locks) - 1:
        return RecapWindow(
            mode="UNAVAILABLE",
            week_index=week_index,
            window_start=None,
            window_end=None,
            start_lock=None,
            end_lock=None,
        )

    start_lock = locks[week_index - 1]
    end_lock = locks[week_index]  # next lock

    # Extra safety: never return a zero-length window
    if start_lock.lock_time == end_lock.lock_time:
        return RecapWindow(
            mode="UNAVAILABLE",
            week_index=week_index,
            window_start=None,
            window_end=None,
            start_lock=start_lock,
            end_lock=end_lock,
        )

    return RecapWindow(
        mode="LOCK_TO_LOCK",
        week_index=week_index,
        window_start=start_lock.lock_time,
        window_end=end_lock.lock_time,
        start_lock=start_lock,
        end_lock=end_lock,
    )
