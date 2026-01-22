"""
Writing Room Intake v1.0 — DETERMINISTIC (Build Phase)

Purpose:
- Accept Tier 1 signals (opaque objects)
- Apply contract-defined gates to produce a Selection Set:
  - included_signal_ids
  - excluded (with explicit reason codes)
  - withheld + withheld_reason (when applicable)
- Remain deterministic given deterministic inputs

Rules (implemented here, contract-aligned, no heuristics):
- Writing Room code may ONLY read signal data through SignalAdapterV1.
- Deterministic ordering:
  - Always sort by adapter.signal_id(signal) before applying redundancy decisions.
- Exclusion gates (hard rules):
  - OUT_OF_WINDOW             -> adapter.is_in_window(...) is False
  - LOW_CONFIDENCE            -> adapter.confidence(signal) not in {"A","B"}
  - INSUFFICIENT_CONTEXT      -> adapter.is_lineage_complete(signal) is False
  - SENSITIVITY_GUARDRAIL     -> adapter.is_sensitive(signal) is True
  - REDUNDANT                 -> duplicate non-null redundancy_key; keep first by sorted signal_id
- Withheld rules (hard):
  - NO_ELIGIBLE_SIGNALS when included_signal_ids is empty

Non-scope (explicit):
- No scoring/ranking beyond deterministic gates
- No freeform narrative logic
- No inferred fields beyond explicit reason details
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    ExcludedSignal,
    ExclusionReasonCode,
    ReasonDetailKV,
    SelectionNote,
    SelectionNoteCode,
    SelectionSetV1,
    WithheldReasonCode,
)
from squadvault.recaps.writing_room.signal_adapter_v1 import SignalAdapterV1


_ALLOWED_CONFIDENCE = {"A", "B"}


@dataclass(frozen=True, slots=True)
class IntakeContextV1:
    """
    Required context for window-based gating.
    """
    league_id: str
    season: int
    week_index: int
    window_id: str
    window_start: str  # ISO-8601 UTC
    window_end: str    # ISO-8601 UTC


def build_selection_set_v1(
    signals: Iterable[Any],
    *,
    adapter: SignalAdapterV1,
    ctx: IntakeContextV1,
    selection_set_id: str,
    created_at_utc: str,
    selection_fingerprint: str,
) -> SelectionSetV1:
    """
    Build Selection Set (v1.0) from input signals.

    Caller responsibilities (DO NOT INVENT here):
    - selection_set_id
    - created_at_utc
    - selection_fingerprint (recipe defined by caller/contract)

    Determinism:
    - Signals are sorted by signal_id prior to applying redundancy rules.
    """
    signals_list = list(signals)

    # Determinism: stable processing order
    signals_sorted = sorted(signals_list, key=lambda s: adapter.signal_id(s))

    included_ids: List[str] = []
    excluded: List[ExcludedSignal] = []
    notes: List[SelectionNote] = []

    seen_redundancy: Dict[str, str] = {}  # redundancy_key -> kept_signal_id

    for sig in signals_sorted:
        sid = adapter.signal_id(sig)

        # Gate: window inclusion
        if not adapter.is_in_window(
            sig,
            league_id=ctx.league_id,
            season=ctx.season,
            week_index=ctx.week_index,
            window_start=ctx.window_start,
            window_end=ctx.window_end,
        ):
            excluded.append(
                ExcludedSignal(
                    signal_id=sid,
                    reason_code=ExclusionReasonCode.OUT_OF_WINDOW,
                    details=None,
                )
            )
            continue

        # Gate: confidence (A/B only)
        conf = adapter.confidence(sig)
        if conf not in _ALLOWED_CONFIDENCE:
            excluded.append(
                ExcludedSignal(
                    signal_id=sid,
                    reason_code=ExclusionReasonCode.LOW_CONFIDENCE,
                    details=[ReasonDetailKV(k="confidence", v=str(conf))],
                )
            )
            continue

        # Gate: lineage completeness
        if not adapter.is_lineage_complete(sig):
            excluded.append(
                ExcludedSignal(
                    signal_id=sid,
                    reason_code=ExclusionReasonCode.INSUFFICIENT_CONTEXT,
                    details=[ReasonDetailKV(k="lineage_complete", v="false")],
                )
            )
            continue

        # Gate: sensitivity
        if adapter.is_sensitive(sig):
            excluded.append(
                ExcludedSignal(
                    signal_id=sid,
                    reason_code=ExclusionReasonCode.SENSITIVITY_GUARDRAIL,
                    details=None,
                )
            )
            continue

        # Gate: redundancy (deterministic winner = first by signal_id in sorted order)
        rkey = adapter.redundancy_key(sig)
        if rkey:
            if rkey in seen_redundancy:
                excluded.append(
                    ExcludedSignal(
                        signal_id=sid,
                        reason_code=ExclusionReasonCode.REDUNDANT,
                        details=[
                            ReasonDetailKV(k="redundancy_key", v=rkey),
                            ReasonDetailKV(k="kept_signal_id", v=seen_redundancy[rkey]),
                        ],
                    )
                )
                continue
            seen_redundancy[rkey] = sid

        included_ids.append(sid)

    # Withheld: no eligible signals
    withheld = False
    withheld_reason: Optional[WithheldReasonCode] = None

    if not included_ids:
        withheld = True
        withheld_reason = WithheldReasonCode.NO_ELIGIBLE_SIGNALS
        notes.append(SelectionNote(note_code=SelectionNoteCode.SIGNALS_EMPTY, note_kv=None))

    # SelectionSetV1 itself enforces its own determinism in to_canonical_dict()
    return SelectionSetV1(
        selection_set_id=selection_set_id,
        league_id=ctx.league_id,
        season=ctx.season,
        week_index=ctx.week_index,
        window_id=ctx.window_id,
        window_start=ctx.window_start,
        window_end=ctx.window_end,
        selection_fingerprint=selection_fingerprint,
        created_at_utc=created_at_utc,
        included_signal_ids=included_ids,
        excluded=excluded,
        notes=notes or None,
        withheld=withheld if withheld else None,
        withheld_reason=withheld_reason,
    )


__all__ = [
    "IntakeContextV1",
    "build_selection_set_v1",
]
