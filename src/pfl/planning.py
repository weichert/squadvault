from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from pfl.schema import SegmentDefinition, ShowFormatDefinition
from pfl.enums import SegmentType, ShowMode


@dataclass(frozen=True)
class ShowPlan:
    format_id: str
    version: str
    mode: ShowMode
    segments: Tuple[SegmentDefinition, ...]


def _is_mapping_like(obj: Any) -> bool:
    return hasattr(obj, "__getitem__") and hasattr(obj, "keys")

def _typecheck_overrides(overrides: Any) -> Mapping[SegmentType, SegmentDefinition]:
    """
    Acceptable shapes (fail-closed):
      - None -> empty
      - mapping-like[SegmentType, SegmentDefinition]
      - tuple/list of SegmentDefinition (each provides .segment_type)
    Returns a Mapping[SegmentType, SegmentDefinition] (as MappingProxyType).
    """
    if overrides is None:
        return MappingProxyType({})

    # schema default is (), so treat empty tuple as "no overrides"
    if overrides == ():
        return MappingProxyType({})

    if _is_mapping_like(overrides):
        for k in overrides.keys():
            if not isinstance(k, SegmentType):
                raise TypeError(f"override key must be SegmentType, got {type(k)!r}")
            v = overrides[k]
            if not isinstance(v, SegmentDefinition):
                raise TypeError(f"override value must be SegmentDefinition, got {type(v)!r}")
        return overrides  # type: ignore[return-value]

    # tuple/list of SegmentDefinition
    if isinstance(overrides, (tuple, list)):
        tmp: dict[SegmentType, SegmentDefinition] = {}
        for item in overrides:
            if not isinstance(item, SegmentDefinition):
                raise TypeError(f"segment_overrides entries must be SegmentDefinition, got {type(item)!r}")
            st = getattr(item, "segment_type", None)
            if not isinstance(st, SegmentType):
                raise TypeError(f"override SegmentDefinition.segment_type must be SegmentType, got {type(st)!r}")
            if st in tmp:
                raise ValueError(f"duplicate override for SegmentType: {st!r}")
            tmp[st] = item
        return MappingProxyType(tmp)

    raise TypeError(
        f"segment_overrides must be mapping-like or tuple/list[SegmentDefinition], got {type(overrides)!r}"
    )


def _registry_to_map(registry: Any) -> Mapping[SegmentType, SegmentDefinition]:
    """
    Adapter:
      - If registry is mapping-like: validate key/value types and use it directly.
      - Else if it looks like pfl.registry.SegmentRegistry (has _definitions): build a local map.
    """
    if _is_mapping_like(registry):
        for k in registry.keys():
            if not isinstance(k, SegmentType):
                raise TypeError(f"registry key must be SegmentType, got {type(k)!r}")
            v = registry[k]
            if not isinstance(v, SegmentDefinition):
                raise TypeError(f"registry value must be SegmentDefinition, got {type(v)!r}")
        return registry  # type: ignore[return-value]

    defs = getattr(registry, "_definitions", None)
    if isinstance(defs, tuple):
        tmp: dict[SegmentType, SegmentDefinition] = {}
        for d in defs:
            if not isinstance(d, SegmentDefinition):
                raise TypeError(f"registry _definitions must contain SegmentDefinition, got {type(d)!r}")
            st = getattr(d, "segment_type", None)
            if not isinstance(st, SegmentType):
                raise TypeError(f"SegmentDefinition.segment_type must be SegmentType, got {type(st)!r}")
            if st in tmp:
                raise ValueError(f"duplicate SegmentType in registry: {st!r}")
            tmp[st] = d
        return MappingProxyType(tmp)

    raise TypeError(
        f"registry must be mapping-like or SegmentRegistry(_definitions=...), got {type(registry)!r}"
    )


def resolve_show_plan(show_format: Any, registry: Any) -> ShowPlan:
    """
    Deterministic resolver:
      - start from show_format.segments_in_order (tuple[SegmentType,...])
      - for each SegmentType, pull SegmentDefinition from registry
      - apply show_format.segment_overrides[segment_type] if present (override replaces canonical)
    """
    if not isinstance(show_format, ShowFormatDefinition):
        raise TypeError(f"show_format must be ShowFormatDefinition, got {type(show_format)!r}")

    reg = _registry_to_map(registry)
    overrides = _typecheck_overrides(getattr(show_format, "segment_overrides", None))

    segments_in_order = getattr(show_format, "segments_in_order", None)
    if not isinstance(segments_in_order, tuple):
        raise TypeError(
            f"show_format.segments_in_order must be tuple[SegmentType, ...], got {type(segments_in_order)!r}"
        )

    resolved: list[SegmentDefinition] = []

    for st in segments_in_order:
        if not isinstance(st, SegmentType):
            raise TypeError(f"segments_in_order entries must be SegmentType, got {type(st)!r}")

        seg = overrides.get(st)
        if seg is None:
            seg = reg[st]  # KeyError if missing is correct + deterministic

        resolved.append(seg)

    return ShowPlan(
        format_id=getattr(show_format, "format_id"),
        version=getattr(show_format, "version"),
        mode=getattr(show_format, "mode"),
        segments=tuple(resolved),
    )

