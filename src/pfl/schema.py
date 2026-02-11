from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional

from .enums import InputNeed, SegmentType, ShowMode
from .validation import (
    require_enum_instance,
    require_max_len,
    require_non_empty_str,
    require_optional_enum_instance,
    require_tuple,
    require_unique_items,
)


@dataclass(frozen=True, slots=True)
class SegmentDefinition:
    segment_type: SegmentType
    display_name: str
    description: str
    required_inputs: tuple[InputNeed, ...]
    min_show_mode: Optional[ShowMode]
    enabled: bool
    version: str

    def __post_init__(self) -> None:
        require_enum_instance("segment_type", self.segment_type, SegmentType)
        require_non_empty_str("display_name", self.display_name)
        require_non_empty_str("description", self.description)
        require_max_len("description", self.description, 500)

        require_tuple("required_inputs", self.required_inputs)
        for idx, need in enumerate(self.required_inputs):
            require_enum_instance(f"required_inputs[{idx}]", need, InputNeed)
        require_unique_items("required_inputs", self.required_inputs)

        require_optional_enum_instance("min_show_mode", self.min_show_mode, ShowMode)

        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool")

        require_non_empty_str("version", self.version)


@dataclass(frozen=True, slots=True)
class ShowFormatDefinition:
    format_id: str
    display_name: str
    mode: ShowMode
    segments_in_order: tuple[SegmentType, ...]
    segment_overrides: tuple[SegmentDefinition, ...]
    version: str

    def __post_init__(self) -> None:
        require_non_empty_str("format_id", self.format_id)
        require_non_empty_str("display_name", self.display_name)
        require_enum_instance("mode", self.mode, ShowMode)

        require_tuple("segments_in_order", self.segments_in_order)
        if not (1 <= len(self.segments_in_order) <= 12):
            raise ValueError("segments_in_order length must be between 1 and 12")
        for idx, st in enumerate(self.segments_in_order):
            require_enum_instance(f"segments_in_order[{idx}]", st, SegmentType)
        require_unique_items("segments_in_order", self.segments_in_order)

        require_tuple("segment_overrides", self.segment_overrides)
        for idx, ov in enumerate(self.segment_overrides):
            if not isinstance(ov, SegmentDefinition):
                raise TypeError(f"segment_overrides[{idx}] must be SegmentDefinition")

        override_types = tuple(ov.segment_type for ov in self.segment_overrides)
        require_unique_items("segment_overrides.segment_type", override_types)

        segments_set = set(self.segments_in_order)
        for ov in self.segment_overrides:
            if ov.segment_type not in segments_set:
                raise ValueError(
                    "segment_overrides contains segment_type not present in segments_in_order"
                )

        require_non_empty_str("version", self.version)

    def overrides_by_type(self) -> MappingProxyType[SegmentType, SegmentDefinition]:
        d = {ov.segment_type: ov for ov in self.segment_overrides}
        return MappingProxyType(d)
