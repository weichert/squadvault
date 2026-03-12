"""Editorial Attunement Layer v1 (EAL)

Contract:
- Restraint-only: may constrain expression, never alters selection, ordering, or facts.
- Metadata-only: must not inspect signal bodies or narrative content.
- Deterministic: same inputs -> same outputs.
- Window-scoped: no state, no accumulation.

Outputs are stable directive strings intended to guide downstream drafting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Stable directive strings (do not change without a version bump)
EAL_HIGH_CONFIDENCE_ALLOWED = "HIGH_CONFIDENCE_ALLOWED"
EAL_MODERATE_CONFIDENCE_ONLY = "MODERATE_CONFIDENCE_ONLY"
EAL_LOW_CONFIDENCE_RESTRAINT = "LOW_CONFIDENCE_RESTRAINT"
EAL_AMBIGUITY_PREFER_SILENCE = "AMBIGUITY_PREFER_SILENCE"


@dataclass(frozen=True)
class EALMeta:
    """Metadata-only inputs. Do not add fields that contain content."""
    has_selection_set: bool
    has_window: bool
    included_count: Optional[int] = None
    excluded_count: Optional[int] = None


def evaluate_editorial_attunement_v1(meta: EALMeta) -> str:
    """Return an EAL directive based only on metadata.

    This function must remain deterministic and restraint-only.
    """
    if not meta.has_window or not meta.has_selection_set:
        return EAL_AMBIGUITY_PREFER_SILENCE

    n = meta.included_count
    if n is None:
        # Unknown selection strength => prefer restraint, but not necessarily silence
        return EAL_LOW_CONFIDENCE_RESTRAINT

    if n <= 0:
        return EAL_AMBIGUITY_PREFER_SILENCE
    if n <= 2:
        return EAL_LOW_CONFIDENCE_RESTRAINT

    # Conservative default. Reserve HIGH_CONFIDENCE for explicit, deterministic completeness markers.
    return EAL_MODERATE_CONFIDENCE_ONLY
