"""
Selection Set Schema v1.0 — CANONICAL TYPES

Source: WRITING_ROOM_INTAKE — Selection Set Schema (v1.0)

Scope (Build Phase / Sprint 1 T2):
- Define enums + dataclasses that match the locked schema.
- Provide deterministic "canonicalization" helpers:
  - All arrays sorted lexicographically (where applicable)
  - SHA256 helper for fingerprints / ids (recipe is caller-defined)
- NO intake logic. NO heuristics. NO new fields.

DO NOT INVENT:
- Do not create new reason codes.
- Do not auto-generate selection_set_id/window_id without an explicit recipe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Dict, List, Optional, Sequence


# ----------------------------
# Enums (locked)
# ----------------------------

class ExclusionReasonCode(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    REDUNDANT = "REDUNDANT"
    OUT_OF_WINDOW = "OUT_OF_WINDOW"
    SENSITIVITY_GUARDRAIL = "SENSITIVITY_GUARDRAIL"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    INTENT_RISK = "INTENT_RISK"
    INTENTIONAL_SILENCE = "INTENTIONAL_SILENCE"


class WithheldReasonCode(str, Enum):
    NO_ELIGIBLE_SIGNALS = "NO_ELIGIBLE_SIGNALS"
    OVERLOAD_PREFER_SILENCE = "OVERLOAD_PREFER_SILENCE"
    AMBIGUITY_PREFER_SILENCE = "AMBIGUITY_PREFER_SILENCE"
    SAFETY_GUARDRAIL = "SAFETY_GUARDRAIL"
    HUMAN_WITHHOLD = "HUMAN_WITHHOLD"


class GroupBasisCode(str, Enum):
    SAME_SUBJECT = "SAME_SUBJECT"
    SAME_SCOPE = "SAME_SCOPE"
    SAME_TIME_WINDOW = "SAME_TIME_WINDOW"
    SHARED_FACT_BASIS = "SHARED_FACT_BASIS"


class SelectionNoteCode(str, Enum):
    WINDOW_INCOMPLETE = "WINDOW_INCOMPLETE"
    WINDOW_WITHHELD = "WINDOW_WITHHELD"
    SIGNALS_EMPTY = "SIGNALS_EMPTY"
    SIGNALS_TRUNCATED = "SIGNALS_TRUNCATED"
    HUMAN_OVERRIDE_APPLIED = "HUMAN_OVERRIDE_APPLIED"


# ----------------------------
# Leaf types
# ----------------------------

@dataclass(frozen=True, slots=True)
class ReasonDetailKV:
    k: str
    v: str

    def to_dict(self) -> Dict[str, str]:
        return {"k": self.k, "v": self.v}


@dataclass(frozen=True, slots=True)
class ExcludedSignal:
    signal_id: str
    reason_code: ExclusionReasonCode
    details: Optional[List[ReasonDetailKV]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "signal_id": self.signal_id,
            "reason_code": self.reason_code.value,
        }
        if self.details:
            # Determinism: sort KVs lexicographically by (k, v)
            det = sorted((kv.to_dict() for kv in self.details), key=lambda x: (x["k"], x["v"]))
            d["details"] = det
        return d


@dataclass(frozen=True, slots=True)
class SignalGrouping:
    group_id: str
    group_basis: GroupBasisCode
    signal_ids: List[str]
    group_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "group_id": self.group_id,
            "group_basis": self.group_basis.value,
            # Determinism: sort lexicographically
            "signal_ids": sorted(self.signal_ids),
        }
        if self.group_label is not None:
            d["group_label"] = self.group_label
        return d


@dataclass(frozen=True, slots=True)
class SelectionNote:
    note_code: SelectionNoteCode
    note_kv: Optional[List[ReasonDetailKV]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"note_code": self.note_code.value}
        if self.note_kv:
            # Determinism: sort KVs lexicographically by (k, v)
            nkv = sorted((kv.to_dict() for kv in self.note_kv), key=lambda x: (x["k"], x["v"]))
            d["note_kv"] = nkv
        return d


# ----------------------------
# Root object
# ----------------------------

@dataclass(frozen=True, slots=True)
class SelectionSetV1:
    # Identity + version
    selection_set_id: str
    version: str = "v1.0"

    # Context
    league_id: str = ""
    season: int = 0
    week_index: int = 0
    window_id: str = ""
    window_start: str = ""  # ISO-8601 UTC
    window_end: str = ""    # ISO-8601 UTC

    # Determinism
    selection_fingerprint: str = ""  # caller-defined recipe; helper provided below
    created_at_utc: str = ""         # ISO-8601 UTC

    # Contents
    included_signal_ids: List[str] = field(default_factory=list)        # deterministic order
    excluded: List[ExcludedSignal] = field(default_factory=list)
    groupings: Optional[List[SignalGrouping]] = None
    notes: Optional[List[SelectionNote]] = None
    withheld: Optional[bool] = None
    withheld_reason: Optional[WithheldReasonCode] = None  # required if withheld=True

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Canonical dict representation:
        - Arrays sorted lexicographically (schema determinism rule).
        - Enums serialized by value string.
        """
        d: Dict[str, Any] = {
            "selection_set_id": self.selection_set_id,
            "version": self.version,
            "league_id": self.league_id,
            "season": self.season,
            "week_index": self.week_index,
            "window_id": self.window_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "selection_fingerprint": self.selection_fingerprint,
            "created_at_utc": self.created_at_utc,
            "included_signal_ids": sorted(self.included_signal_ids),
            # Determinism: excluded sorted by signal_id then reason_code
            "excluded": sorted(
                (e.to_dict() for e in self.excluded),
                key=lambda x: (x["signal_id"], x["reason_code"]),
            ),
        }

        if self.groupings is not None:
            # Determinism: sort groupings by group_id
            d["groupings"] = sorted((g.to_dict() for g in self.groupings), key=lambda x: x["group_id"])

        if self.notes is not None:
            # Determinism: sort notes by note_code
            d["notes"] = sorted((n.to_dict() for n in self.notes), key=lambda x: x["note_code"])

        if self.withheld is not None:
            d["withheld"] = bool(self.withheld)

        if self.withheld is True:
            if self.withheld_reason is None:
                raise ValueError("withheld_reason is required when withheld=True")
            d["withheld_reason"] = self.withheld_reason.value
        elif self.withheld_reason is not None:
            # If supplied while withheld != True, serialize anyway (backward-compatible),
            # but caller should avoid this unless explicitly required.
            d["withheld_reason"] = self.withheld_reason.value

        return d

    def to_canonical_json(self) -> str:
        """
        Canonical JSON:
        - sorted keys
        - compact separators
        """
        return canonical_json(self.to_canonical_dict())


# ----------------------------
# Determinism helpers (locked rule: SHA256)
# ----------------------------

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def sha256_of_canonical_json(obj: Any) -> str:
    """
    Helper to compute SHA256 over canonical JSON encoding.
    Use this for selection_fingerprint *only if* your fingerprint recipe is:
      sha256(canonical_json(selection_set_payload))
    If your contract recipe differs, do not use this helper.
    """
    return sha256_hex(canonical_json(obj).encode("utf-8"))


__all__ = [
    "ExclusionReasonCode",
    "WithheldReasonCode",
    "GroupBasisCode",
    "SelectionNoteCode",
    "ReasonDetailKV",
    "ExcludedSignal",
    "SignalGrouping",
    "SelectionNote",
    "SelectionSetV1",
    "canonical_json",
    "sha256_hex",
    "sha256_of_canonical_json",
]
