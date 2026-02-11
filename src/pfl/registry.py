from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .enums import SegmentType, ShowMode, InputNeed
from .schema import SegmentDefinition, ShowFormatDefinition
from .validation import require_enum_instance, require_tuple


@dataclass(frozen=True, slots=True)
class SegmentRegistry:
    """
    Deterministic, fail-closed registry of canonical SegmentDefinition objects.

    Constraints:
    - Exactly one SegmentDefinition per SegmentType
    - Must include ALL SegmentType enum members
    - Deterministic ordering: stored in SegmentType enum order
    - No coercion: segment types must be SegmentType (not str)
    - Exposes read-only MappingProxyType view
    - Internals are tuple-based
    """
    _definitions: tuple[SegmentDefinition, ...]
    _by_type: Mapping[SegmentType, SegmentDefinition] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        require_tuple("_definitions", self._definitions)

        seen: dict[SegmentType, SegmentDefinition] = {}
        for idx, d in enumerate(self._definitions):
            if not isinstance(d, SegmentDefinition):
                raise TypeError(f"_definitions[{idx}] must be SegmentDefinition")

            require_enum_instance("segment_type", d.segment_type, SegmentType)

            st = d.segment_type
            if st in seen:
                raise ValueError(f"Duplicate SegmentType in registry: {st!r}")
            seen[st] = d

        missing = tuple(st for st in SegmentType if st not in seen)
        if missing:
            raise ValueError(f"Missing SegmentType definitions in registry: {missing!r}")

        ordered = tuple(seen[st] for st in SegmentType)

        object.__setattr__(self, "_definitions", ordered)
        object.__setattr__(
            self,
            "_by_type",
            MappingProxyType({d.segment_type: d for d in ordered}),
        )

    def get(self, segment_type: SegmentType) -> SegmentDefinition:
        require_enum_instance("segment_type", segment_type, SegmentType)
        return self._by_type[segment_type]

    def all_definitions(self) -> tuple[SegmentDefinition, ...]:
        return self._definitions

    def as_mapping(self) -> MappingProxyType[SegmentType, SegmentDefinition]:
        # Already a MappingProxyType, returned as-is.
        return self._by_type  # type: ignore[return-value]


# ----------------------------
# Canonical Segment Definitions (v1.0)
# ----------------------------

def _canonical_segment_definitions_v1() -> tuple[SegmentDefinition, ...]:
    """
    Canonical deterministic definitions for all SegmentType enum members.
    Declarative only. No logic.
    """

    return (
        SegmentDefinition(
            segment_type=SegmentType.COLD_OPEN,
            display_name="Cold Open",
            description="Opening segment that establishes context and tone before structured coverage begins.",
            required_inputs=(InputNeed.SEASON_NARRATIVE_STATE,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.HEADLINE_MATCHUP,
            display_name="Headline Matchup",
            description="Primary featured matchup segment framing stakes and competitive tension.",
            required_inputs=(InputNeed.SEASON_NARRATIVE_STATE,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.COACH_SPOTLIGHT,
            display_name="Coach Spotlight",
            description="Focused segment highlighting a coach profile or defining coaching decision.",
            required_inputs=(InputNeed.COACH_PROFILES,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.PRESSURE_METER,
            display_name="Pressure Meter",
            description="Evaluates competitive pressure and situational intensity entering the week.",
            required_inputs=(InputNeed.SEASON_NARRATIVE_STATE,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.RIVALRY_HEAT_CHECK,
            display_name="Rivalry Heat Check",
            description="Examines rivalry dynamics and historical emotional stakes.",
            required_inputs=(InputNeed.LEAGUE_LORE,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.TRADE_DESK,
            display_name="Trade Desk",
            description="Segment reviewing trades, roster shifts, and commissioner implications.",
            required_inputs=(InputNeed.COMMISSIONER_SETTINGS,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.FLASHBACK,
            display_name="Flashback",
            description="Historical callback segment referencing prior league events.",
            required_inputs=(InputNeed.LEAGUE_LORE,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
        SegmentDefinition(
            segment_type=SegmentType.CLOSING_PICKS,
            display_name="Closing Picks",
            description="Final segment delivering concise closing predictions or calls.",
            required_inputs=(InputNeed.SEASON_NARRATIVE_STATE,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        ),
    )


CANONICAL_SEGMENT_REGISTRY_V1: SegmentRegistry = SegmentRegistry(_canonical_segment_definitions_v1())


# ----------------------------
# Show Format Catalog (STATIC)
# ----------------------------

STANDARD_SHOW_V1: ShowFormatDefinition = ShowFormatDefinition(
    format_id="standard_v1",
    display_name="Standard Show (v1)",
    mode=ShowMode.STANDARD,
    segments_in_order=(
        SegmentType.COLD_OPEN,
        SegmentType.HEADLINE_MATCHUP,
        SegmentType.COACH_SPOTLIGHT,
        SegmentType.CLOSING_PICKS,
    ),
    segment_overrides=(),
    version="1.0",
)


def validate_show_format_catalog(registry: SegmentRegistry, show_format: ShowFormatDefinition) -> None:
    """
    Phase 3 validation: registry + catalog consistency.

    - segments_in_order values must be SegmentType (schema enforces, but we re-check fail-closed)
    - all referenced segments must exist in registry
    """
    if not isinstance(show_format, ShowFormatDefinition):
        raise TypeError("show_format must be ShowFormatDefinition")

    for idx, st in enumerate(show_format.segments_in_order):
        require_enum_instance(f"segments_in_order[{idx}]", st, SegmentType)
        registry.get(st)
