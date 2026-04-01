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
        """Return the unique signal identifier."""
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
        """Return True if signal has complete data lineage."""
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
        """Return True if signal falls within the active window."""
        ...

    def is_sensitive(self, signal: Any) -> bool:
        """Return True if signal is flagged as sensitive."""
        ...

    def is_ambiguous(self, signal: Any) -> bool:
        """Return True if signal is flagged as ambiguous."""
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
        """Return the unique signal identifier."""
        return str(signal["signal_id"])

    def confidence(self, signal: dict) -> str:
        """Return the signal confidence grade."""
        return str(signal["confidence"])

    def is_lineage_complete(self, signal: dict) -> bool:
        """Return True if signal has complete data lineage."""
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
        """Return True if signal falls within the active window."""
        return bool(signal.get("in_window", False))

    def is_sensitive(self, signal: dict) -> bool:
        """Return True if signal is flagged as sensitive."""
        return bool(signal.get("sensitive", False))

    def is_ambiguous(self, signal: dict) -> bool:
        """Return True if signal is flagged as ambiguous."""
        return bool(signal.get("ambiguous", False))

    def redundancy_key(self, signal: dict) -> Optional[str]:
        """Return a key for detecting redundant signals."""
        return signal.get("redundancy_key")


__all__ = [
    "SignalAdapterV1",
    "DictSignalAdapter",
]
