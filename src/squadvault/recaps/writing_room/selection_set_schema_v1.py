"""
Selection Set Schema v1.0 — (SKELETON ONLY)

Contract-driven schema defining the output of Writing Room intake:
- included items
- excluded items (with explicit reason codes)
- withheld outcomes (with explicit reason codes)
- deterministic ordering + fingerprinting helpers (to be implemented)

Sprint 1 / T1: No logic. Placeholders only.
"""

from __future__ import annotations

# NOTE: We are intentionally not defining any Signal schema here.
# Signals will be treated as opaque inputs via adapters/extractors in intake_v1.

# TODO (Sprint 1 / T2): Define enums/dataclasses that match the locked Selection Set Schema v1.0.
# TODO (Sprint 1 / T2): Implement deterministic ordering rules and stable fingerprint helpers.


__all__ = [
    # Intentionally empty for skeleton stage.
]
