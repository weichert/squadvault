# src/pfl/coverage.py
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType  # (not used here; included only if you later expose mapping views)
from typing import Iterable

from pfl.enums import InputNeed, ShowMode
from pfl.planning import ShowPlan
from pfl.schema import SegmentDefinition


@dataclass(frozen=True)
class InputNeedCoverage:
    format_id: str
    version: str
    mode: ShowMode
    needs: tuple[InputNeed, ...]  # stable order; no duplicates


def resolve_input_need_coverage(plan: ShowPlan) -> InputNeedCoverage:
    """
    Compute the exact InputNeed coverage required to render a resolved show plan.

    Deterministic union:
      - Iterate segments in plan order
      - Iterate required_inputs in segment order
      - First occurrence wins (stable order)
      - No duplicates
    """
    if not isinstance(plan, ShowPlan):
        raise TypeError("plan must be ShowPlan")

    needs_out: list[InputNeed] = []
    seen: set[InputNeed] = set()

    segments = plan.segments
    # We intentionally do not require segments to be tuple; only iterate in order.
    for seg in segments:
        if not isinstance(seg, SegmentDefinition):
            raise TypeError("each plan segment must be SegmentDefinition")

        req = seg.required_inputs
        if not isinstance(req, tuple):
            raise TypeError("segment.required_inputs must be tuple[InputNeed, ...]")

        for item in req:
            if not isinstance(item, InputNeed):
                raise TypeError("segment.required_inputs items must be InputNeed")
            if item in seen:
                continue
            seen.add(item)
            needs_out.append(item)

    return InputNeedCoverage(
        format_id=plan.format_id,
        version=plan.version,
        mode=plan.mode,
        needs=tuple(needs_out),
    )
