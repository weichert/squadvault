import pytest

from pfl.enums import PlayStyle, PublicationMode
from pfl.models import (
    CommissionerSettings,
    CoachProfile,
    CoachQuote,
    LikenessConsent,
    SeasonNarrativeState,
)
from pfl.validation import ValidationError


def test_overlong_quote_fails() -> None:
    with pytest.raises(ValidationError):
        CoachQuote(
            quote_id="q1",
            text="x" * 201,
            category="HYPE",
            approved_for_broadcast=True,
        )


def test_invalid_enum_fails() -> None:
    consent = LikenessConsent(
        static_image=True,
        ai_avatar=False,
        synthetic_voice=False,
        on_screen_interview_format=False,
    )
    q = CoachQuote(
        quote_id="q1",
        text="No excuses.",
        category="GENERAL",
        approved_for_broadcast=True,
    )
    with pytest.raises(ValidationError):
        CoachProfile(  # type: ignore[arg-type]
            coach_id="c1",
            display_name="Coach One",
            years_in_league=1,
            team_name="Sharks",
            team_colors=("blue",),
            play_style="BALANCED",  # must be PlayStyle enum
            rivalry_target=None,
            personality_tag=None,
            quote_library=(q,),
            likeness_consent=consent,
        )


def test_rivalry_self_reference_fails() -> None:
    consent = LikenessConsent(
        static_image=True,
        ai_avatar=False,
        synthetic_voice=True,
        on_screen_interview_format=False,
    )
    q = CoachQuote(
        quote_id="q1",
        text="Keep it simple.",
        category="GENERAL",
        approved_for_broadcast=True,
    )
    with pytest.raises(ValidationError):
        CoachProfile(
            coach_id="c1",
            display_name="Coach One",
            years_in_league=3,
            team_name="Sharks",
            team_colors=("blue", "white"),
            play_style=PlayStyle.BALANCED,
            rivalry_target="c1",
            personality_tag=None,
            quote_library=(q,),
            likeness_consent=consent,
        )


def test_likeness_consent_requires_visual_anchor() -> None:
    with pytest.raises(ValidationError):
        LikenessConsent(
            static_image=False,
            ai_avatar=False,
            synthetic_voice=True,
            on_screen_interview_format=False,
        )


def test_invalid_rivalry_heat_index_fails() -> None:
    with pytest.raises(ValidationError):
        SeasonNarrativeState.from_parts(
            undefeated_teams=["A"],
            streaks={"A": 3},
            rivalry_heat_index=101,
            trade_arcs={"A": ["trade1"]},
            pressure_index={"A": 50},
        )


def test_pressure_index_range_fails() -> None:
    with pytest.raises(ValidationError):
        SeasonNarrativeState.from_parts(
            undefeated_teams=["A"],
            streaks={"A": 3},
            rivalry_heat_index=50,
            trade_arcs={"A": ["trade1"]},
            pressure_index={"A": 101},
        )


def test_deterministic_equality_same_inputs_equal() -> None:
    s1 = SeasonNarrativeState.from_parts(
        undefeated_teams=["A", "B"],
        streaks={"A": 2, "B": 1},
        rivalry_heat_index=42,
        trade_arcs={"A": ["t1", "t2"], "B": []},
        pressure_index={"A": 10, "B": 20},
    )
    s2 = SeasonNarrativeState.from_parts(
        undefeated_teams=["A", "B"],
        streaks={"B": 1, "A": 2},  # different insertion order
        rivalry_heat_index=42,
        trade_arcs={"B": [], "A": ["t1", "t2"]},  # different insertion order
        pressure_index={"B": 20, "A": 10},  # different insertion order
    )
    assert s1 == s2


def test_commissioner_tone_ceiling_range_fails() -> None:
    with pytest.raises(ValidationError):
        CommissionerSettings(
            tone_ceiling=11,
            rivalry_aggressiveness=50,
            publication_mode=PublicationMode.AUTO,
        )

def test_commissioner_rivalry_aggressiveness_range_fails() -> None:
    with pytest.raises(ValidationError):
        CommissionerSettings(
            tone_ceiling=7,
            rivalry_aggressiveness=101,
            publication_mode=PublicationMode.AUTO,
        )


def test_commissioner_publication_mode_invalid_enum_fails() -> None:
    with pytest.raises(ValidationError):
        CommissionerSettings(  # type: ignore[arg-type]
            tone_ceiling=7,
            rivalry_aggressiveness=50,
            publication_mode="AUTO",  # must be PublicationMode enum
        )


def test_commissioner_deterministic_equality() -> None:
    a = CommissionerSettings(
        tone_ceiling=7,
        rivalry_aggressiveness=50,
        publication_mode=PublicationMode.REVIEW_REQUIRED,
    )
    b = CommissionerSettings(
        tone_ceiling=7,
        rivalry_aggressiveness=50,
        publication_mode=PublicationMode.REVIEW_REQUIRED,
    )
    assert a == b
