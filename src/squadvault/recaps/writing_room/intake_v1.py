# SquadVault — Writing Room Intake v1 (schema-aligned)
#
# Canonical goals:
# - Deterministic intake from Tier1 signals into a SelectionSet
# - Strictly record included + excluded (with reason codes)
# - Withhold when no eligible signals
# - All arrays sorted lexicographically by id for determinism
#
# This module MUST NOT define a second SelectionSetV1 class.
# Always use the canonical schema SelectionSetV1.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from datetime import datetime, timezone

from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    SelectionSetV1,
    ExcludedSignal,
    ReasonDetailKV,
    ExclusionReasonCode,
    WithheldReasonCode,
)

def _details_one(k: str, v: object) -> list[ReasonDetailKV]:
    return [ReasonDetailKV(k=k, v=str(v))]



def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso_utc(s: str) -> Optional[datetime]:
    if not s or not isinstance(s, str):
        return None
    try:
        # Accept "Z"
        if s.endswith("Z"):
            s2 = s[:-1] + "+00:00"
            return datetime.fromisoformat(s2)
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _in_window(occurred_at_utc: str, window_start: str, window_end: str) -> bool:
    t = _parse_iso_utc(occurred_at_utc)
    ws = _parse_iso_utc(window_start)
    we = _parse_iso_utc(window_end)
    if not t or not ws or not we:
        return False
    return ws <= t <= we


def _boolish(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return x != 0
    if isinstance(x, str):
        return x.strip().lower() in ("1", "true", "yes", "y", "t")
    return False


@dataclass(frozen=True)
class IntakeContextV1:
    league_id: str
    season: int
    week_index: int
    window_id: str
    window_start: str
    window_end: str
    # Tests previously instantiated without created_at_utc — make optional.
    created_at_utc: str = "1970-01-01T00:00:00Z"


def _normalize_ctx_signals_args(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Tuple[IntakeContextV1, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Normalize *any* calling convention into:
      (ctx, signals_list_of_dicts, remaining_kwargs)

    Supported call styles (all valid):
      build_selection_set_v1(ctx, signals=[...])
      build_selection_set_v1(ctx=ctx, signals=[...])
      build_selection_set_v1([signals...], ctx=ctx)   # tolerate accidental swap
      build_selection_set_v1(ctx, [...])              # signals positional
      build_selection_set_v1(ctx, adapter=..., ...)   # adapter provides signals
    """
    kw = dict(kwargs)

    # Pull ctx
    ctx = kw.pop("ctx", None)
    pos = list(args)

    if ctx is None and pos:
        ctx = pos.pop(0)

    # If caller accidentally passed signals first and ctx in kwargs
    if isinstance(ctx, list) and ("ctx" in kwargs) and isinstance(kwargs.get("ctx"), IntakeContextV1):
        # swap
        pos.insert(0, ctx)
        ctx = kwargs["ctx"]

    if not isinstance(ctx, IntakeContextV1):
        raise TypeError(f"ctx must be IntakeContextV1; got {type(ctx)}")

    # created_at normalization (accept created_at_utc kw and override ctx value deterministically)
    created_at_utc = kw.pop("created_at_utc", None)
    if created_at_utc:
        ctx = IntakeContextV1(
            league_id=ctx.league_id,
            season=ctx.season,
            week_index=ctx.week_index,
            window_id=ctx.window_id,
            window_start=ctx.window_start,
            window_end=ctx.window_end,
            created_at_utc=created_at_utc,
        )

    # Signals source
    signals = kw.pop("signals", None)
    if signals is None and pos:
        signals = pos.pop(0)

    if signals is None:
        adapter = kw.pop("adapter", None)
        if adapter is not None:
            # Best-effort adapter API compatibility
            if hasattr(adapter, "iter_signals"):
                signals = list(adapter.iter_signals(ctx))
            elif hasattr(adapter, "get_signals"):
                signals = list(adapter.get_signals(ctx))
            elif hasattr(adapter, "fetch_signals"):
                signals = list(adapter.fetch_signals(ctx))
            elif hasattr(adapter, "signals_for_ctx"):
                signals = list(adapter.signals_for_ctx(ctx))
            else:
                raise TypeError("adapter provided but no supported method found (iter_signals/get_signals/fetch_signals/signals_for_ctx)")
        else:
            raise TypeError("build_selection_set_v1 requires signals=... or adapter=...")

    if not isinstance(signals, list):
        # allow iterables
        signals = list(signals)

    # Ensure list-of-dict
    out: List[Dict[str, Any]] = []
    for s in signals:
        if isinstance(s, dict):
            out.append(s)
        else:
            # attempt dataclass / object with __dict__
            if hasattr(s, "__dict__"):
                out.append(dict(s.__dict__))
            else:
                raise TypeError(f"signal must be dict-like; got {type(s)}")

    return ctx, out, kw


def _signal_id(sig: Dict[str, Any]) -> str:
    return str(sig.get("signal_id") or sig.get("id") or "")


def _occurred_at(sig: Dict[str, Any]) -> str:
    return str(sig.get("occurred_at_utc") or sig.get("occurred_at") or sig.get("timestamp_utc") or "")


def _confidence(sig: Dict[str, Any]) -> Optional[float]:
    c = sig.get("confidence")
    if c is None:
        return None
    try:
        return float(c)
    except Exception:
        return None


def _sensitive(sig: Dict[str, Any]) -> bool:
    # tolerate multiple field names
    if "is_sensitive" in sig:
        return _boolish(sig.get("is_sensitive"))
    if "sensitive" in sig:
        return _boolish(sig.get("sensitive"))
    if "sensitivity" in sig and isinstance(sig.get("sensitivity"), str):
        return sig["sensitivity"].strip().lower() in ("high", "sensitive", "restricted")
    return False


def _has_context(sig: Dict[str, Any]) -> bool:
    # tolerate multiple names
    for k in ("has_sufficient_context", "sufficient_context", "context_ok", "has_context"):
        if k in sig:
            return _boolish(sig.get(k))
    # default to True if not specified (tests expect explicit insufficient_context signals to be excluded)
    return True


def _redundancy_key(sig: Dict[str, Any]) -> Optional[str]:
    rk = sig.get("redundancy_key") or sig.get("redundancy_group") or sig.get("dedupe_key")
    if rk is None:
        return None
    rk = str(rk).strip()
    return rk or None


_ALLOWED_CONFIDENCE = {"A", "B"}

# Deterministic intentional silence:
# If upstream provides signal dict metadata with event_type, suppress known-noise transaction types.
_INTENTIONALLY_SILENT_EVENT_TYPES = {
    "TRANSACTION_LOCK_ALL_PLAYERS",
    "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS",
}

def _details(k: str, v: object) -> list[ReasonDetailKV]:
    return [ReasonDetailKV(k=str(k), v=str(v))]

def build_selection_set_v1(*args: Any, **kwargs: Any) -> SelectionSetV1:
    """
    Build canonical SelectionSetV1.

    Determinism:
    - sort by adapter.signal_id(signal) before redundancy decisions
    - included_signal_ids is sorted in output
    - excluded is sorted by signal_id in output
    """
    ctx, signals, kw = _normalize_ctx_signals_args(args, kwargs)

    adapter = kw.pop("adapter", None)
    if adapter is None:
        raise TypeError("build_selection_set_v1 requires adapter=...")

    selection_set_id = kw.pop("selection_set_id", "")
    selection_fingerprint = kw.pop("selection_fingerprint", "")
    created_at_utc = ctx.created_at_utc or kw.pop("created_at_utc", None) or _now_utc_iso()

    # Deterministic processing order
    signals_sorted = sorted(signals, key=lambda s: adapter.signal_id(s))

    included_ids: list[str] = []
    excluded: list[ExcludedSignal] = []

    seen_redundancy: dict[str, str] = {}  # redundancy_key -> kept_signal_id

    for sig in signals_sorted:
        sid = adapter.signal_id(sig)

        # Intentional silence (only when event_type metadata present)
        if isinstance(sig, dict):
            et = sig.get("event_type")
            if et in _INTENTIONALLY_SILENT_EVENT_TYPES:
                excluded.append(
                    ExcludedSignal(
                        signal_id=sid,
                        reason_code=ExclusionReasonCode.INTENTIONAL_SILENCE,
                        details=_details("event_type", et),
                    )
                )
                continue

        # Gate: window
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

        # Gate: confidence
        conf = adapter.confidence(sig)
        if conf not in _ALLOWED_CONFIDENCE:
            excluded.append(
                ExcludedSignal(
                    signal_id=sid,
                    reason_code=ExclusionReasonCode.LOW_CONFIDENCE,
                    details=_details("confidence", conf),
                )
            )
            continue

        # Gate: lineage completeness
        if not adapter.is_lineage_complete(sig):
            excluded.append(
                ExcludedSignal(
                    signal_id=sid,
                    reason_code=ExclusionReasonCode.INSUFFICIENT_CONTEXT,
                    details=_details("lineage_complete", "false"),
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

        # Gate: redundancy (winner = first by sorted signal_id)
        rkey = adapter.redundancy_key(sig)
        if rkey:
            if rkey in seen_redundancy:
                excluded.append(
                    ExcludedSignal(
                        signal_id=sid,
                        reason_code=ExclusionReasonCode.REDUNDANT,
                        details=[
                            ReasonDetailKV(k="redundancy_key", v=str(rkey)),
                            ReasonDetailKV(k="kept_signal_id", v=str(seen_redundancy[rkey])),
                        ],
                    )
                )
                continue
            seen_redundancy[rkey] = sid

        included_ids.append(sid)

    included_ids = sorted(included_ids)
    excluded = sorted(excluded, key=lambda e: e.signal_id)

    withheld = None
    withheld_reason: Optional[WithheldReasonCode] = None
    if not included_ids:
        withheld = True
        withheld_reason = WithheldReasonCode.NO_ELIGIBLE_SIGNALS

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
        notes=[],
        withheld=withheld,
        withheld_reason=withheld_reason,
    )
