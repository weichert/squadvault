"""
Signal Adapter v1.0 — SKELETON ONLY

Purpose:
- Define the ONLY allowed interface for reading data from Tier 1 signals
- Prevent Writing Room from inventing or depending on a Signal schema
- Keep intake deterministic and contract-driven

Sprint 1 / T3:
- Interface definitions only
- No logic
- No defaults
"""

from __future__ import annotations

from typing import Any, Optional, Protocol


class SignalAdapterV1(Protocol):
    """
    Adapter interface for opaque Signal objects.

    Writing Room code may ONLY access signal data via this interface.
    """

    def signal_id(self, signal: Any) -> str:
        ...

    def confidence(self, signal: Any) -> str:
        """
        Expected values (by contract):
        - "A"
        - "B"
        - "C"
        """
        ...

    def is_lineage_complete(self, signal: Any) -> bool:
        ...

    def is_in_window(
        self,
        signal: Any,
        *,
        league_id: str,
        season: int,
        week_index: int,
        window_start: str,
        window_end: str,
    ) -> bool:
        ...

    def is_sensitive(self, signal: Any) -> bool:
        ...

    def is_ambiguous(self, signal: Any) -> bool:
        ...

    def redundancy_key(self, signal: Any) -> Optional[str]:
        """
        Signals returning the same non-null redundancy_key are considered redundant.
        """
        ...


class DictSignalAdapter:
    """
    Minimal reference adapter for dict-based signals.

    Intended ONLY for tests, examples, and scaffolding.
    """

    def signal_id(self, signal: dict) -> str:
        return signal["signal_id"]

    def confidence(self, signal: dict) -> str:
        return signal["confidence"]

    def is_lineage_complete(self, signal: dict) -> bool:
        return bool(signal.get("lineage_complete", False))

    def is_in_window(
        self,
        signal: dict,
        *,
        league_id: str,
        season: int,
        week_index: int,
        window_start: str,
        window_end: str,
    ) -> bool:
        return bool(signal.get("in_window", False))

    def is_sensitive(self, signal: dict) -> bool:
        return bool(signal.get("sensitive", False))

    def is_ambiguous(self, signal: dict) -> bool:
        return bool(signal.get("ambiguous", False))

    def redundancy_key(self, signal: dict) -> Optional[str]:
        return signal.get("redundancy_key")


__all__ = [
    "SignalAdapterV1",
    "DictSignalAdapter",
]
