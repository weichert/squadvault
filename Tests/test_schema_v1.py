import pytest

from pfl.enums import InputNeed, SegmentType, ShowMode
from pfl.schema import SegmentDefinition, ShowFormatDefinition


def test_segment_definition_rejects_string_enums() -> None:
    with pytest.raises(TypeError):
        SegmentDefinition(  # type: ignore[arg-type]
            segment_type="COLD_OPEN",
            display_name="Cold Open",
            description="Intro segment",
            required_inputs=(InputNeed.COMMISSIONER_SETTINGS,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        )

    with pytest.raises(TypeError):
        SegmentDefinition(  # type: ignore[arg-type]
            segment_type=SegmentType.COLD_OPEN,
            display_name="Cold Open",
            description="Intro segment",
            required_inputs=("COMMISSIONER_SETTINGS",),  # type: ignore[arg-type]
            min_show_mode=None,
            enabled=True,
            version="1.0",
        )


def test_segment_definition_validation() -> None:
    with pytest.raises(ValueError):
        SegmentDefinition(
            segment_type=SegmentType.COLD_OPEN,
            display_name="",
            description="Intro segment",
            required_inputs=(InputNeed.COMMISSIONER_SETTINGS,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        )

    with pytest.raises(ValueError):
        SegmentDefinition(
            segment_type=SegmentType.COLD_OPEN,
            display_name="Cold Open",
            description="x" * 501,
            required_inputs=(InputNeed.COMMISSIONER_SETTINGS,),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        )

    with pytest.raises(ValueError):
        SegmentDefinition(
            segment_type=SegmentType.COLD_OPEN,
            display_name="Cold Open",
            description="Intro segment",
            required_inputs=(
                InputNeed.COMMISSIONER_SETTINGS,
                InputNeed.COMMISSIONER_SETTINGS,
            ),
            min_show_mode=None,
            enabled=True,
            version="1.0",
        )


def test_show_format_definition_validation() -> None:
    ok_seg = SegmentDefinition(
        segment_type=SegmentType.COLD_OPEN,
        display_name="Cold Open",
        description="Intro segment",
        required_inputs=(InputNeed.COMMISSIONER_SETTINGS,),
        min_show_mode=None,
        enabled=True,
        version="1.0",
    )

    with pytest.raises(ValueError):
        ShowFormatDefinition(
            format_id="",
            display_name="Std",
            mode=ShowMode.STANDARD,
            segments_in_order=(SegmentType.COLD_OPEN,),
            segment_overrides=(),
            version="1.0",
        )

    with pytest.raises(ValueError):
        ShowFormatDefinition(
            format_id="std_v1",
            display_name="Std",
            mode=ShowMode.STANDARD,
            segments_in_order=(),
            segment_overrides=(),
            version="1.0",
        )

    with pytest.raises(ValueError):
        ShowFormatDefinition(
            format_id="std_v1",
            display_name="Std",
            mode=ShowMode.STANDARD,
            segments_in_order=tuple([SegmentType.COLD_OPEN] * 13),
            segment_overrides=(),
            version="1.0",
        )

    with pytest.raises(ValueError):
        ShowFormatDefinition(
            format_id="std_v1",
            display_name="Std",
            mode=ShowMode.STANDARD,
            segments_in_order=(SegmentType.COLD_OPEN, SegmentType.COLD_OPEN),
            segment_overrides=(),
            version="1.0",
        )

    with pytest.raises(ValueError):
        ShowFormatDefinition(
            format_id="std_v1",
            display_name="Std",
            mode=ShowMode.STANDARD,
            segments_in_order=(SegmentType.COLD_OPEN,),
            segment_overrides=(
                SegmentDefinition(
                    segment_type=SegmentType.CLOSING_PICKS,
                    display_name="Closing Picks",
                    description="Wrap-up",
                    required_inputs=(),
                    min_show_mode=None,
                    enabled=True,
                    version="1.0",
                ),
            ),
            version="1.0",
        )

    with pytest.raises(ValueError):
        ShowFormatDefinition(
            format_id="std_v1",
            display_name="Std",
            mode=ShowMode.STANDARD,
            segments_in_order=(SegmentType.COLD_OPEN,),
            segment_overrides=(ok_seg, ok_seg),
            version="1.0",
        )


def test_deterministic_equality_and_happy_path_fixture() -> None:
    fmt1 = ShowFormatDefinition(
        format_id="standard_4_v1",
        display_name="Standard (4)",
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
    fmt2 = ShowFormatDefinition(
        format_id="standard_4_v1",
        display_name="Standard (4)",
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
    assert fmt1 == fmt2

    seg1 = SegmentDefinition(
        segment_type=SegmentType.COACH_SPOTLIGHT,
        display_name="Coach Spotlight",
        description="A deterministic coaching vignette slot.",
        required_inputs=(InputNeed.COACH_PROFILES, InputNeed.COMMISSIONER_SETTINGS),
        min_show_mode=None,
        enabled=True,
        version="1.0",
    )
    seg2 = SegmentDefinition(
        segment_type=SegmentType.COACH_SPOTLIGHT,
        display_name="Coach Spotlight",
        description="A deterministic coaching vignette slot.",
        required_inputs=(InputNeed.COACH_PROFILES, InputNeed.COMMISSIONER_SETTINGS),
        min_show_mode=None,
        enabled=True,
        version="1.0",
    )
    assert seg1 == seg2
