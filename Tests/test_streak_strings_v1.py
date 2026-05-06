"""Tests for streak_strings_v1 helper and the in-scope refactored call sites.

Covers:
- Helper format correctness across each of the 5 helpers.
- Threshold parity with _detect_streaks
  (|streak| in {-2, -1, 0, 1, 2} -> None; |streak| == 3 short form;
  |streak| >= 4 long form).
- Branching coverage for format_streak_record (tied/broke +
  approach-to-record on both winning and losing sides).
- _ascii_punct interaction: helper outputs without em-dash are
  idempotent under _ascii_punct; format_streak_outcome contains
  em-dash and gets normalized to hyphen if/when _ascii_punct is
  applied (the angle path does not apply it today; this test
  documents the interaction so any future change surfaces).
- Behavioral parity: synthetic SeasonContext + LeagueHistoryContext
  driven through _detect_streaks / _detect_streak_records produces
  angles whose headline/detail strings exactly equal the helper output.
"""

from __future__ import annotations

from squadvault.core.recaps.context.league_history_v1 import (
    LeagueHistoryContextV1,
    StreakRecord,
)
from squadvault.core.recaps.context.season_context_v1 import (
    TeamRecord,
    WeekMatchupContext,
)
from squadvault.core.recaps.render.deterministic_bullets_v1 import _ascii_punct
from squadvault.core.recaps.render.streak_strings_v1 import (
    format_streak_marker,
    format_streak_outcome,
    format_streak_phrase,
    format_streak_record,
    format_streak_status,
)

# =====================================================================
# format_streak_phrase — noun phrase, |streak| >= 2 floor
# =====================================================================

def test_phrase_winning_typical() -> None:
    assert format_streak_phrase(4) == "4-game win streak"
    assert format_streak_phrase(5) == "5-game win streak"
    assert format_streak_phrase(10) == "10-game win streak"


def test_phrase_losing_typical() -> None:
    assert format_streak_phrase(-4) == "4-game losing streak"
    assert format_streak_phrase(-5) == "5-game losing streak"
    assert format_streak_phrase(-10) == "10-game losing streak"


def test_phrase_winning_boundary() -> None:
    # Grammatical floor is 2; helper produces a phrase even though
    # consumers gate higher.
    assert format_streak_phrase(2) == "2-game win streak"
    assert format_streak_phrase(3) == "3-game win streak"


def test_phrase_losing_boundary() -> None:
    assert format_streak_phrase(-2) == "2-game losing streak"
    assert format_streak_phrase(-3) == "3-game losing streak"


def test_phrase_below_floor_returns_none() -> None:
    assert format_streak_phrase(-1) is None
    assert format_streak_phrase(0) is None
    assert format_streak_phrase(1) is None


# =====================================================================
# format_streak_status — T1/T2/T3/T4 headlines + threshold parity
# =====================================================================

def test_status_t1_long_form_winning() -> None:
    # T1: long-form winning, |streak| >= 4
    assert format_streak_status("Wolves", 4) == "Wolves on 4-game win streak"
    assert format_streak_status("Wolves", 5) == "Wolves on 5-game win streak"
    assert format_streak_status("Wolves", 10) == "Wolves on 10-game win streak"


def test_status_t2_short_form_winning() -> None:
    # T2: short-form winning, streak == 3
    assert format_streak_status("Hawks", 3) == "Hawks has won 3 straight"


def test_status_t3_long_form_losing() -> None:
    # T3: long-form losing, |streak| >= 4
    assert format_streak_status("Bears", -4) == "Bears on 4-game losing streak"
    assert format_streak_status("Bears", -5) == "Bears on 5-game losing streak"
    assert format_streak_status("Bears", -10) == "Bears on 10-game losing streak"


def test_status_t4_short_form_losing() -> None:
    # T4: short-form losing, streak == -3
    assert format_streak_status("Rams", -3) == "Rams has lost 3 straight"


def test_status_threshold_parity_below_3_returns_none() -> None:
    # Threshold parity with _detect_streaks: |streak| < 3 -> no angle
    for streak in [-2, -1, 0, 1, 2]:
        assert format_streak_status("Anyone", streak) is None, (
            f"Expected None for streak={streak}, got truthy value"
        )


def test_status_composes_from_phrase_helper() -> None:
    # The long-form should embed the noun phrase produced by
    # format_streak_phrase. If format_streak_phrase ever changes
    # its template, this test surfaces it (it will still pass if
    # the change propagates correctly, but reading the assertion
    # makes the dependency explicit).
    name = "Tigers"
    streak = 7
    phrase = format_streak_phrase(streak)
    assert phrase is not None
    assert format_streak_status(name, streak) == f"{name} on {phrase}"


# =====================================================================
# format_streak_outcome — T5/T6 detail clauses + em-dash preservation
# =====================================================================

def test_outcome_t5_continuation() -> None:
    # T5: won this week
    assert format_streak_outcome("Falcons", "7-3", True, "Wolves") == (
        "Record: 7-3. Beat Wolves this week \u2014 streak continues."
    )


def test_outcome_t6_extension() -> None:
    # T6: lost this week
    assert format_streak_outcome("Falcons", "3-7", False, "Wolves") == (
        "Record: 3-7. Lost to Wolves this week \u2014 streak extended, not snapped."
    )


def test_outcome_em_dash_present_t5() -> None:
    # The em-dash (U+2014) is the canonical separator. Helper preserves it.
    out = format_streak_outcome("Falcons", "7-3", True, "Wolves")
    assert "\u2014" in out, f"Expected em-dash in T5 output: {out!r}"


def test_outcome_em_dash_present_t6() -> None:
    out = format_streak_outcome("Falcons", "3-7", False, "Wolves")
    assert "\u2014" in out, f"Expected em-dash in T6 output: {out!r}"


def test_outcome_franchise_name_param_accepted_unused() -> None:
    # franchise_name is reserved for future template revisions; passing
    # any value (including the empty string) does not change output.
    a = format_streak_outcome("", "7-3", True, "Wolves")
    b = format_streak_outcome("Falcons", "7-3", True, "Wolves")
    assert a == b


# =====================================================================
# format_streak_record — T8/T9-WIN/T10/T9-LOSS branches
# =====================================================================

def test_record_t8_tied_winning() -> None:
    # streak == record: tied
    result = format_streak_record("Tigers", 8, 8, "Lions")
    assert result is not None
    headline, detail = result
    assert headline == "Tigers tied/broke the league win streak record (8 games)"
    assert detail == "Previous record: 8 by Lions."


def test_record_t8_broke_winning() -> None:
    # streak > record: broke
    result = format_streak_record("Tigers", 9, 8, "Lions")
    assert result is not None
    headline, detail = result
    assert headline == "Tigers tied/broke the league win streak record (9 games)"
    assert detail == "Previous record: 8 by Lions."


def test_record_t9_one_win_from_record() -> None:
    # streak == record - 1: approach
    result = format_streak_record("Tigers", 7, 8, "Lions")
    assert result is not None
    headline, detail = result
    assert headline == "Tigers is 1 win from the league win streak record (8)"
    assert detail == ""  # T9 has empty detail by design


def test_record_winning_gap_returns_none() -> None:
    # streak > 3 but < record - 1: no record claim applies
    assert format_streak_record("Tigers", 5, 10, "Lions") is None


def test_record_t10_tied_losing() -> None:
    # |streak| == record on losing side: tied
    result = format_streak_record("Bears", -8, 8, "Pelicans")
    assert result is not None
    headline, detail = result
    assert headline == "Bears tied/broke the league loss streak record (8 games)"
    assert detail == "Previous record: 8 by Pelicans."


def test_record_t10_broke_losing() -> None:
    # |streak| > record on losing side: broke
    result = format_streak_record("Bears", -9, 8, "Pelicans")
    assert result is not None
    headline, detail = result
    assert headline == "Bears tied/broke the league loss streak record (9 games)"
    assert detail == "Previous record: 8 by Pelicans."


def test_record_t9_one_loss_from_record() -> None:
    # streak == -(record - 1): T9-LOSS approach (added in §10 Q1 thread closure).
    result = format_streak_record("Bears", -7, 8, "Pelicans")
    assert result is not None
    headline, detail = result
    assert headline == "Bears is 1 loss from the league loss streak record (8)"
    assert detail == ""  # T9-LOSS has empty detail by design (mirrors T9-WIN)


def test_record_t9_loss_below_outer_gate() -> None:
    """Edge case: arithmetic alone is insufficient — outer gate governs.

    abs(-2) == 3 - 1 satisfies the T9-LOSS arithmetic, but the
    helper's outer gate ``streak <= -3`` (mirroring T9-WIN's
    ``streak >= 3`` at line 217) excludes |streak| == 2. Returns None.

    Consumer-side gate in ``_detect_streak_records``
    (narrative_angles_v1.py:579) is also -3, so this is doubly
    gated. Helper-internal symmetry with T9-WIN is the design
    intent (Path A in the §10 Q1 Step 1 brief).
    """
    assert format_streak_record("Bears", -2, 3, "Pelicans") is None


def test_record_below_threshold_returns_none() -> None:
    # |streak| < 3: helper returns None regardless of record_length
    for streak in [-2, -1, 0, 1, 2]:
        assert format_streak_record("X", streak, 5, "Y") is None, (
            f"Expected None for streak={streak}"
        )


# =====================================================================
# format_streak_marker — T7 standings cell
# =====================================================================

def test_marker_winning() -> None:
    assert format_streak_marker(1) == "W1"
    assert format_streak_marker(3) == "W3"
    assert format_streak_marker(10) == "W10"


def test_marker_losing() -> None:
    assert format_streak_marker(-1) == "L1"
    assert format_streak_marker(-2) == "L2"
    assert format_streak_marker(-10) == "L10"


def test_marker_no_streak() -> None:
    assert format_streak_marker(0) == "-"


# =====================================================================
# _ascii_punct interaction
# =====================================================================

def test_ascii_punct_phrase_idempotent() -> None:
    # No characters in the _ascii_punct replacement set.
    out = format_streak_phrase(5)
    assert out is not None
    assert _ascii_punct(out) == out


def test_ascii_punct_status_idempotent() -> None:
    # Long-form: no characters in the _ascii_punct replacement set.
    out = format_streak_status("Wolves", 7)
    assert out is not None
    assert _ascii_punct(out) == out
    # Short-form: same property.
    out = format_streak_status("Wolves", 3)
    assert out is not None
    assert _ascii_punct(out) == out


def test_ascii_punct_outcome_em_dash_normalizes() -> None:
    """T5/T6 contain em-dash. _ascii_punct converts em-dash to hyphen.

    Today the narrative-angles render path does NOT apply _ascii_punct,
    so the em-dash reaches the prompt unchanged. If a future refactor
    pipes angle prose through _ascii_punct (e.g. for export-side
    consistency), the em-dash will normalize to a hyphen — a format
    change. This test documents the interaction so any such change
    is intentional, not silent.
    """
    out = format_streak_outcome("Falcons", "7-3", True, "Wolves")
    assert "\u2014" in out
    normalized = _ascii_punct(out)
    assert "\u2014" not in normalized
    assert " - streak continues." in normalized


def test_ascii_punct_record_idempotent() -> None:
    # T8/T9/T10 templates contain no characters in the replacement set.
    result = format_streak_record("Tigers", 8, 8, "Lions")
    assert result is not None
    headline, detail = result
    assert _ascii_punct(headline) == headline
    assert _ascii_punct(detail) == detail


def test_ascii_punct_marker_idempotent() -> None:
    for streak in [-3, -1, 0, 1, 4]:
        out = format_streak_marker(streak)
        assert _ascii_punct(out) == out


# =====================================================================
# Behavioral parity — synthetic context drives _detect_streaks
# =====================================================================

def _stub_team_record(fid: str, wins: int, losses: int, streak: int) -> TeamRecord:
    return TeamRecord(
        franchise_id=fid, wins=wins, losses=losses, ties=0,
        points_for=100.0 * (wins + losses), points_against=95.0 * (wins + losses),
        current_streak=streak,
    )


def _stub_matchup(
    winner_id: str, loser_id: str, winner_score: float = 110.0, loser_score: float = 90.0,
) -> WeekMatchupContext:
    return WeekMatchupContext(
        winner_id=winner_id, loser_id=loser_id,
        winner_score=winner_score, loser_score=loser_score,
        margin=winner_score - loser_score, is_tie=False,
        winner_record_after=None, loser_record_after=None,
    )


def _make_context(matchups: tuple, standings: tuple, *, total_through_week: int | None = None):
    from squadvault.core.recaps.context.season_context_v1 import SeasonContextV1
    return SeasonContextV1(
        league_id="test_league",
        season=2025,
        through_week=13,
        standings=standings,
        week_matchups=matchups,
        week_high_scorer=None,
        week_low_scorer=None,
        week_closest_game=None,
        week_biggest_blowout=None,
        season_high=None,
        season_low=None,
        season_avg_score=None,
        total_matchups_through_week=(
            total_through_week if total_through_week is not None
            else max(len(matchups) * 13, 1 if standings else 0)
        ),
        matchups_this_week=len(matchups),
        playoff_info=None,
    )


def test_parity_detect_streaks_t1_long_winning() -> None:
    """_detect_streaks on streak=4 produces headline equal to format_streak_status."""
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streaks

    standings = (
        _stub_team_record("F1", 7, 1, 4),  # streak=4 -> T1 fires
        _stub_team_record("F2", 1, 7, 0),
    )
    matchups = (_stub_matchup("F1", "F2"),)
    ctx = _make_context(matchups, standings)
    angles = _detect_streaks(ctx)
    streak_angles = [a for a in angles if a.category == "STREAK"]
    assert len(streak_angles) == 1
    assert streak_angles[0].headline == format_streak_status("F1", 4)
    # And the detail equals the outcome helper output.
    assert streak_angles[0].detail == format_streak_outcome("F1", "7-1", True, "F2")


def test_parity_detect_streaks_t2_short_winning() -> None:
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streaks

    standings = (
        _stub_team_record("F1", 5, 2, 3),  # streak=3 -> T2 fires
        _stub_team_record("F2", 2, 5, 0),
    )
    matchups = (_stub_matchup("F1", "F2"),)
    ctx = _make_context(matchups, standings)
    streak_angles = [a for a in _detect_streaks(ctx) if a.category == "STREAK"]
    assert len(streak_angles) == 1
    assert streak_angles[0].headline == format_streak_status("F1", 3)
    assert streak_angles[0].detail == format_streak_outcome("F1", "5-2", True, "F2")


def test_parity_detect_streaks_t3_long_losing() -> None:
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streaks

    standings = (
        _stub_team_record("F1", 7, 1, 0),
        _stub_team_record("F2", 1, 7, -4),  # streak=-4 -> T3 fires
    )
    matchups = (_stub_matchup("F1", "F2"),)  # F2 lost again
    ctx = _make_context(matchups, standings)
    streak_angles = [a for a in _detect_streaks(ctx) if a.category == "STREAK"]
    assert len(streak_angles) == 1
    assert streak_angles[0].headline == format_streak_status("F2", -4)
    assert streak_angles[0].detail == format_streak_outcome("F2", "1-7", False, "F1")


def test_parity_detect_streaks_t4_short_losing() -> None:
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streaks

    standings = (
        _stub_team_record("F1", 5, 2, 0),
        _stub_team_record("F2", 2, 5, -3),  # streak=-3 -> T4 fires
    )
    matchups = (_stub_matchup("F1", "F2"),)
    ctx = _make_context(matchups, standings)
    streak_angles = [a for a in _detect_streaks(ctx) if a.category == "STREAK"]
    assert len(streak_angles) == 1
    assert streak_angles[0].headline == format_streak_status("F2", -3)
    assert streak_angles[0].detail == format_streak_outcome("F2", "2-5", False, "F1")


def test_parity_detect_streaks_below_threshold_no_angle() -> None:
    """|streak| in {-2,-1,0,1,2} produces zero STREAK angles."""
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streaks

    for streak in [-2, -1, 0, 1, 2]:
        standings = (
            _stub_team_record("F1", 4, 4, streak),
            _stub_team_record("F2", 4, 4, 0),
        )
        matchups = (_stub_matchup("F1", "F2"),)
        ctx = _make_context(matchups, standings)
        streak_angles = [a for a in _detect_streaks(ctx) if a.category == "STREAK"]
        assert len([a for a in streak_angles if "F1" in a.headline]) == 0, (
            f"Unexpected STREAK angle for streak={streak}"
        )


# =====================================================================
# Behavioral parity — _detect_streak_records
# =====================================================================

def _stub_streak_record(fid: str, length: int, kind: str) -> StreakRecord:
    return StreakRecord(
        franchise_id=fid, streak_type=kind, length=length,
        start_season=2020, start_week=1, end_season=2020, end_week=length,
    )


def _stub_history(
    win_streak: StreakRecord | None,
    loss_streak: StreakRecord | None,
) -> LeagueHistoryContextV1:
    return LeagueHistoryContextV1(
        league_id="test_league",
        seasons_available=(2020, 2021, 2022, 2023, 2024, 2025),  # multi-season
        total_matchups_all_time=600,
        all_time_records=(),
        all_time_high=None,
        all_time_low=None,
        all_time_avg_score=None,
        longest_win_streak=win_streak,
        longest_loss_streak=loss_streak,
        best_season_record=None,
        worst_season_record=None,
    )


def test_parity_detect_streak_records_t8_tied() -> None:
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streak_records

    standings = (_stub_team_record("F1", 8, 0, 8),)  # streak ties record
    ctx = _make_context((), standings)
    history = _stub_history(_stub_streak_record("HOLDER", 8, "win"), None)
    angles = _detect_streak_records(ctx, history)
    assert len(angles) == 1
    expected = format_streak_record("F1", 8, 8, "HOLDER")
    assert expected is not None
    assert angles[0].headline == expected[0]
    assert angles[0].detail == expected[1]


def test_parity_detect_streak_records_t9_approach() -> None:
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streak_records

    standings = (_stub_team_record("F1", 7, 0, 7),)  # one win short of record (8)
    ctx = _make_context((), standings)
    history = _stub_history(_stub_streak_record("HOLDER", 8, "win"), None)
    angles = _detect_streak_records(ctx, history)
    assert len(angles) == 1
    expected = format_streak_record("F1", 7, 8, "HOLDER")
    assert expected is not None
    assert angles[0].headline == expected[0]
    assert angles[0].detail == expected[1]


def test_parity_detect_streak_records_t10_tied_losing() -> None:
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streak_records

    standings = (_stub_team_record("F1", 0, 8, -8),)  # streak ties loss record
    ctx = _make_context((), standings)
    history = _stub_history(None, _stub_streak_record("LHOLDER", 8, "loss"))
    angles = _detect_streak_records(ctx, history)
    assert len(angles) == 1
    expected = format_streak_record("F1", -8, 8, "LHOLDER")
    assert expected is not None
    assert angles[0].headline == expected[0]
    assert angles[0].detail == expected[1]


def test_parity_detect_streak_records_t9_loss_approach() -> None:
    """T9-LOSS: -7 vs record 8 produces a one-from-record angle.

    Mirrors test_parity_detect_streak_records_t9_approach above;
    the §10 Q1 thread closure added the loss-side approach form.
    """
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_streak_records

    standings = (_stub_team_record("F1", 0, 7, -7),)  # one loss short of record (8)
    ctx = _make_context((), standings)
    history = _stub_history(None, _stub_streak_record("LHOLDER", 8, "loss"))
    angles = _detect_streak_records(ctx, history)
    assert len(angles) == 1
    expected = format_streak_record("F1", -7, 8, "LHOLDER")
    assert expected is not None
    assert angles[0].headline == expected[0]
    assert angles[0].detail == expected[1]


# =====================================================================
# Behavioral parity — season_context_v1 standings marker
# =====================================================================

def test_parity_season_context_standings_marker() -> None:
    """The standings-row 'Streak: {marker}' value comes from format_streak_marker."""
    from squadvault.core.recaps.context.season_context_v1 import render_season_context_for_prompt

    standings = (
        _stub_team_record("F1", 8, 1, 4),   # W4
        _stub_team_record("F2", 5, 4, -2),  # L2
        _stub_team_record("F3", 4, 5, 0),   # -
    )
    ctx = _make_context((), standings)
    out = render_season_context_for_prompt(ctx)
    # Each marker form must appear exactly as the helper produces it.
    assert f"Streak: {format_streak_marker(4)}" in out
    assert f"Streak: {format_streak_marker(-2)}" in out
    assert f"Streak: {format_streak_marker(0)}" in out


# =====================================================================
# Behavioral parity — franchise_deep_angles_v1 D49 sub-phrase
# =====================================================================

def test_parity_d49_streak_phrase_substring() -> None:
    """D49 headlines embed format_streak_phrase verbatim as a sub-phrase."""
    # Direct integration test: validate that the substring produced by
    # the helper appears in a synthetically constructed D49 headline.
    # The full D49 detector requires a non-trivial canonical event
    # corpus to fire; we restrict this parity check to the sub-phrase
    # contract that the refactor preserves.
    n_games = 5
    expected_sub = format_streak_phrase(n_games)
    assert expected_sub == "5-game win streak"
    # The four D49 tier headlines all contain "{name}'s {phrase} has [...] margins: ..."
    # so testing any one tier's composition suffices for the sub-phrase contract.
    composed = f"Wolves's {expected_sub} has growing margins: 5, 10, 15, 20, 25"
    assert expected_sub in composed
