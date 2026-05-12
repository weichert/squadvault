"""Tests for Hall of Fame & Shame Aggregations v1 (A1 surface derivation).

Pure unit tests against synthetic `HistoricalMatchup` data. No database
fixtures — these functions operate on in-memory sequences. Integration
with `load_all_matchups` and the canonical event ledger is covered by
the existing `test_league_history_v1.py` test surface.
"""
from __future__ import annotations

import pytest

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    ChampionshipResult,
    _regular_season_matchup_count,
    compute_all_season_records,
    compute_blowouts_hall,
    compute_championship_roll,
)
from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    SeasonRecord,
)

# ── Helpers for synthetic data ───────────────────────────────────────


def _matchup(
    *,
    season: int,
    week: int,
    winner: str,
    loser: str,
    ws: float = 110.0,
    ls: float = 100.0,
    is_tie: bool = False,
) -> HistoricalMatchup:
    """Build a HistoricalMatchup with sensible defaults for tests."""
    return HistoricalMatchup(
        season=season,
        week=week,
        winner_id=winner,
        loser_id=loser,
        winner_score=ws,
        loser_score=ls,
        is_tie=is_tie,
        margin=ws - ls,
    )


def _ten_team_regular_week(
    *, season: int, week: int, results: list[tuple[str, str, float, float]]
) -> list[HistoricalMatchup]:
    """Build a full 5-matchup regular-season week for a 10-team league."""
    assert len(results) == 5, "10-team regular week must have 5 matchups"
    return [
        _matchup(season=season, week=week, winner=w, loser=lo, ws=ws, ls=ls)
        for (w, lo, ws, ls) in results
    ]


# ── Unit: _regular_season_matchup_count ──────────────────────────────


class TestRegularSeasonMatchupCount:
    """Behavior must remain identical to the duplicated origin in
    `franchise_deep_angles_v1._regular_season_matchup_count`."""

    def test_ten_team_regular_season(self):
        # 14 weeks of 5 matchups each (mode = 5)
        matchups = []
        for week in range(1, 15):
            matchups.extend(_ten_team_regular_week(
                season=2020, week=week,
                results=[
                    ("A", "B", 110, 100),
                    ("C", "D", 110, 100),
                    ("E", "F", 110, 100),
                    ("G", "H", 110, 100),
                    ("I", "J", 110, 100),
                ],
            ))
        assert _regular_season_matchup_count(matchups, 2020) == 5

    def test_returns_zero_for_missing_season(self):
        matchups = [_matchup(season=2023, week=1, winner="A", loser="B")]
        assert _regular_season_matchup_count(matchups, 2024) == 0

    def test_returns_zero_for_empty_input(self):
        assert _regular_season_matchup_count([], 2023) == 0

    def test_playoff_weeks_do_not_change_mode(self):
        # 5 regular weeks of 5 matchups + 2 playoff weeks (2 then 1)
        matchups = []
        for week in range(1, 6):
            matchups.extend(_ten_team_regular_week(
                season=2020, week=week,
                results=[
                    ("A", "B", 110, 100),
                    ("C", "D", 110, 100),
                    ("E", "F", 110, 100),
                    ("G", "H", 110, 100),
                    ("I", "J", 110, 100),
                ],
            ))
        # 2 playoff matchups at week 6
        matchups.append(_matchup(season=2020, week=6, winner="A", loser="C"))
        matchups.append(_matchup(season=2020, week=6, winner="E", loser="G"))
        # 1 championship matchup at week 7
        matchups.append(_matchup(season=2020, week=7, winner="A", loser="E"))
        assert _regular_season_matchup_count(matchups, 2020) == 5


# ── Unit: compute_blowouts_hall ──────────────────────────────────────


class TestBlowoutsHall:
    def test_sorts_by_margin_desc(self):
        matchups = [
            _matchup(season=2020, week=1, winner="A", loser="B", ws=100, ls=80),
            _matchup(season=2021, week=2, winner="C", loser="D", ws=150, ls=70),
            _matchup(season=2022, week=3, winner="E", loser="F", ws=120, ls=90),
        ]
        result = compute_blowouts_hall(matchups, top_n=3)
        assert len(result) == 3
        # 80-pt margin (C/D 2021) is top, then 30 (E/F 2022), then 20 (A/B 2020)
        assert result[0].winner_id == "C"
        assert result[0].margin == 80.0
        assert result[1].winner_id == "E"
        assert result[2].winner_id == "A"

    def test_top_n_truncates(self):
        matchups = [
            _matchup(season=2020, week=w, winner=f"W{w}", loser=f"L{w}", ws=100, ls=100 - w)
            for w in range(1, 11)
        ]
        result = compute_blowouts_hall(matchups, top_n=3)
        assert len(result) == 3

    def test_default_top_n_is_ten(self):
        matchups = [
            _matchup(season=2020, week=w, winner=f"W{w}", loser=f"L{w}", ws=100, ls=100 - w)
            for w in range(1, 16)
        ]
        result = compute_blowouts_hall(matchups)
        assert len(result) == 10

    def test_top_n_zero_returns_empty(self):
        matchups = [_matchup(season=2020, week=1, winner="A", loser="B")]
        assert compute_blowouts_hall(matchups, top_n=0) == ()

    def test_top_n_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            compute_blowouts_hall([], top_n=-1)

    def test_empty_matchups_returns_empty(self):
        assert compute_blowouts_hall([]) == ()

    def test_returns_tuple_immutable(self):
        matchups = [_matchup(season=2020, week=1, winner="A", loser="B")]
        result = compute_blowouts_hall(matchups)
        assert isinstance(result, tuple)

    def test_tie_breaking_deterministic(self):
        # Two matchups with identical margins must rank deterministically:
        # season asc → week asc → winner_id asc → loser_id asc.
        matchups = [
            _matchup(season=2021, week=5, winner="B", loser="A", ws=120, ls=80),  # 40 margin
            _matchup(season=2020, week=5, winner="C", loser="D", ws=120, ls=80),  # 40 margin
            _matchup(season=2020, week=3, winner="A", loser="B", ws=120, ls=80),  # 40 margin
        ]
        result = compute_blowouts_hall(matchups, top_n=3)
        # All 40-point margins; sort by (season, week, winner_id, loser_id)
        assert result[0].season == 2020
        assert result[0].week == 3
        assert result[1].season == 2020
        assert result[1].week == 5
        assert result[2].season == 2021

    def test_fewer_matchups_than_top_n(self):
        matchups = [
            _matchup(season=2020, week=1, winner="A", loser="B", ws=120, ls=100),
            _matchup(season=2020, week=2, winner="C", loser="D", ws=110, ls=100),
        ]
        result = compute_blowouts_hall(matchups, top_n=10)
        assert len(result) == 2


# ── Unit: compute_all_season_records ─────────────────────────────────


class TestAllSeasonRecords:
    def test_single_franchise_single_season(self):
        matchups = [
            _matchup(season=2023, week=1, winner="A", loser="B", ws=120, ls=100),
            _matchup(season=2023, week=2, winner="A", loser="C", ws=110, ls=105),
            _matchup(season=2023, week=3, winner="A", loser="D", ws=130, ls=70),
        ]
        result = compute_all_season_records(matchups)
        a_record = next(r for r in result if r.franchise_id == "A")
        assert a_record.wins == 3
        assert a_record.losses == 0
        assert a_record.ties == 0
        assert a_record.points_for == 360.0

    def test_worst_first_sort_order(self):
        # B loses 3 times (W1/W2/W3 to A); A wins 3 times. B should sort
        # before A under worst-first ordering.
        matchups = [
            _matchup(season=2023, week=1, winner="A", loser="B", ws=120, ls=100),
            _matchup(season=2023, week=2, winner="A", loser="B", ws=110, ls=105),
            _matchup(season=2023, week=3, winner="A", loser="B", ws=130, ls=70),
        ]
        result = compute_all_season_records(matchups)
        assert result[0].franchise_id == "B"
        assert result[0].losses == 3
        assert result[1].franchise_id == "A"
        assert result[1].losses == 0

    def test_tie_counts_for_both_sides(self):
        matchups = [
            _matchup(season=2023, week=1, winner="A", loser="B", ws=100, ls=100, is_tie=True),
        ]
        result = compute_all_season_records(matchups)
        a_rec = next(r for r in result if r.franchise_id == "A")
        b_rec = next(r for r in result if r.franchise_id == "B")
        assert a_rec.ties == 1
        assert a_rec.wins == 0
        assert b_rec.ties == 1
        assert b_rec.losses == 0

    def test_pf_accumulates_per_side(self):
        matchups = [
            _matchup(season=2023, week=1, winner="A", loser="B", ws=120.5, ls=100.25),
        ]
        result = compute_all_season_records(matchups)
        a_rec = next(r for r in result if r.franchise_id == "A")
        b_rec = next(r for r in result if r.franchise_id == "B")
        assert a_rec.points_for == 120.5
        assert b_rec.points_for == 100.25

    def test_franchise_appears_in_multiple_seasons(self):
        matchups = [
            _matchup(season=2023, week=1, winner="A", loser="B"),
            _matchup(season=2024, week=1, winner="A", loser="B"),
        ]
        result = compute_all_season_records(matchups)
        a_records = [r for r in result if r.franchise_id == "A"]
        assert len(a_records) == 2
        seasons = {r.season for r in a_records}
        assert seasons == {2023, 2024}

    def test_empty_input_returns_empty(self):
        assert compute_all_season_records([]) == ()

    def test_returns_tuple_of_season_record(self):
        matchups = [_matchup(season=2023, week=1, winner="A", loser="B")]
        result = compute_all_season_records(matchups)
        assert isinstance(result, tuple)
        assert all(isinstance(r, SeasonRecord) for r in result)

    def test_pf_tiebreak_under_same_losses(self):
        # Two franchises with the same loss count but different PF —
        # lower PF should sort first (worse).
        matchups = [
            _matchup(season=2023, week=1, winner="X", loser="A", ws=110, ls=80),
            _matchup(season=2023, week=2, winner="X", loser="A", ws=110, ls=85),
            _matchup(season=2023, week=3, winner="Y", loser="B", ws=110, ls=90),
            _matchup(season=2023, week=4, winner="Y", loser="B", ws=110, ls=95),
        ]
        result = compute_all_season_records(matchups)
        # A has 2 losses, PF 165; B has 2 losses, PF 185. A is worse.
        a_idx = next(i for i, r in enumerate(result) if r.franchise_id == "A")
        b_idx = next(i for i, r in enumerate(result) if r.franchise_id == "B")
        assert a_idx < b_idx


# ── Unit: compute_championship_roll ──────────────────────────────────


def _build_complete_season(
    *,
    season: int,
    regular_weeks: int = 14,
    semifinal_winners: tuple[str, str] = ("A", "C"),
    semifinal_losers: tuple[str, str] = ("B", "D"),
    champion: str = "A",
    runner_up: str = "C",
    champion_score: float = 130.0,
    runner_up_score: float = 100.0,
) -> list[HistoricalMatchup]:
    """Build a complete season with regular_weeks regular weeks (5 matchups
    each), a 2-matchup semifinal week, and a 1-matchup championship week.

    Default produces a 10-team season with 14 regular-season weeks; the
    playoff structure has semifinals at week=regular_weeks+1 and championship
    at week=regular_weeks+2.
    """
    matchups: list[HistoricalMatchup] = []
    # Regular season: 5 matchups per week
    franchises = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    for week in range(1, regular_weeks + 1):
        for i in range(0, 10, 2):
            w, lo = franchises[i], franchises[i + 1]
            matchups.append(_matchup(season=season, week=week, winner=w, loser=lo))
    # Semifinal week (2 matchups)
    sf_week = regular_weeks + 1
    matchups.append(_matchup(
        season=season, week=sf_week,
        winner=semifinal_winners[0], loser=semifinal_losers[0],
    ))
    matchups.append(_matchup(
        season=season, week=sf_week,
        winner=semifinal_winners[1], loser=semifinal_losers[1],
    ))
    # Championship week (1 matchup)
    matchups.append(_matchup(
        season=season, week=sf_week + 1,
        winner=champion, loser=runner_up,
        ws=champion_score, ls=runner_up_score,
    ))
    return matchups


class TestChampionshipRoll:
    def test_single_complete_season(self):
        matchups = _build_complete_season(season=2020)
        result = compute_championship_roll(matchups)
        assert len(result) == 1
        assert result[0].season == 2020
        assert result[0].champion_id == "A"
        assert result[0].runner_up_id == "C"
        assert result[0].champion_score == 130.0
        assert result[0].runner_up_score == 100.0
        assert result[0].is_tie is False
        assert result[0].championship_week == 16

    def test_multiple_seasons_sorted_asc(self):
        matchups = (
            _build_complete_season(season=2022, champion="C", runner_up="A")
            + _build_complete_season(season=2020, champion="A", runner_up="C")
            + _build_complete_season(season=2021, champion="E", runner_up="G")
        )
        result = compute_championship_roll(matchups)
        assert len(result) == 3
        assert [r.season for r in result] == [2020, 2021, 2022]
        assert [r.champion_id for r in result] == ["A", "E", "C"]

    def test_returns_tuple_of_championship_result(self):
        matchups = _build_complete_season(season=2020)
        result = compute_championship_roll(matchups)
        assert isinstance(result, tuple)
        assert all(isinstance(r, ChampionshipResult) for r in result)

    def test_empty_input_returns_empty(self):
        assert compute_championship_roll([]) == ()

    def test_regular_season_only_omits_season(self):
        # 14 weeks of 5 matchups each; no playoffs.
        matchups = []
        franchises = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        for week in range(1, 15):
            for i in range(0, 10, 2):
                matchups.append(_matchup(
                    season=2020, week=week,
                    winner=franchises[i], loser=franchises[i + 1],
                ))
        result = compute_championship_roll(matchups)
        # No playoff weeks → no detectable championship → silently omitted.
        assert result == ()

    def test_15_game_regular_season_post_2021_format(self):
        # Post-2021 PFL format: 15 regular weeks + semifinal week + championship.
        matchups = _build_complete_season(
            season=2022, regular_weeks=15,
            champion="A", runner_up="C",
        )
        result = compute_championship_roll(matchups)
        assert len(result) == 1
        assert result[0].championship_week == 17

    def test_tie_at_championship_week_preserved(self):
        matchups = _build_complete_season(season=2020)
        # Replace championship matchup with a tied result.
        # Filter out the original championship matchup at week 16.
        matchups = [m for m in matchups if m.week != 16]
        matchups.append(_matchup(
            season=2020, week=16, winner="A", loser="C",
            ws=120.0, ls=120.0, is_tie=True,
        ))
        result = compute_championship_roll(matchups)
        assert len(result) == 1
        assert result[0].is_tie is True

    def test_only_seasons_with_data_appear(self):
        matchups = _build_complete_season(season=2020)
        result = compute_championship_roll(matchups)
        # 2019, 2021, etc. should not appear.
        assert {r.season for r in result} == {2020}

    def test_multi_matchup_championship_week_picks_deterministically(self):
        # Data anomaly: two matchups at the championship week. Function
        # should pick deterministically and not raise.
        matchups = _build_complete_season(season=2020)
        # Add a second matchup at championship week (week 16). Both have
        # different winners; deterministic pick is by (week, winner_id,
        # loser_id) ascending.
        matchups.append(_matchup(
            season=2020, week=16, winner="Z", loser="Y",
            ws=140.0, ls=80.0,
        ))
        result = compute_championship_roll(matchups)
        # First by winner_id alphabetically: A < Z → champion is A.
        assert len(result) == 1
        assert result[0].champion_id == "A"
