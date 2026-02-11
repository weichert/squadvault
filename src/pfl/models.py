from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional, Sequence, Tuple

from .enums import PlayStyle, PublicationMode
from .validation import (
    ValidationError,
    require_enum,
    require_int_min,
    require_iterable_max_len,
    require_range_int,
    require_str_max_len,
    require_type,
)


def _sorted_items_int_map(m: Mapping[str, int]) -> Tuple[Tuple[str, int], ...]:
    return tuple(sorted(m.items(), key=lambda kv: kv[0]))


def _sorted_items_trade_arcs(
    m: Mapping[str, Sequence[str]],
) -> Tuple[Tuple[str, Tuple[str, ...]], ...]:
    items = []
    for k, v in m.items():
        items.append((k, tuple(v)))
    return tuple(sorted(items, key=lambda kv: kv[0]))


@dataclass(frozen=True)
class CoachQuote:
    quote_id: str
    text: str
    category: str
    approved_for_broadcast: bool

    def __post_init__(self) -> None:
        require_type("quote_id", self.quote_id, str)
        require_type("text", self.text, str)
        require_type("category", self.category, str)
        require_type("approved_for_broadcast", self.approved_for_broadcast, bool)
        require_str_max_len("text", self.text, 200)


@dataclass(frozen=True)
class LikenessConsent:
    static_image: bool
    ai_avatar: bool
    synthetic_voice: bool
    on_screen_interview_format: bool

    def __post_init__(self) -> None:
        require_type("static_image", self.static_image, bool)
        require_type("ai_avatar", self.ai_avatar, bool)
        require_type("synthetic_voice", self.synthetic_voice, bool)
        require_type("on_screen_interview_format", self.on_screen_interview_format, bool)

        # Constraint: synthetic_voice cannot be True if static_image is False
        if self.synthetic_voice and (not self.static_image):
            raise ValidationError(
                "synthetic_voice cannot be True when static_image is False "
                "(must have at least one visual anchor)"
            )

@dataclass(frozen=True)
class CommissionerSettings:
    """
    Deterministic commissioner-controlled governance knobs.
    Data-only (no editorial logic).
    """
    tone_ceiling: int
    rivalry_aggressiveness: int
    publication_mode: PublicationMode

    def __post_init__(self) -> None:
        require_type("tone_ceiling", self.tone_ceiling, int)
        require_range_int("tone_ceiling", self.tone_ceiling, 0, 10)

        require_type("rivalry_aggressiveness", self.rivalry_aggressiveness, int)
        require_range_int("rivalry_aggressiveness", self.rivalry_aggressiveness, 0, 100)

        require_enum("publication_mode", self.publication_mode, PublicationMode)

@dataclass(frozen=True)
class LoreEntry:
    entry_id: str
    season_reference: Optional[int]
    teams_involved: Tuple[str, ...]
    short_description: str
    approved: bool

    def __post_init__(self) -> None:
        require_type("entry_id", self.entry_id, str)

        if self.season_reference is not None:
            require_type("season_reference", self.season_reference, int)

        require_type("teams_involved", self.teams_involved, tuple)
        for t in self.teams_involved:
            require_type("teams_involved item", t, str)

        require_type("short_description", self.short_description, str)
        require_str_max_len("short_description", self.short_description, 300)

        require_type("approved", self.approved, bool)


@dataclass(frozen=True)
class LeagueLore:
    founding_story: str
    legendary_moments: Tuple[LoreEntry, ...] = field(default_factory=tuple)
    infamous_trades: Tuple[LoreEntry, ...] = field(default_factory=tuple)
    traditions: Tuple[LoreEntry, ...] = field(default_factory=tuple)
    rivalry_flags: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        require_type("founding_story", self.founding_story, str)

        # Enforce tuple immutability deterministically
        object.__setattr__(self, "legendary_moments", tuple(self.legendary_moments))
        object.__setattr__(self, "infamous_trades", tuple(self.infamous_trades))
        object.__setattr__(self, "traditions", tuple(self.traditions))
        object.__setattr__(self, "rivalry_flags", tuple(self.rivalry_flags))

        for name, entries in (
            ("legendary_moments", self.legendary_moments),
            ("infamous_trades", self.infamous_trades),
            ("traditions", self.traditions),
        ):
            for e in entries:
                if not isinstance(e, LoreEntry):
                    raise ValidationError(f"{name} must contain LoreEntry objects")
                # “All lore entries must include approval flag” is guaranteed by the model shape (approved: bool).


@dataclass(frozen=True)
class CoachProfile:
    coach_id: str
    display_name: str
    years_in_league: int
    team_name: str
    team_colors: Tuple[str, ...]
    play_style: PlayStyle
    rivalry_target: Optional[str]
    personality_tag: Optional[str]
    quote_library: Tuple[CoachQuote, ...]
    likeness_consent: LikenessConsent

    def __post_init__(self) -> None:
        require_type("coach_id", self.coach_id, str)
        require_type("display_name", self.display_name, str)
        require_type("years_in_league", self.years_in_league, int)
        require_type("team_name", self.team_name, str)

        require_type("team_colors", self.team_colors, tuple)
        for c in self.team_colors:
            require_type("team_colors item", c, str)

        require_enum("play_style", self.play_style, PlayStyle)

        if self.rivalry_target is not None:
            require_type("rivalry_target", self.rivalry_target, str)
        if self.personality_tag is not None:
            require_type("personality_tag", self.personality_tag, str)

        if not isinstance(self.likeness_consent, LikenessConsent):
            raise ValidationError("likeness_consent must be a LikenessConsent")

        require_type("quote_library", self.quote_library, tuple)
        for q in self.quote_library:
            if not isinstance(q, CoachQuote):
                raise ValidationError("quote_library must contain CoachQuote objects")

        require_int_min("years_in_league", self.years_in_league, 0)
        require_iterable_max_len("team_colors", self.team_colors, 3)
        require_iterable_max_len("quote_library", self.quote_library, 5)

        if self.rivalry_target is not None and self.rivalry_target == self.coach_id:
            raise ValidationError("rivalry_target cannot equal coach_id")


@dataclass(frozen=True)
class SeasonNarrativeState:
    undefeated_teams: Tuple[str, ...]
    streaks_items: Tuple[Tuple[str, int], ...]
    rivalry_heat_index: int
    trade_arcs_items: Tuple[Tuple[str, Tuple[str, ...]], ...]
    pressure_index_items: Tuple[Tuple[str, int], ...]

    @staticmethod
    def from_parts(
        *,
        undefeated_teams: Sequence[str],
        streaks: Mapping[str, int],
        rivalry_heat_index: int,
        trade_arcs: Mapping[str, Sequence[str]],
        pressure_index: Mapping[str, int],
    ) -> "SeasonNarrativeState":
        return SeasonNarrativeState(
            undefeated_teams=tuple(undefeated_teams),
            streaks_items=_sorted_items_int_map(streaks),
            rivalry_heat_index=rivalry_heat_index,
            trade_arcs_items=_sorted_items_trade_arcs(trade_arcs),
            pressure_index_items=_sorted_items_int_map(pressure_index),
        )

    def __post_init__(self) -> None:
        require_type("undefeated_teams", self.undefeated_teams, tuple)
        for t in self.undefeated_teams:
            require_type("undefeated_teams item", t, str)

        require_type("rivalry_heat_index", self.rivalry_heat_index, int)
        require_range_int("rivalry_heat_index", self.rivalry_heat_index, 0, 100)

        require_type("streaks_items", self.streaks_items, tuple)
        for k, v in self.streaks_items:
            require_type("streaks key", k, str)
            require_type("streaks value", v, int)

        require_type("pressure_index_items", self.pressure_index_items, tuple)
        for k, v in self.pressure_index_items:
            require_type("pressure_index key", k, str)
            require_type("pressure_index value", v, int)
            require_range_int("pressure_index value", v, 0, 100)

        require_type("trade_arcs_items", self.trade_arcs_items, tuple)
        for k, arc in self.trade_arcs_items:
            require_type("trade_arcs key", k, str)
            require_type("trade_arcs value", arc, tuple)
            for item in arc:
                require_type("trade_arcs item", item, str)

    @property
    def streaks(self) -> Mapping[str, int]:
        return MappingProxyType(dict(self.streaks_items))

    @property
    def trade_arcs(self) -> Mapping[str, Tuple[str, ...]]:
        return MappingProxyType({k: v for k, v in self.trade_arcs_items})

    @property
    def pressure_index(self) -> Mapping[str, int]:
        return MappingProxyType(dict(self.pressure_index_items))
