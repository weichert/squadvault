"""Tests for Championship Timeline Aggregations v1 (A3 surface derivation).

Pure unit tests against synthetic `HistoricalMatchup` data. No database
fixtures — these functions operate on in-memory sequences. Integration
with `load_all_matchups` and the canonical event ledger is covered by
the existing `test_league_history_v1.py` test surface.

The three A3-specific invariants from the A3 spec (§6.2 / §6.3 / §6.7)
are exercised explicitly:

- W17/W18 collapse-by-content (§6.2): `TestComputePlayoffBracket`'s
  collapse tests — duplicate consecutive playoff weeks collapse, by
  content equality, not by era.
- Per-season set semantics (§6.3):
  `TestComputeCrossSeasonPlayoffRecords.test_per_season_set_semantics`
  — a franchise in two playoff weeks of one season counts as one
  playoff-season appearance.
- Not-a-real-time-tracker (§6.7) is an operational-cadence invariant
  enforced by the generation script's design, not the aggregation
  layer; it has no aggregation-layer test.
"""
from __future__ import annotations

from squadvault.core.recaps.context.championship_timeline_aggregations_v1 import (
    ROUND_CHAMPIONSHIP,
    ROUND_PRELIMINARY,
    ROUND_SEMIFINAL,
    BridesmaidRecord,
    CrossSeasonPlayoffRecords,
    FranchisePlayoffRecord,
    SeasonBracket,
    _label_for_round,
    _longest_consecutive_run,
    compute_bridesmaids,
    compute_cross_season_playoff_records,
    compute_playoff_bracket,
)
from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    ChampionshipResult,
)
from squadvault.core.recaps.context.league_history_v1 import HistoricalMatchup

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
        margin=round(abs(ws - ls), 2),
    )


def _regular_season(
    season: int, *, weeks: int = 14, matchups_per_week: int = 5,
) -> list[HistoricalMatchup]:
    """Build a regular season: `weeks` weeks of `matchups_per_week` games.

    Regular-season franchises are named `r0`..`r{2*matchups_per_week-1}`
    so they never collide with the playoff franchises tests pass in
    explicitly. The mode of per-week matchup counts is
    `matchups_per_week`.
    """
    out: list[HistoricalMatchup] = []
    for w in range(1, weeks + 1):
        for i in range(matchups_per_week):
            out.append(_matchup(
                season=season, week=w,
                winner=f"r{2 * i}", loser=f"r{2 * i + 1}",
            ))
    return out


def _playoff_week(
    season: int,
    week: int,
    pairs: list[tuple],
) -> list[HistoricalMatchup]:
    """Build one playoff week from `(winner, loser[, ws, ls])` tuples."""
    out: list[HistoricalMatchup] = []
    for p in pairs:
        if len(p) == 4:
            w, lo, ws, ls = p
        else:
            w, lo = p
            ws, ls = 120.0, 100.0
        out.append(_matchup(
            season=season, week=week, winner=w, loser=lo, ws=ws, ls=ls,
        ))
    return out


def _standard_playoff_season(
    season: int,
    *,
    regular_weeks: int = 14,
    prelim: list[tuple] | None = None,
    semifinal: list[tuple] | None = None,
    championship: tuple = ("A", "B", 130.0, 90.0),
) -> list[HistoricalMatchup]:
    """A full season: regular weeks + a clean 3-round playoff bracket.

    Playoff weeks are `regular_weeks+1` (preliminary, default 4
    matchups), `regular_weeks+2` (semifinal, default 2 matchups), and
    `regular_weeks+3` (championship, 1 matchup). Each playoff week's
    count is below the regular-season mode of 5, so the
    playoff-detection trick flags all three.
    """
    if prelim is None:
        prelim = [("A", "H"), ("B", "G"), ("C", "F"), ("D", "E")]
    if semifinal is None:
        semifinal = [("A", "C"), ("B", "D")]

    out = _regular_season(season, weeks=regular_weeks)
    out += _playoff_week(season, regular_weeks + 1, prelim)
    out += _playoff_week(season, regular_weeks + 2, semifinal)
    out += _playoff_week(season, regular_weeks + 3, [championship])
    return out


# ── Unit: _label_for_round ───────────────────────────────────────────


class TestLabelForRound:
    def test_three_round_bracket(self):
        # idx 0,1,2 of a 3-round bracket -> prelim, semifinal, championship
        assert _label_for_round(0, 3) == ROUND_PRELIMINARY
        assert _label_for_round(1, 3) == ROUND_SEMIFINAL
        assert _label_for_round(2, 3) == ROUND_CHAMPIONSHIP

    def test_single_round_bracket(self):
        assert _label_for_round(0, 1) == ROUND_CHAMPIONSHIP

    def test_two_round_bracket(self):
        assert _label_for_round(0, 2) == ROUND_SEMIFINAL
        assert _label_for_round(1, 2) == ROUND_CHAMPIONSHIP

    def test_four_round_bracket_uses_round_n_for_extra(self):
        # earliest round of a 4-round bracket is "Round 1"; the rest
        # are the three named rounds counting back from the end.
        assert _label_for_round(0, 4) == "Round 1"
        assert _label_for_round(1, 4) == ROUND_PRELIMINARY
        assert _label_for_round(2, 4) == ROUND_SEMIFINAL
        assert _label_for_round(3, 4) == ROUND_CHAMPIONSHIP


# ── Unit: _longest_consecutive_run ───────────────────────────────────


class TestLongestConsecutiveRun:
    def test_empty_set_returns_zero(self):
        assert _longest_consecutive_run(set()) == 0

    def test_single_element(self):
        assert _longest_consecutive_run({2015}) == 1

    def test_fully_contiguous(self):
        assert _longest_consecutive_run({2010, 2011, 2012, 2013}) == 4

    def test_gapped_returns_longest_run(self):
        # 2010-2012 (run of 3), gap, 2015-2016 (run of 2) -> 3
        assert _longest_consecutive_run({2010, 2011, 2012, 2015, 2016}) == 3

    def test_two_equal_runs(self):
        assert _longest_consecutive_run({2010, 2011, 2014, 2015}) == 2

    def test_all_isolated(self):
        assert _longest_consecutive_run({2010, 2012, 2014}) == 1


# ── Unit: compute_playoff_bracket ────────────────────────────────────


class TestComputePlayoffBracket:
    def test_single_clean_three_round_season(self):
        matchups = _standard_playoff_season(2018)
        brackets = compute_playoff_bracket(matchups)
        assert len(brackets) == 1
        bracket = brackets[0]
        assert isinstance(bracket, SeasonBracket)
        assert bracket.season == 2018
        assert len(bracket.rounds) == 3
        assert [r.round_label for r in bracket.rounds] == [
            ROUND_PRELIMINARY, ROUND_SEMIFINAL, ROUND_CHAMPIONSHIP,
        ]
        assert [r.week for r in bracket.rounds] == [15, 16, 17]

    def test_rounds_carry_their_matchups(self):
        matchups = _standard_playoff_season(2018)
        bracket = compute_playoff_bracket(matchups)[0]
        prelim, semifinal, championship = bracket.rounds
        assert len(prelim.matchups) == 4
        assert len(semifinal.matchups) == 2
        assert len(championship.matchups) == 1
        champ_matchup = championship.matchups[0]
        assert champ_matchup.winner_id == "A"
        assert champ_matchup.loser_id == "B"

    def test_matchups_sorted_within_round(self):
        # prelim pairs passed out of order; the round must sort them
        # by (winner_id, loser_id) for determinism.
        matchups = _standard_playoff_season(
            2018,
            prelim=[("D", "E"), ("A", "H"), ("C", "F"), ("B", "G")],
        )
        prelim = compute_playoff_bracket(matchups)[0].rounds[0]
        winners = [m.winner_id for m in prelim.matchups]
        assert winners == ["A", "B", "C", "D"]

    def test_multiple_seasons_sorted_ascending(self):
        matchups = (
            _standard_playoff_season(2020)
            + _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
        )
        brackets = compute_playoff_bracket(matchups)
        assert [b.season for b in brackets] == [2018, 2019, 2020]

    def test_empty_input_returns_empty(self):
        assert compute_playoff_bracket([]) == ()

    def test_regular_season_only_season_omitted(self):
        # A season with no week below the mode has no detectable
        # playoffs and is silently omitted per D3-Alpha + Reset Memo
        # section 2.3.
        matchups = _regular_season(2017, weeks=14)
        assert compute_playoff_bracket(matchups) == ()

    def test_w17_w18_duplicate_collapses_to_championship(self):
        # The A3 spec section 6.2 invariant: a post-2021-style season
        # carries verbatim-identical W17 and W18 championship rows. The
        # later week is dropped; the bracket presents as a clean
        # 3-round shape with W17 as the Championship round.
        matchups = _regular_season(2022, weeks=14)
        matchups += _playoff_week(2022, 15, [
            ("A", "H"), ("B", "G"), ("C", "F"), ("D", "E"),
        ])
        matchups += _playoff_week(2022, 16, [("A", "C"), ("B", "D")])
        matchups += _playoff_week(2022, 17, [("A", "B", 120.0, 100.0)])
        matchups += _playoff_week(2022, 18, [("A", "B", 120.0, 100.0)])
        bracket = compute_playoff_bracket(matchups)[0]
        assert len(bracket.rounds) == 3
        assert [r.week for r in bracket.rounds] == [15, 16, 17]
        assert bracket.rounds[-1].round_label == ROUND_CHAMPIONSHIP
        assert bracket.rounds[-1].week == 17

    def test_collapse_is_content_based_not_era_based(self):
        # Two consecutive playoff weeks with DIFFERENT scores are NOT
        # duplicates and must NOT collapse — proving the rule is keyed
        # on content equality, not on "post-2021, suppress W18".
        matchups = _regular_season(2022, weeks=14)
        matchups += _playoff_week(2022, 15, [
            ("A", "H"), ("B", "G"), ("C", "F"), ("D", "E"),
        ])
        matchups += _playoff_week(2022, 16, [("A", "C"), ("B", "D")])
        matchups += _playoff_week(2022, 17, [("A", "B", 120.0, 100.0)])
        matchups += _playoff_week(2022, 18, [("A", "B", 130.0, 90.0)])
        bracket = compute_playoff_bracket(matchups)[0]
        assert len(bracket.rounds) == 4
        assert [r.week for r in bracket.rounds] == [15, 16, 17, 18]

    def test_collapse_robust_to_substrate_change_no_duplicate(self):
        # A re-ingested season with the duplication removed (no W18 at
        # all) yields a clean 3-round bracket with no collapse needed —
        # the content-based rule simply finds nothing to collapse.
        matchups = _regular_season(2022, weeks=14)
        matchups += _playoff_week(2022, 15, [
            ("A", "H"), ("B", "G"), ("C", "F"), ("D", "E"),
        ])
        matchups += _playoff_week(2022, 16, [("A", "C"), ("B", "D")])
        matchups += _playoff_week(2022, 17, [("A", "B", 120.0, 100.0)])
        bracket = compute_playoff_bracket(matchups)[0]
        assert len(bracket.rounds) == 3
        assert [r.week for r in bracket.rounds] == [15, 16, 17]

    def test_collapse_requires_consecutive_week_numbers(self):
        # Identical content in NON-consecutive playoff weeks (W16, W18
        # with W17 absent) does not collapse — the spec rule is keyed
        # on "two consecutive playoff weeks".
        matchups = _regular_season(2022, weeks=14)
        matchups += _playoff_week(2022, 15, [
            ("A", "H"), ("B", "G"), ("C", "F"), ("D", "E"),
        ])
        matchups += _playoff_week(2022, 16, [("A", "B", 120.0, 100.0)])
        matchups += _playoff_week(2022, 18, [("A", "B", 120.0, 100.0)])
        bracket = compute_playoff_bracket(matchups)[0]
        assert len(bracket.rounds) == 3
        assert [r.week for r in bracket.rounds] == [15, 16, 18]

    def test_triple_duplicate_collapses_to_one(self):
        # Anomaly robustness: W17 == W18 == W19, all verbatim-identical
        # and week-consecutive, collapse to a single Championship round.
        matchups = _regular_season(2022, weeks=14)
        matchups += _playoff_week(2022, 15, [
            ("A", "H"), ("B", "G"), ("C", "F"), ("D", "E"),
        ])
        matchups += _playoff_week(2022, 16, [("A", "C"), ("B", "D")])
        matchups += _playoff_week(2022, 17, [("A", "B", 120.0, 100.0)])
        matchups += _playoff_week(2022, 18, [("A", "B", 120.0, 100.0)])
        matchups += _playoff_week(2022, 19, [("A", "B", 120.0, 100.0)])
        bracket = compute_playoff_bracket(matchups)[0]
        assert len(bracket.rounds) == 3
        assert [r.week for r in bracket.rounds] == [15, 16, 17]

    def test_two_round_bracket_labels(self):
        # A season with only two detectable playoff weeks labels them
        # semifinal -> championship (counting back from the end).
        matchups = _regular_season(2016, weeks=14)
        matchups += _playoff_week(2016, 15, [("A", "C"), ("B", "D")])
        matchups += _playoff_week(2016, 16, [("A", "B")])
        bracket = compute_playoff_bracket(matchups)[0]
        assert [r.round_label for r in bracket.rounds] == [
            ROUND_SEMIFINAL, ROUND_CHAMPIONSHIP,
        ]


# ── Unit: compute_cross_season_playoff_records ───────────────────────


class TestComputeCrossSeasonPlayoffRecords:
    def test_empty_input(self):
        records = compute_cross_season_playoff_records([])
        assert isinstance(records, CrossSeasonPlayoffRecords)
        assert records.per_franchise == ()
        assert records.total_seasons == 0

    def test_total_seasons_counts_distinct_seasons(self):
        matchups = (
            _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
        )
        records = compute_cross_season_playoff_records(matchups)
        assert records.total_seasons == 2

    def test_per_season_set_semantics(self):
        # The A3 spec section 6.3 invariant. Franchise "A" appears in
        # all three playoff weeks of a single season (prelim, semifinal,
        # championship). Per-season set semantics: that is ONE
        # playoff-season appearance, not three.
        matchups = _standard_playoff_season(2018)
        records = compute_cross_season_playoff_records(matchups)
        rec_a = next(r for r in records.per_franchise if r.franchise_id == "A")
        assert rec_a.playoff_season_count == 1

    def test_playoff_appearances_accumulate_across_seasons(self):
        # "A" makes the playoffs in three separate seasons -> count 3.
        matchups = (
            _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
            + _standard_playoff_season(2020)
        )
        records = compute_cross_season_playoff_records(matchups)
        rec_a = next(r for r in records.per_franchise if r.franchise_id == "A")
        assert rec_a.playoff_season_count == 3

    def test_championship_appearance_count(self):
        # "A" and "B" meet in the championship every season; each gets
        # one championship appearance per season.
        matchups = (
            _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
        )
        records = compute_cross_season_playoff_records(matchups)
        rec_a = next(r for r in records.per_franchise if r.franchise_id == "A")
        rec_b = next(r for r in records.per_franchise if r.franchise_id == "B")
        assert rec_a.championship_appearance_count == 2
        assert rec_b.championship_appearance_count == 2

    def test_longest_active_streak(self):
        # "A" makes the playoffs 2017, 2018, 2019 (consecutive) and 2022
        # -> longest active streak is 3.
        matchups = (
            _standard_playoff_season(2017)
            + _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
            + _standard_playoff_season(2022)
        )
        records = compute_cross_season_playoff_records(matchups)
        rec_a = next(r for r in records.per_franchise if r.franchise_id == "A")
        assert rec_a.longest_active_streak == 3

    def test_longest_drought_streak(self):
        # "Z" is active every season (appears in the prelim round) but
        # only makes a deeper run once. Build: 2017-2020 Z plays the
        # prelim and loses; only in 2018 does Z reach the semifinal.
        # Z's playoff seasons: all of 2017-2020 (it is in the prelim
        # week each year). To create an actual drought we need a
        # franchise active but absent from every playoff week.
        # "r0" is a regular-season-only franchise: active each season,
        # never in a playoff week -> drought spans every season.
        matchups = (
            _standard_playoff_season(2017)
            + _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
        )
        records = compute_cross_season_playoff_records(matchups)
        rec_r0 = next(r for r in records.per_franchise if r.franchise_id == "r0")
        assert rec_r0.playoff_season_count == 0
        assert rec_r0.longest_active_streak == 0
        assert rec_r0.longest_drought_streak == 3

    def test_drought_zero_when_franchise_always_makes_playoffs(self):
        # "A" makes the playoffs every active season -> drought 0.
        matchups = (
            _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
        )
        records = compute_cross_season_playoff_records(matchups)
        rec_a = next(r for r in records.per_franchise if r.franchise_id == "A")
        assert rec_a.longest_drought_streak == 0

    def test_drought_respects_tenure_gap(self):
        # "r0" is active 2017-2018, absent 2019, active 2020 — and never
        # makes a playoff week. The 2019 gap is not in its active set,
        # so the drought runs are 2017-2018 (length 2) and 2020 (length
        # 1); the longest is 2, not 4.
        matchups = (
            _standard_playoff_season(2017)
            + _standard_playoff_season(2018)
            + _standard_playoff_season(2020)
        )
        records = compute_cross_season_playoff_records(matchups)
        rec_r0 = next(r for r in records.per_franchise if r.franchise_id == "r0")
        assert rec_r0.longest_drought_streak == 2

    def test_sort_order_franchise_id_tiebreak(self):
        # "A" and "B" each make all three playoff seasons, each appear
        # in all three championships, each carry a 3-season active
        # streak — they tie on every sort key except franchise_id, so
        # "A" sorts ahead of "B".
        matchups = (
            _standard_playoff_season(2017)
            + _standard_playoff_season(2018)
            + _standard_playoff_season(2019)
        )
        records = compute_cross_season_playoff_records(matchups)
        fids = [r.franchise_id for r in records.per_franchise]
        assert fids.index("A") < fids.index("B")

    def test_franchise_never_in_playoffs(self):
        # A regular-season-only franchise has zero playoff seasons and
        # zero active streak but is still present in the records (it is
        # an active franchise).
        matchups = _standard_playoff_season(2018)
        records = compute_cross_season_playoff_records(matchups)
        rec_r2 = next(r for r in records.per_franchise if r.franchise_id == "r2")
        assert rec_r2.playoff_season_count == 0
        assert rec_r2.championship_appearance_count == 0
        assert rec_r2.longest_active_streak == 0

    def test_records_are_franchise_playoff_record_instances(self):
        matchups = _standard_playoff_season(2018)
        records = compute_cross_season_playoff_records(matchups)
        assert all(
            isinstance(r, FranchisePlayoffRecord)
            for r in records.per_franchise
        )


# ── Unit: compute_bridesmaids ────────────────────────────────────────


def _champ_result(
    season: int, champion: str, runner_up: str,
) -> ChampionshipResult:
    """Build a ChampionshipResult for bridesmaid tests."""
    return ChampionshipResult(
        season=season,
        champion_id=champion,
        runner_up_id=runner_up,
        championship_week=17,
        champion_score=120.0,
        runner_up_score=100.0,
        is_tie=False,
    )


class TestComputeBridesmaids:
    def test_empty_input_returns_empty(self):
        assert compute_bridesmaids([]) == ()

    def test_groups_by_runner_up(self):
        roll = [
            _champ_result(2018, "A", "B"),
            _champ_result(2019, "A", "B"),
            _champ_result(2020, "C", "D"),
        ]
        bridesmaids = compute_bridesmaids(roll)
        rec_b = next(r for r in bridesmaids if r.franchise_id == "B")
        assert rec_b.runner_up_count == 2

    def test_runner_up_seasons_sorted(self):
        roll = [
            _champ_result(2020, "A", "B"),
            _champ_result(2018, "A", "B"),
            _champ_result(2019, "C", "B"),
        ]
        bridesmaids = compute_bridesmaids(roll)
        rec_b = next(r for r in bridesmaids if r.franchise_id == "B")
        assert rec_b.runner_up_seasons == (2018, 2019, 2020)

    def test_perennial_bridesmaid_zero_titles(self):
        # "B" is the runner-up three times and champion zero times —
        # the perennial-bridesmaid archetype per spec section 3.7.
        roll = [
            _champ_result(2018, "A", "B"),
            _champ_result(2019, "C", "B"),
            _champ_result(2020, "D", "B"),
        ]
        bridesmaids = compute_bridesmaids(roll)
        rec_b = next(r for r in bridesmaids if r.franchise_id == "B")
        assert rec_b.runner_up_count == 3
        assert rec_b.championship_count == 0

    def test_championship_count_carried(self):
        # "A" wins twice and is runner-up once.
        roll = [
            _champ_result(2018, "A", "B"),
            _champ_result(2019, "A", "C"),
            _champ_result(2020, "D", "A"),
        ]
        bridesmaids = compute_bridesmaids(roll)
        rec_a = next(r for r in bridesmaids if r.franchise_id == "A")
        assert rec_a.runner_up_count == 1
        assert rec_a.championship_count == 2

    def test_sort_order_runner_up_desc(self):
        roll = [
            _champ_result(2018, "A", "B"),
            _champ_result(2019, "A", "B"),
            _champ_result(2020, "A", "C"),
        ]
        bridesmaids = compute_bridesmaids(roll)
        assert bridesmaids[0].franchise_id == "B"
        assert bridesmaids[0].runner_up_count == 2

    def test_sort_tiebreak_fewer_titles_ranks_higher(self):
        # "B" and "C" each have one runner-up finish; "C" also has a
        # title, "B" has none. "B" — the purer bridesmaid — ranks first.
        roll = [
            _champ_result(2018, "A", "B"),
            _champ_result(2019, "A", "C"),
            _champ_result(2020, "C", "D"),
        ]
        bridesmaids = compute_bridesmaids(roll)
        b_idx = next(
            i for i, r in enumerate(bridesmaids) if r.franchise_id == "B"
        )
        c_idx = next(
            i for i, r in enumerate(bridesmaids) if r.franchise_id == "C"
        )
        assert b_idx < c_idx

    def test_champion_only_franchise_absent_from_bridesmaids(self):
        # A franchise that is only ever champion, never runner-up, does
        # not appear in the Bridesmaids leaderboard at all.
        roll = [_champ_result(2018, "A", "B")]
        bridesmaids = compute_bridesmaids(roll)
        assert all(r.franchise_id != "A" for r in bridesmaids)

    def test_returns_tuple_of_bridesmaid_record(self):
        roll = [_champ_result(2018, "A", "B")]
        bridesmaids = compute_bridesmaids(roll)
        assert isinstance(bridesmaids, tuple)
        assert all(isinstance(r, BridesmaidRecord) for r in bridesmaids)
