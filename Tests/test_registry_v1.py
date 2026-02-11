import pytest

from pfl.enums import SegmentType, InputNeed
from pfl.registry import (
    SegmentRegistry,
    CANONICAL_SEGMENT_REGISTRY_V1,
    STANDARD_SHOW_V1,
    validate_show_format_catalog,
)
from pfl.schema import SegmentDefinition


def _mk_def(st: SegmentType) -> SegmentDefinition:
    empty_inputs: tuple[InputNeed, ...] = ()
    return SegmentDefinition(
        segment_type=st,
        display_name=f"{st.name}",
        description="x",
        required_inputs=empty_inputs,
        min_show_mode=None,
        enabled=True,
        version="1.0",
    )


def test_registry_rejects_duplicate_segment_type() -> None:
    defs = tuple(_mk_def(st) for st in SegmentType)
    dup = defs + (defs[0],)
    with pytest.raises(ValueError, match="Duplicate SegmentType"):
        SegmentRegistry(dup)


def test_registry_rejects_missing_segment_type() -> None:
    defs = tuple(_mk_def(st) for st in SegmentType)
    if len(defs) < 1:
        pytest.skip("SegmentType enum unexpectedly empty")
    missing_one = defs[:-1]
    with pytest.raises(ValueError, match="Missing SegmentType"):
        SegmentRegistry(missing_one)


def test_lookup_works() -> None:
    for st in SegmentType:
        d = CANONICAL_SEGMENT_REGISTRY_V1.get(st)
        assert d.segment_type is st


def test_lookup_invalid_type_raises_typeerror() -> None:
    # Fail-closed: registry does not accept strings or other types.
    with pytest.raises(TypeError):
        CANONICAL_SEGMENT_REGISTRY_V1.get("COLD_OPEN")  # type: ignore[arg-type]


def test_mapping_invalid_key_raises_keyerror() -> None:
    mp = CANONICAL_SEGMENT_REGISTRY_V1.as_mapping()
    with pytest.raises(KeyError):
        mp[object()]  # type: ignore[index]


def test_registry_is_deterministic_equal_for_identical_construction() -> None:
    defs_a = tuple(_mk_def(st) for st in SegmentType)
    defs_b = tuple(_mk_def(st) for st in SegmentType)
    ra = SegmentRegistry(defs_a)
    rb = SegmentRegistry(defs_b)
    assert ra == rb
    assert ra.all_definitions() == rb.all_definitions()


def test_standard_show_v1_validates() -> None:
    validate_show_format_catalog(CANONICAL_SEGMENT_REGISTRY_V1, STANDARD_SHOW_V1)


def test_standard_show_v1_references_only_registered_segments() -> None:
    reg_map = CANONICAL_SEGMENT_REGISTRY_V1.as_mapping()
    for st in STANDARD_SHOW_V1.segments_in_order:
        assert st in reg_map

