"""
weekly_selection_v1.py

Deterministically selects recap-worthy canonical events for a given week_index.

Contract:
- Computes a weekly window via weekly_windows_v1.window_for_week_index
- Selects canonical_events inside [window_start, window_end) AND event_type is allowlisted
- Orders deterministically: occurred_at, event_type, canonical_id
- Fingerprint: sha256 of ordered canonical_ids (as strings) joined by commas

Safety:
- If window is UNSAFE or missing boundaries, returns empty selection.
- No inference; selection is purely DB-driven + allowlist.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from squadvault.core.recaps.selection.weekly_windows_v1 import WeeklyWindow, window_for_week_index


# -------------------------
# Allowlist (v1)
# -------------------------

def _load_allowlist_event_types() -> List[str]:
    """
    Pull allowlist from config if present. Provide a conservative fallback.
    """
    # Preferred location in this repo (based on earlier work)
    try:
        from squadvault.config.recap_event_allowlist_v1 import ALLOWLIST_EVENT_TYPES  # type: ignore
        if isinstance(ALLOWLIST_EVENT_TYPES, (list, tuple)) and ALLOWLIST_EVENT_TYPES:
            return [str(x) for x in ALLOWLIST_EVENT_TYPES]
    except Exception:
        pass

    # Conservative fallback (must match your current MVP coverage)
    return [
        "TRANSACTION_FREE_AGENT",
        "TRANSACTION_TRADE",
        "TRANSACTION_BBID_WAIVER",
        "WAIVER_BID_AWARDED",
        # NOTE: lock events exist but should not be recap bullets; keep them out by default.
        # "TRANSACTION_LOCK_ALL_PLAYERS",
        # "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS",
        # "DRAFT_PICK",
    ]


# -------------------------
# Selection result
# -------------------------

@dataclass(frozen=True)
class SelectionResult:
    week_index: int
    window: WeeklyWindow
    canonical_ids: List[str]
    counts_by_type: Dict[str, int]
    fingerprint: str


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _fingerprint_from_ids(ids: List[str]) -> str:
    # sha256 of comma-joined canonical ids
    s = ",".join(ids).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


def _db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def select_weekly_recap_events_v1(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    *,
    allowlist_event_types: Optional[List[str]] = None,
) -> SelectionResult:
    """
    Deterministically select recap-worthy canonical event IDs for a week.
    """
    window = window_for_week_index(db_path, str(league_id), int(season), int(week_index))

    # Conservative: refuse to select if we leading-edge can't compute a safe window.
    if window.mode != "LOCK_TO_LOCK" or not window.window_start or not window.window_end:
        return SelectionResult(
            week_index=week_index,
            window=window,
            canonical_ids=[],
            counts_by_type={},
            fingerprint=_fingerprint_from_ids([]),
        )

    # Degenerate lock-to-lock (start == end) is treated as unsafe upstream; but double-guard anyway.
    if window.window_start == window.window_end:
        return SelectionResult(
            week_index=week_index,
            window=window,
            canonical_ids=[],
            counts_by_type={},
            fingerprint=_fingerprint_from_ids([]),
        )

    allow = allowlist_event_types if allowlist_event_types is not None else _load_allowlist_event_types()
    allow = [str(x) for x in allow if x]

    conn = _db_connect(db_path)
    try:
        cur = conn.cursor()

        # Allowlist filter (parameterized IN)
        # If allowlist is empty, return empty selection (most conservative)
        if not allow:
            return SelectionResult(
                week_index=week_index,
                window=window,
                canonical_ids=[],
                counts_by_type={},
                fingerprint=_fingerprint_from_ids([]),
            )

        placeholders = ",".join(["?"] * len(allow))

        cur.execute(
            f"""
            SELECT
              id AS canonical_id,
              occurred_at,
              event_type
            FROM canonical_events
            WHERE league_id = ?
              AND season = ?
              AND occurred_at IS NOT NULL
              AND occurred_at >= ?
              AND occurred_at <  ?
              AND event_type IN ({placeholders})
            ORDER BY occurred_at ASC, event_type ASC, id ASC
            """,
            [str(league_id), int(season), window.window_start, window.window_end, *allow],
        )

        rows = [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    canonical_ids: List[str] = [str(r["canonical_id"]) for r in rows]
    counts: Dict[str, int] = {}
    for r in rows:
        et = str(r.get("event_type") or "")
        counts[et] = counts.get(et, 0) + 1

    fp = _fingerprint_from_ids(canonical_ids)

    return SelectionResult(
        week_index=week_index,
        window=window,
        canonical_ids=canonical_ids,
        counts_by_type=counts,
        fingerprint=fp,
    )


__all__ = ["SelectionResult", "select_weekly_recap_events_v1"]
