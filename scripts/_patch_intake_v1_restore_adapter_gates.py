from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

NEEDLE_START = "def build_selection_set_v1"
NEEDLE_RETURN = "return SelectionSetV1("

PATCH_BLOCK = r'''
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
'''

def main() -> int:
    s = TARGET.read_text(encoding="utf-8")

    # Hard requirement: file must already contain normalize helper; we’ll keep it.
    if "_normalize_ctx_signals_args" not in s:
        raise SystemExit("ERROR: intake_v1.py missing _normalize_ctx_signals_args; refusing to patch.")

    # Replace the existing build_selection_set_v1 definition entirely.
    m = re.search(r"\ndef build_selection_set_v1\(", s)
    if not m:
        raise SystemExit("ERROR: could not find build_selection_set_v1; refusing to patch.")

    # Find end of current build_selection_set_v1 by locating the next top-level def after it.
    start = m.start()
    m2 = re.search(r"\n^def\s+\w+\(", s[m.end():], flags=re.M)
    if m2:
        end = m.end() + m2.start()
    else:
        end = len(s)

    # Ensure we have required imports (ReasonDetailKV + Optional already in file typically)
    if "ReasonDetailKV" not in s:
        raise SystemExit("ERROR: intake_v1.py missing ReasonDetailKV import; refusing to patch.")
    if "ExclusionReasonCode" not in s or "ExcludedSignal" not in s:
        raise SystemExit("ERROR: intake_v1.py missing schema imports; refusing to patch.")

    # Ensure Optional imported (needed in patch block)
    if "Optional" not in s:
        # Try to add Optional to typing import line
        s = re.sub(r"from typing import ([^\n]+)\n", lambda mm: mm.group(0) if "Optional" in mm.group(1) else f"from typing import {mm.group(1)}, Optional\n", s, count=1)

    s2 = s[:start] + "\n" + PATCH_BLOCK.strip() + "\n" + s[end:]

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: patched adapter-first gates into {TARGET.relative_to(ROOT)}")
    print("Next: ./scripts/py -m py_compile ... and run tests")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
