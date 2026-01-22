"""
Writing Room Intake v1.0 — (SKELETON ONLY)

Purpose:
- Accept Tier 1 signals (opaque objects)
- Apply contract-defined gates to produce a Selection Set (included/excluded/withheld)
- Remain deterministic given deterministic inputs

Sprint 1 / T1: No logic. Placeholders only.

DO NOT INVENT:
- No Signal schema in this module.
- No ranking/scoring/heuristics beyond contract gates.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional


# TODO (Sprint 1 / T3): Define a thin adapter/extractor protocol (callables or lightweight interface)
# so we can read required fields from opaque signals without inventing a signal schema.


def build_selection_set_v1(
    signals: Iterable[Any],
    *,
    season: int,
    week_index: int,
    window_start: str,
    window_end: str,
    # adapter: Optional[SignalAdapter] = None,  # TODO: introduce in T3
) -> Any:
    """
    Build Selection Set (v1.0) from input signals.

    SKELETON ONLY:
    - Signature is intentionally minimal and may be refined in T3,
      but must remain contract-aligned and deterministic.

    Returns:
        A Selection Set object (type TBD in T2/T3).
    """
    raise NotImplementedError("Sprint 1 / T1 skeleton: implement in T3.")


__all__ = [
    "build_selection_set_v1",
]
