"""
Writing Room Intake v1.0 — SKELETON ONLY

Purpose:
- Accept Tier 1 signals (opaque objects)
- Apply contract-defined gates to produce a Selection Set (included/excluded/withheld)
- Remain deterministic given deterministic inputs

Sprint 1:
- Interface + signature only
- NO selection logic yet

DO NOT INVENT:
- No Signal schema
- No ranking/scoring
- No heuristics
"""

from __future__ import annotations

from typing import Any, Iterable

from squadvault.recaps.writing_room.signal_adapter_v1 import SignalAdapterV1


def build_selection_set_v1(
    signals: Iterable[Any],
    *,
    adapter: SignalAdapterV1,
    league_id: str,
    season: int,
    week_index: int,
    window_start: str,
    window_end: str,
) -> Any:
    """
    Build Selection Set (v1.0) from input signals.

    SKELETON ONLY.
    Logic will be implemented in a later task.
    """
    raise NotImplementedError("Sprint 1 skeleton: intake logic not implemented.")
