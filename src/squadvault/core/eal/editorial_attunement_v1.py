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
    included_count: int | None = None
    excluded_count: int | None = None
    is_playoff: bool = False


def evaluate_editorial_attunement_v1(meta: EALMeta) -> str:
    """Return an EAL directive based only on metadata.

    This function must remain deterministic and restraint-only.

    Playoff weeks have fewer canonical events by design (fewer matchups).
    When is_playoff is True and at least 1 event is included, the floor
    is MODERATE_CONFIDENCE_ONLY rather than LOW_CONFIDENCE_RESTRAINT.
    This prevents championship recaps from being unnecessarily restrained.
    """
    if not meta.has_window or not meta.has_selection_set:
        return EAL_AMBIGUITY_PREFER_SILENCE

    n = meta.included_count
    if n is None:
        return EAL_LOW_CONFIDENCE_RESTRAINT

    if n <= 0:
        return EAL_AMBIGUITY_PREFER_SILENCE

    # Playoff floor: at least MODERATE when any events exist
    if meta.is_playoff:
        if n >= 8:
            return EAL_HIGH_CONFIDENCE_ALLOWED
        return EAL_MODERATE_CONFIDENCE_ONLY

    if n <= 2:
        return EAL_LOW_CONFIDENCE_RESTRAINT
    if n >= 8:
        return EAL_HIGH_CONFIDENCE_ALLOWED

    return EAL_MODERATE_CONFIDENCE_ONLY
