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

# Week-keyed event types (D-W1 Option B): these carry an explicit, reliable
# payload_json.week. For historical seasons their occurred_at is NULL, so the
# lock-derived timestamp window cannot reach them. They are selected by week
# field instead — but ONLY when occurred_at IS NULL, so any event the timestamp
# window already captures (e.g. all 2024-2025 matchups) is untouched and selection
# stays byte-identical for currently-working weeks.
WEEK_KEYED_EVENT_TYPES = frozenset({"WEEKLY_MATCHUP_RESULT"})


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

    allow = allowlist_event_types if allowlist_event_types is not None else _load_allowlist_event_types()
    allow = [str(x) for x in allow if x]
    if not allow:
        return SelectionResult(
            week_index=week_index, window=window, canonical_ids=[],
            counts_by_type={}, fingerprint=_fingerprint_from_ids([]),
        )

    window_safe = (
        window.mode in _SAFE_WINDOW_MODES
        and window.window_start
        and window.window_end
        and window.window_start != window.window_end
    )

    rows: list[dict] = []
    with DatabaseSession(db_path) as conn:
        cur = conn.cursor()

        # Path 1 - timestamp window (unchanged behavior). Only when a safe,
        # non-degenerate window exists; otherwise this path contributes nothing.
        if window_safe:
            placeholders = ",".join(["?"] * len(allow))
            cur.execute(
                f"""
                SELECT action_fingerprint AS canonical_id, occurred_at, event_type
                FROM canonical_events
                WHERE league_id = ?
                  AND season = ?
                  AND occurred_at IS NOT NULL
                  AND occurred_at >= ?
                  AND occurred_at <  ?
                  AND event_type IN ({placeholders})
                """,
                [str(league_id), int(season), window.window_start, window.window_end, *allow],
            )
            rows.extend(_row_to_dict(r) for r in cur.fetchall())

        # Path 2 - week-field selection (D-W1 Option B), a FALLBACK for historical
        # seasons whose week-keyed events are entirely un-timestamped (occurred_at
        # NULL), which the lock-derived window cannot reach. It is gated per season:
        # applied ONLY to a week-keyed type that has ZERO timestamped events in this
        # season. Any season the timestamp window already handles (e.g. 2024-2025,
        # whose matchups are timestamped) is left untouched, so its selections stay
        # byte-identical. (A lone un-timestamped event inside an otherwise-timestamped
        # season is therefore left as-is - a pre-existing data quirk, out of scope.)
        for t in (x for x in allow if x in WEEK_KEYED_EVENT_TYPES):
            has_ts = cur.execute(
                """
                SELECT 1 FROM canonical_events
                WHERE league_id = ? AND season = ? AND event_type = ?
                  AND occurred_at IS NOT NULL
                LIMIT 1
                """,
                [str(league_id), int(season), t],
            ).fetchone()
            if has_ts:
                continue  # timestamp window handles this type for this season
            cur.execute(
                """
                SELECT ce.action_fingerprint AS canonical_id, ce.occurred_at, ce.event_type
                FROM canonical_events ce
                JOIN memory_events me ON ce.best_memory_event_id = me.id
                WHERE ce.league_id = ?
                  AND ce.season = ?
                  AND ce.occurred_at IS NULL
                  AND ce.event_type = ?
                  AND CAST(json_extract(me.payload_json, '$.week') AS INTEGER) = ?
                """,
                [str(league_id), int(season), t, int(week_index)],
            )
            rows.extend(_row_to_dict(r) for r in cur.fetchall())

    # Dedup by canonical_id; deterministic order matching the prior SQL ordering
    # (occurred_at, event_type, action_fingerprint). NULL occurred_at -> "" sorts
    # first, ahead of any ISO-8601 timestamp.
    seen: dict[str, dict] = {}
    for r in rows:
        cid = str(r["canonical_id"])
        seen.setdefault(cid, r)
    ordered = sorted(
        seen.values(),
        key=lambda r: (str(r.get("occurred_at") or ""), str(r.get("event_type") or ""), str(r["canonical_id"])),
    )

    canonical_ids: list[str] = [str(r["canonical_id"]) for r in ordered]
    counts: dict[str, int] = {}
    for r in ordered:
        et = str(r.get("event_type") or "")
        counts[et] = counts.get(et, 0) + 1

    return SelectionResult(
        week_index=week_index,
        window=window,
        canonical_ids=canonical_ids,
        counts_by_type=counts,
        fingerprint=_fingerprint_from_ids(canonical_ids),
    )


__all__ = ["SelectionResult", "select_weekly_recap_events_v1"]
