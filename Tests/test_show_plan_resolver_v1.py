from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from pfl.enums import SegmentType
from pfl.planning import resolve_show_plan
from pfl.registry import CANONICAL_SEGMENT_REGISTRY_V1, STANDARD_SHOW_V1
from pfl.schema import SegmentDefinition, ShowFormatDefinition


def _make_modified_segment(seg: SegmentDefinition) -> SegmentDefinition:
    """
    Deterministically create a different SegmentDefinition without knowing field names.
    Assumes SegmentDefinition is a dataclass (per your Phase 1/2).
    """
    if not dataclasses.is_dataclass(seg):
        raise RuntimeError("SegmentDefinition is expected to be a dataclass for this test helper.")

    fields = dataclasses.fields(seg)
    kwargs = {f.name: getattr(seg, f.name) for f in fields}

    # deterministically modify the first str field (if any)
    for f in fields:
        v = kwargs.get(f.name)
        if isinstance(v, str):
            kwargs[f.name] = v + "__override"
            return seg.__class__(**kwargs)

    # fallback: deterministically modify the first tuple field (if any)
    for f in fields:
        v = kwargs.get(f.name)
        if isinstance(v, tuple):
            kwargs[f.name] = v + v[:0]
            return seg.__class__(**kwargs)

    raise RuntimeError("Could not deterministically modify a SegmentDefinition for override testing.")


def _make_format_with_override(
    base: ShowFormatDefinition,
    st: SegmentType,
    override_seg: SegmentDefinition,
) -> ShowFormatDefinition:
    if not dataclasses.is_dataclass(base):
        raise RuntimeError("ShowFormatDefinition is expected to be a dataclass for this test helper.")

    fields = dataclasses.fields(base)
    kwargs = {f.name: getattr(base, f.name) for f in fields}

    existing = getattr(base, "segment_overrides", None)
    if existing is None:
        existing_t = ()
    elif isinstance(existing, tuple):
        existing_t = existing
    elif isinstance(existing, list):
        existing_t = tuple(existing)
    else:
        # If someone switches schema later, keep fail-closed.
        raise TypeError(f"unexpected segment_overrides type in schema: {type(existing)!r}")

    # remove any prior override for this segment_type, then add ours
    filtered = tuple(o for o in existing_t if getattr(o, "segment_type", None) != st)
    kwargs["segment_overrides"] = filtered + (override_seg,)

    return base.__class__(**kwargs)


def test_resolve_show_plan_deterministic_repeated_equals():
    p1 = resolve_show_plan(STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1)
    p2 = resolve_show_plan(STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1)
    assert p1 == p2


def test_resolve_show_plan_override_replaces_canonical_for_segment_type():
    # baseline plan gives us the canonical segment at position 0
    baseline = resolve_show_plan(STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1)

    st = STANDARD_SHOW_V1.segments_in_order[0]
    assert isinstance(st, SegmentType)

    canonical = baseline.segments[0]
    override = _make_modified_segment(canonical)
    assert override != canonical

    fmt = _make_format_with_override(STANDARD_SHOW_V1, st, override)
    plan = resolve_show_plan(fmt, CANONICAL_SEGMENT_REGISTRY_V1)

    assert plan.segments[0] is override


def test_resolve_show_plan_fail_closed_on_wrong_types():
    with pytest.raises(TypeError):
        resolve_show_plan("STANDARD_SHOW_V1", CANONICAL_SEGMENT_REGISTRY_V1)

    with pytest.raises(TypeError):
        resolve_show_plan(STANDARD_SHOW_V1, "CANONICAL_SEGMENT_REGISTRY_V1")

    with pytest.raises(TypeError):
        resolve_show_plan(STANDARD_SHOW_V1, MappingProxyType({"not_an_enum": object()}))


def test_resolver_only_references_registered_segment_types():
    # If any referenced SegmentType is not registered, resolver should KeyError deterministically.
    # This test asserts it does NOT raise for the canonical format+registry pair.
    resolve_show_plan(STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1)
