"""
Writing Room Identity Recipes v1.0 — SAFE HELPERS (Build Phase)

Goal:
- Provide contract-safe helpers for producing stable IDs and fingerprints
- DO NOT INVENT a recipe. Callers must explicitly choose inputs.

This module offers:
- Payload builders (dict) for ids/fingerprints
- SHA256-over-canonical-json helpers

Notes:
- canonical_json() and sha256_of_canonical_json() come from Selection Set Schema v1.
- These helpers are deterministic and pure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    canonical_json,
    sha256_of_canonical_json,
)


def selection_set_id_payload_v1(
    *,
    league_id: str,
    season: int,
    week_index: int,
    window_id: str,
    version: str = "v1.0",
) -> Dict[str, Any]:
    """
    Build a canonical payload for selection_set_id derivation.

    Contract note:
    - This is a *suggested payload shape* only.
    - Using it is optional; callers may define a different payload by contract.

    Determinism:
    - Dict keys are sorted when canonical_json() is applied.
    """
    return {
        "type": "selection_set_id",
        "version": version,
        "league_id": league_id,
        "season": season,
        "week_index": week_index,
        "window_id": window_id,
    }


def selection_fingerprint_payload_v1(
    *,
    included_signal_ids: Iterable[str],
    excluded_signal_ids: Iterable[str],
    excluded_reason_codes: Optional[Iterable[str]] = None,
    version: str = "v1.0",
) -> Dict[str, Any]:
    """
    Build a canonical payload for selection_fingerprint derivation.

    Contract note:
    - This is a *suggested payload shape* only.
    - The caller/contract must choose what goes into the fingerprint.

    Determinism:
    - We sort all arrays lexicographically in the payload itself.
    """
    payload: Dict[str, Any] = {
        "type": "selection_fingerprint",
        "version": version,
        "included_signal_ids": sorted(list(included_signal_ids)),
        "excluded_signal_ids": sorted(list(excluded_signal_ids)),
    }
    if excluded_reason_codes is not None:
        payload["excluded_reason_codes"] = sorted(list(excluded_reason_codes))
    return payload


def compute_sha256_hex_from_payload_v1(payload: Dict[str, Any]) -> str:
    """
    Compute sha256(canonical_json(payload)).
    """
    return sha256_of_canonical_json(payload)


__all__ = [
    "selection_set_id_payload_v1",
    "selection_fingerprint_payload_v1",
    "compute_sha256_hex_from_payload_v1",
]
