"""Unit tests for per-matchup anchors (Option 2, phase 1).

Pure functions over HistoricalMatchup lists -- no DB. Covers current-streak
computation (incl. tie-breaks-streak), H2H/season-record/streak rendering, and
the explicit-absence paths (no prior meetings / 0-0 / no active streak).
"""
from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    compute_current_streaks,
)
from squadvault.core.recaps.render.render_matchup_anchors_v1 import (
    render_matchup_anchors_for_prompt,
)


def _m(season, week, w, lo, tie=False):
    return HistoricalMatchup(
        season=season, week=week, winner_id=w, loser_id=lo,
        winner_score=100.0, loser_score=(100.0 if tie else 90.0),
        is_tie=tie, margin=(0.0 if tie else 10.0),
    )


_SCHEDULE = [
    _m(2024, 1, "A", "B"), _m(2024, 2, "A", "B"),
    _m(2025, 1, "A", "C"), _m(2025, 1, "B", "D"),
    _m(2025, 2, "A", "D"), _m(2025, 2, "C", "B"),
    _m(2025, 3, "A", "B"), _m(2025, 3, "D", "C"),
]
_NAMES = {"A": "Robb's Raiders", "B": "Ben's Gods", "C": "Purple Haze", "D": "Stu's Crew"}


def test_current_streaks_through_week_3():
    st = compute_current_streaks(_SCHEDULE)
    assert st["A"] == ("win", 5)
    assert st["B"] == ("loss", 2)
    assert st["C"] == ("loss", 1)
    assert st["D"] == ("win", 1)


def test_tie_breaks_streak():
    st = compute_current_streaks(_SCHEDULE + [_m(2025, 4, "A", "D", tie=True)])
    assert st["A"] == ("none", 0)
    assert st["D"] == ("none", 0)


def test_renderer_h2h_record_and_streak():
    out = render_matchup_anchors_for_prompt(
        matchups=_SCHEDULE, week_pairs=[("A", "B"), ("C", "D")],
        current_season=2025, week=3, name_map=_NAMES,
    )
    assert "Robb's Raiders leads 3-0 (3 meetings)." in out
    assert "Stu's Crew leads 1-0 (1 meeting)." in out          # singular
    assert "(1 meetings)" not in out
    assert "Robb's Raiders: season 3-0; current a 5-game winning streak" in out
    assert "Ben's Gods: season 1-2; current a 2-game losing streak" in out
    assert "Purple Haze: season 1-2; current a 1-game losing streak" in out
    assert "Stu's Crew: season 1-2; current a 1-game winning streak" in out
    assert "cite these exactly" in out


def test_renderer_explicit_absence():
    out = render_matchup_anchors_for_prompt(
        matchups=[_m(2025, 1, "A", "B")], week_pairs=[("A", "C")],
        current_season=2025, week=1, name_map=_NAMES,
    )
    assert "no prior meetings" in out
    assert (
        "Purple Haze: season 0-0 (no games yet this season); "
        "current no active streak" in out
    )


def test_renderer_empty_pairs_returns_empty():
    assert render_matchup_anchors_for_prompt(
        matchups=_SCHEDULE, week_pairs=[], current_season=2025, week=3,
    ) == ""
