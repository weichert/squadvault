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
from dataclasses import dataclass

from squadvault.core.recaps.selection.weekly_windows_v1 import WeeklyWindow, window_for_week_index
from squadvault.core.storage.db_utils import row_to_dict as _row_to_dict
from squadvault.core.storage.session import DatabaseSession

# -------------------------
# Allowlist (v1)
# -------------------------

def _load_allowlist_event_types() -> list[str]:
    """
    Pull allowlist from config if present. Provide a conservative fallback.
    """
    # Preferred location in this repo (based on earlier work)
    try:
        from squadvault.config.recap_event_allowlist_v1 import ALLOWLIST_EVENT_TYPES  # type: ignore
        if isinstance(ALLOWLIST_EVENT_TYPES, (list, tuple)) and ALLOWLIST_EVENT_TYPES:
            return [str(x) for x in ALLOWLIST_EVENT_TYPES]
    except (ImportError, AttributeError):
        pass

    # Conservative fallback (must match your current MVP coverage)
    return [
        "TRANSACTION_FREE_AGENT",
        "TRANSACTION_TRADE",
        "TRANSACTION_BBID_WAIVER",
        "WAIVER_BID_AWARDED",
        "WEEKLY_MATCHUP_RESULT",
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
    canonical_ids: list[str]
    counts_by_type: dict[str, int]
    fingerprint: str



# Safe window modes that produce a usable [start, end) boundary.
# Must stay in sync with recap_week_gating_check.SAFE_WINDOW_MODES.
_SAFE_WINDOW_MODES = {"LOCK_TO_LOCK", "LOCK_TO_SEASON_END", "LOCK_PLUS_7D_CAP"}


def _fingerprint_from_ids(ids: list[str]) -> str:
    # sha256 of comma-joined canonical ids
    """Compute SHA-256 fingerprint from sorted canonical IDs."""
    s = ",".join(ids).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


# _db_connect removed — use DatabaseSession instead


def select_weekly_recap_events_v1(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    *,
    allowlist_event_types: list[str] | None = None,
    season_end: str | None = None,
) -> SelectionResult:
    """
    Deterministically select recap-worthy canonical event IDs for a week.

    Parameters
    ----------
    season_end : optional ISO-8601 UTC cap for final-week windowing.
        Forwarded to window_for_week_index for weeks where the next lock
        is absent (e.g., the last week of the season).
    """
    window = window_for_week_index(
        db_path, str(league_id), int(season), int(week_index),
        season_end=season_end,
    )

    # Conservative: refuse to select if we can't compute a safe window.
    if window.mode not in _SAFE_WINDOW_MODES or not window.window_start or not window.window_end:
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

    with DatabaseSession(db_path) as conn:
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
                action_fingerprint AS canonical_id,
                occurred_at,
                event_type
            FROM canonical_events
            WHERE league_id = ?
              AND season = ?
              AND occurred_at IS NOT NULL
              AND occurred_at >= ?
              AND occurred_at <  ?
              AND event_type IN ({placeholders})
            ORDER BY occurred_at ASC, event_type ASC, action_fingerprint ASC
            """,
            [str(league_id), int(season), window.window_start, window.window_end, *allow],
        )

        rows = [_row_to_dict(r) for r in cur.fetchall()]

    canonical_ids: list[str] = [str(r["canonical_id"]) for r in rows]
    counts: dict[str, int] = {}
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
