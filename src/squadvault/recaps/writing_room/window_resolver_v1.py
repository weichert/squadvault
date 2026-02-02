"""
Writing Room Window Resolver v1.0 (Build Phase)

Purpose:
- Resolve the weekly window boundaries deterministically from existing weekly window logic.
- Produce a stable window_id.

Rules:
- No new window logic here.
- Calls existing window selector as source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from squadvault.recaps.writing_room.identity_recipes_v1 import compute_sha256_hex_from_payload_v1


@dataclass(frozen=True, slots=True)
class WritingRoomWindowV1:
    window_id: str
    window_start: str
    window_end: str
    mode: str


def _window_id_payload_v1(
    *,
    league_id: str,
    season: int,
    week_index: int,
    window_start: str,
    window_end: str,
    mode: str,
    version: str = "v1.0",
) -> Dict[str, Any]:
    return {
        "type": "writing_room_window_id",
        "version": version,
        "league_id": league_id,
        "season": season,
        "week_index": week_index,
        "mode": mode,
        "window_start": window_start,
        "window_end": window_end,
    }


def resolve_weekly_window_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> WritingRoomWindowV1:
    # Source of truth: existing weekly window logic.
    from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index

    w = window_for_week_index(db_path, league_id, season, week_index)

    # window_for_week_index returns something like:
    # WeeklyWindow(mode='LOCK_TO_LOCK', week_index=..., window_start='...', window_end='...', ...)
    mode = getattr(w, "mode", "UNKNOWN")
    window_start = getattr(w, "window_start")
    window_end = getattr(w, "window_end")

    payload = _window_id_payload_v1(
        league_id=league_id,
        season=season,
        week_index=week_index,
        mode=str(mode),
        window_start=str(window_start),
        window_end=str(window_end),
    )
    window_id = compute_sha256_hex_from_payload_v1(payload)

    return WritingRoomWindowV1(
        window_id=window_id,
        window_start=str(window_start),
        window_end=str(window_end),
        mode=str(mode),
    )


__all__ = [
    "WritingRoomWindowV1",
    "resolve_weekly_window_v1",
]
