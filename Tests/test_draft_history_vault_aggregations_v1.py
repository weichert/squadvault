"""Tests for Draft History Vault Aggregations v1 (A2 surface derivation).

Pure unit tests against synthetic AuctionPick and PlayerSeasonScoring
data. No database fixtures - these functions operate on in-memory
sequences and mappings. Integration with `load_all_auction_picks` and
`load_player_season_scoring` is covered by the existing
`test_auction_draft_angles_v1.py` test surface.

Includes a regression test against the Cavallini/Mahomes 2018 anchor
(franchise 0002, player 9988, $62, QB) per A2 spec section 4.5 / Step 1
section 4.5 - the anchor must surface as the QB-position record under
`compute_auction_most_expensive_v1`.
"""
from __future__ import annotations

import pytest

from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    AuctionPick,
    PlayerSeasonScoring,
)
from squadvault.core.recaps.context.draft_history_vault_aggregations_v1 import (
    BargainEntry,
    BustEntry,
    MostExpensivePick,
    MostExpensiveResult,
    compute_auction_bargain_hall_v1,
    compute_auction_bust_hall_v1,
    compute_auction_most_expensive_v1,
)

# -- Helpers for synthetic data --------------------------------------


def _pick(
    *,
    season: int,
    franchise_id: str = "F1",
    player_id: str = "P1",
    bid: float = 10.0,
    position: str = "RB",
) -> AuctionPick:
    """Build an AuctionPick with sensible defaults for tests."""
    return AuctionPick(
        season=season,
        franchise_id=franchise_id,
        player_id=player_id,
        bid_amount=bid,
        position=position,
    )


def _score(
    *,
    season: int,
    franchise_id: str = "F1",
    player_id: str = "P1",
    total: float = 100.0,
    weeks: int = 14,
    starters: int | None = None,
) -> PlayerSeasonScoring:
    """Build a PlayerSeasonScoring with sensible defaults."""
    return PlayerSeasonScoring(
        season=season,
        franchise_id=franchise_id,
        player_id=player_id,
        total_points=total,
        weeks_played=weeks,
        starter_weeks=starters if starters is not None else weeks,
    )


# -- compute_auction_most_expensive_v1 -------------------------------


class TestComputeAuctionMostExpensiveV1:
    """A2 spec section 3.1 and section 3.8 sub-shape."""

    def test_empty_picks_returns_empty_result(self):
        result = compute_auction_most_expensive_v1([])
        assert result == MostExpensiveResult(overall=None, per_position=())

    def test_zero_bid_picks_excluded(self):
        # The loader pre-filters, but the aggregation defensively also.
        # Construct a synthetic zero-bid pick to confirm exclusion.
        # AuctionPick is frozen so we have to construct it directly.
        zero_pick = AuctionPick(
            season=2020, franchise_id="F1", player_id="P1",
            bid_amount=0.0, position="RB",
        )
        result = compute_auction_most_expensive_v1([zero_pick])
        assert result.overall is None
        assert result.per_position == ()

    def test_single_pick_is_overall_and_per_position(self):
        pick = _pick(season=2020, bid=50.0, position="QB")
        result = compute_auction_most_expensive_v1([pick])
        assert result.overall is not None
        assert result.overall.bid_amount == 50.0
        assert result.overall.player_id == "P1"
        assert len(result.per_position) == 1
        assert result.per_position[0].position == "QB"
        assert result.per_position[0].bid_amount == 50.0

    def test_overall_is_max_bid_across_all_positions(self):
        picks = [
            _pick(season=2020, player_id="qb_top", bid=80.0, position="QB"),
            _pick(season=2020, player_id="rb_top", bid=70.0, position="RB"),
            _pick(season=2020, player_id="wr_top", bid=60.0, position="WR"),
        ]
        result = compute_auction_most_expensive_v1(picks)
        assert result.overall is not None
        assert result.overall.player_id == "qb_top"
        assert result.overall.bid_amount == 80.0

    def test_per_position_records_sorted_by_position_ascending(self):
        picks = [
            _pick(season=2020, player_id="wr_top", bid=50.0, position="WR"),
            _pick(season=2020, player_id="qb_top", bid=80.0, position="QB"),
            _pick(season=2020, player_id="rb_top", bid=70.0, position="RB"),
        ]
        result = compute_auction_most_expensive_v1(picks)
        positions = [r.position for r in result.per_position]
        assert positions == ["QB", "RB", "WR"]  # sorted ascending

    def test_per_position_excludes_picks_without_position(self):
        picks = [
            _pick(season=2020, player_id="no_pos", bid=100.0, position=""),
            _pick(season=2020, player_id="rb_top", bid=50.0, position="RB"),
        ]
        result = compute_auction_most_expensive_v1(picks)
        # Overall record is the highest bid - the no-position pick.
        assert result.overall is not None
        assert result.overall.player_id == "no_pos"
        assert result.overall.bid_amount == 100.0
        # Per-position records exclude the empty-position pick.
        assert len(result.per_position) == 1
        assert result.per_position[0].position == "RB"
        assert result.per_position[0].player_id == "rb_top"

    def test_top_1_per_position_when_multiple_picks_share_position(self):
        picks = [
            _pick(season=2018, player_id="rb_low", bid=20.0, position="RB"),
            _pick(season=2020, player_id="rb_high", bid=80.0, position="RB"),
            _pick(season=2022, player_id="rb_mid", bid=50.0, position="RB"),
        ]
        result = compute_auction_most_expensive_v1(picks)
        assert len(result.per_position) == 1
        assert result.per_position[0].player_id == "rb_high"
        assert result.per_position[0].bid_amount == 80.0
        assert result.per_position[0].season == 2020

    def test_tie_break_prefers_earlier_season(self):
        # Same bid, different seasons - earlier season wins per
        # tie-break rule (season ascending after bid descending).
        picks = [
            _pick(season=2022, player_id="P1", bid=60.0, position="QB"),
            _pick(season=2018, player_id="P2", bid=60.0, position="QB"),
            _pick(season=2020, player_id="P3", bid=60.0, position="QB"),
        ]
        result = compute_auction_most_expensive_v1(picks)
        assert result.overall is not None
        assert result.overall.season == 2018
        assert len(result.per_position) == 1
        assert result.per_position[0].season == 2018

    def test_determinism_identical_inputs_produce_identical_outputs(self):
        picks = [
            _pick(season=2020, franchise_id="F1", player_id="P1",
                   bid=80.0, position="QB"),
            _pick(season=2020, franchise_id="F2", player_id="P2",
                   bid=70.0, position="RB"),
            _pick(season=2020, franchise_id="F3", player_id="P3",
                   bid=60.0, position="WR"),
        ]
        a = compute_auction_most_expensive_v1(picks)
        b = compute_auction_most_expensive_v1(picks)
        assert a == b
        # Reordering inputs must not change output.
        c = compute_auction_most_expensive_v1(list(reversed(picks)))
        assert a == c

    def test_cavallini_mahomes_2018_qb_anchor_regression(self):
        """A2 spec section 4.5 / Step 1 section 4.5 anchor.

        The Italian Cavallini / Mahomes 2018 pick (franchise 0002,
        player 9988, $62, QB) must surface as the QB-position
        record under appropriate substrate state. This test
        validates the derivation against a substrate-fragment
        synthesized to match the empirically-confirmed historical
        facts: $62 is the highest QB bid in the substrate when
        all other 2018+ QB picks are lower-bid.

        Per the anti-drift discipline in the session brief: the
        Cavallini anchor is a TEST TARGET, not a hardcode. The
        derivation surfaces it; the test validates the derivation.
        """
        picks = [
            # The anchor pick.
            AuctionPick(
                season=2018, franchise_id="0002", player_id="9988",
                bid_amount=62.0, position="QB",
            ),
            # Other QB picks across seasons, all lower-bid.
            AuctionPick(
                season=2019, franchise_id="0003", player_id="qb_a",
                bid_amount=45.0, position="QB",
            ),
            AuctionPick(
                season=2020, franchise_id="0004", player_id="qb_b",
                bid_amount=55.0, position="QB",
            ),
            AuctionPick(
                season=2022, franchise_id="0005", player_id="qb_c",
                bid_amount=50.0, position="QB",
            ),
            # A higher non-QB pick - tests that QB-position record
            # is computed independently of the overall record.
            AuctionPick(
                season=2023, franchise_id="0006", player_id="rb_top",
                bid_amount=75.0, position="RB",
            ),
        ]
        result = compute_auction_most_expensive_v1(picks)

        # Overall record is the RB at $75, not the QB at $62.
        assert result.overall is not None
        assert result.overall.player_id == "rb_top"
        assert result.overall.bid_amount == 75.0

        # The QB-position record is the Cavallini anchor.
        qb_records = [r for r in result.per_position if r.position == "QB"]
        assert len(qb_records) == 1
        qb_record = qb_records[0]
        assert qb_record.season == 2018
        assert qb_record.franchise_id == "0002"
        assert qb_record.player_id == "9988"
        assert qb_record.bid_amount == 62.0


# -- compute_auction_bust_hall_v1 ------------------------------------


class TestComputeAuctionBustHallV1:
    """A2 spec section 3.1 Auction-Bust Hall sub-shape."""

    def test_empty_picks_returns_empty_tuple(self):
        result = compute_auction_bust_hall_v1([], {})
        assert result == ()

    def test_no_scoring_entries_returns_empty(self):
        picks = [_pick(season=2020, bid=80.0)]
        result = compute_auction_bust_hall_v1(picks, {})
        assert result == ()

    def test_top_n_zero_returns_empty(self):
        picks = [_pick(season=2020, bid=80.0)]
        scoring = {(2020, "F1", "P1"): _score(season=2020, total=10.0, weeks=14)}
        # Add some baseline starters so league_avg is defined.
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=150.0, weeks=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring, top_n=0)
        assert result == ()

    def test_negative_top_n_raises(self):
        with pytest.raises(ValueError, match="top_n must be non-negative"):
            compute_auction_bust_hall_v1([], {}, top_n=-1)

    def test_pick_below_min_starter_weeks_excluded(self):
        picks = [_pick(season=2020, bid=80.0)]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, total=10.0, weeks=3, starters=3,
            ),
        }
        # Add baseline starters with more weeks so they satisfy the
        # starters > 0 filter for league_avg computation.
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=150.0, weeks=14, starters=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring, min_starter_weeks=4)
        assert result == ()

    def test_pick_above_threshold_excluded(self):
        # player_avg = 100/10 = 10.0; league_avg = 150/14 ~= 10.71;
        # threshold = 10.71 * 0.5 ~= 5.36. player_avg > threshold, so excluded.
        picks = [_pick(season=2020, bid=80.0)]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, total=100.0, weeks=10, starters=10,
            ),
        }
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=150.0, weeks=14, starters=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring)
        assert result == ()

    def test_pick_below_threshold_with_high_bid_surfaces_as_bust(self):
        # Match D22's league_avg: mean across all starter entries
        # INCLUDING the bust pick itself.
        # 5 starters at 150/14 = 10.71; 1 bust at 20/8 = 2.5.
        # league_avg = (5 * 10.71 + 2.5) / 6 ~= 9.345.
        # threshold = 9.345 * 0.5 ~= 4.67. player_avg = 2.5 < 4.67.
        # severity = (9.345 - 2.5) * 80 ~= 547.6.
        picks = [_pick(season=2020, bid=80.0, player_id="bust_pick")]
        scoring = {
            (2020, "F1", "bust_pick"): _score(
                season=2020, player_id="bust_pick",
                total=20.0, weeks=8, starters=8,
            ),
        }
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=150.0, weeks=14, starters=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring)
        assert len(result) == 1
        entry = result[0]
        assert entry.player_id == "bust_pick"
        assert entry.bid_amount == 80.0
        assert entry.player_avg == 2.5
        assert entry.starter_weeks == 8
        # severity ~ 547.6, exact value depends on league_avg.
        assert 500.0 < entry.severity_signal < 600.0

    def test_cross_season_aggregation_separate_league_avgs(self):
        # Two seasons with different league averages; same player_avg
        # but different bid amounts should rank by severity correctly.
        picks = [
            _pick(season=2020, franchise_id="F1", player_id="A",
                   bid=60.0, position="RB"),
            _pick(season=2022, franchise_id="F2", player_id="B",
                   bid=80.0, position="RB"),
        ]
        scoring = {
            (2020, "F1", "A"): _score(
                season=2020, franchise_id="F1", player_id="A",
                total=20.0, weeks=10, starters=10,
            ),
            (2022, "F2", "B"): _score(
                season=2022, franchise_id="F2", player_id="B",
                total=20.0, weeks=10, starters=10,
            ),
        }
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=140.0, weeks=14, starters=14,
            )
            scoring[(2022, f"O{i}", f"O{i}_P")] = _score(
                season=2022, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=140.0, weeks=14, starters=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring)
        # Both qualify; higher bid (B at $80) has higher severity.
        assert len(result) == 2
        assert result[0].player_id == "B"
        assert result[1].player_id == "A"

    def test_top_n_caps_output(self):
        picks = []
        scoring = {}
        for i in range(10):
            pid = f"bust_{i}"
            picks.append(_pick(
                season=2020, franchise_id="F1", player_id=pid, bid=80.0 - i,
            ))
            scoring[(2020, "F1", pid)] = _score(
                season=2020, franchise_id="F1", player_id=pid,
                total=20.0, weeks=10, starters=10,
            )
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=150.0, weeks=14, starters=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring, top_n=3)
        assert len(result) == 3

    def test_severity_ordering_deterministic(self):
        # Construct three picks with strictly decreasing severity.
        picks = [
            _pick(season=2020, franchise_id="FA", player_id="A", bid=60.0),
            _pick(season=2020, franchise_id="FB", player_id="B", bid=80.0),
            _pick(season=2020, franchise_id="FC", player_id="C", bid=40.0),
        ]
        scoring = {
            (2020, "FA", "A"): _score(
                season=2020, franchise_id="FA", player_id="A",
                total=20.0, weeks=10, starters=10,
            ),
            (2020, "FB", "B"): _score(
                season=2020, franchise_id="FB", player_id="B",
                total=20.0, weeks=10, starters=10,
            ),
            (2020, "FC", "C"): _score(
                season=2020, franchise_id="FC", player_id="C",
                total=20.0, weeks=10, starters=10,
            ),
        }
        for i in range(5):
            scoring[(2020, f"O{i}", f"O{i}_P")] = _score(
                season=2020, franchise_id=f"O{i}", player_id=f"O{i}_P",
                total=150.0, weeks=14, starters=14,
            )
        result = compute_auction_bust_hall_v1(picks, scoring)
        assert [r.player_id for r in result] == ["B", "A", "C"]

    def test_determinism_identical_inputs_produce_identical_outputs(self):
        picks = [
            _pick(season=2020, franchise_id="F1", player_id="P1", bid=60.0),
            _pick(season=2022, franchise_id="F2", player_id="P2", bid=70.0),
        ]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, franchise_id="F1", player_id="P1",
                total=20.0, weeks=8, starters=8,
            ),
            (2022, "F2", "P2"): _score(
                season=2022, franchise_id="F2", player_id="P2",
                total=15.0, weeks=8, starters=8,
            ),
        }
        for s in (2020, 2022):
            for i in range(5):
                scoring[(s, f"O{i}", f"O{i}_P")] = _score(
                    season=s, franchise_id=f"O{i}", player_id=f"O{i}_P",
                    total=150.0, weeks=14, starters=14,
                )
        a = compute_auction_bust_hall_v1(picks, scoring)
        b = compute_auction_bust_hall_v1(picks, scoring)
        assert a == b


# -- compute_auction_bargain_hall_v1 ---------------------------------


class TestComputeAuctionBargainHallV1:
    """A2 spec section 3.1 Auction-Bargain Hall sub-shape."""

    def test_empty_picks_returns_empty_tuple(self):
        result = compute_auction_bargain_hall_v1([], {})
        assert result == ()

    def test_no_scoring_entries_returns_empty(self):
        picks = [_pick(season=2020, bid=10.0)]
        result = compute_auction_bargain_hall_v1(picks, {})
        assert result == ()

    def test_below_min_points_excluded(self):
        picks = [_pick(season=2020, bid=1.0)]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, total=49.0, weeks=14, starters=14,
            ),
        }
        result = compute_auction_bargain_hall_v1(picks, scoring, min_points=50)
        assert result == ()

    def test_at_min_points_threshold_included(self):
        picks = [_pick(season=2020, bid=1.0)]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, total=50.0, weeks=14, starters=14,
            ),
        }
        result = compute_auction_bargain_hall_v1(picks, scoring, min_points=50)
        assert len(result) == 1
        assert result[0].dollar_per_point == pytest.approx(0.02)

    def test_dollar_zero_total_points_filtered_defensively(self):
        # Construct a synthetic 0-points entry that passes min_points=0
        # threshold but would otherwise cause ZeroDivisionError.
        picks = [_pick(season=2020, bid=1.0)]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, total=0.0, weeks=14, starters=0,
            ),
        }
        result = compute_auction_bargain_hall_v1(
            picks, scoring, min_points=0,
        )
        # Pick is excluded by the defensive total_points > 0 check.
        assert result == ()

    def test_negative_top_n_raises(self):
        with pytest.raises(ValueError, match="top_n must be non-negative"):
            compute_auction_bargain_hall_v1([], {}, top_n=-1)

    def test_top_n_zero_returns_empty(self):
        picks = [_pick(season=2020, bid=1.0)]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, total=100.0, weeks=14, starters=14,
            ),
        }
        result = compute_auction_bargain_hall_v1(picks, scoring, top_n=0)
        assert result == ()

    def test_lowest_dollar_per_point_ranks_first(self):
        picks = [
            _pick(season=2020, franchise_id="FA", player_id="A", bid=10.0),
            _pick(season=2020, franchise_id="FB", player_id="B", bid=2.0),
            _pick(season=2020, franchise_id="FC", player_id="C", bid=5.0),
        ]
        scoring = {
            (2020, "FA", "A"): _score(
                season=2020, franchise_id="FA", player_id="A",
                total=100.0, weeks=14, starters=14,
            ),  # 0.10
            (2020, "FB", "B"): _score(
                season=2020, franchise_id="FB", player_id="B",
                total=100.0, weeks=14, starters=14,
            ),  # 0.02 - best
            (2020, "FC", "C"): _score(
                season=2020, franchise_id="FC", player_id="C",
                total=100.0, weeks=14, starters=14,
            ),  # 0.05
        }
        result = compute_auction_bargain_hall_v1(picks, scoring)
        assert [r.player_id for r in result] == ["B", "C", "A"]

    def test_tie_break_prefers_higher_total_points(self):
        # Same dollar_per_point ratio (0.10), different total_points.
        picks = [
            _pick(season=2020, franchise_id="FA", player_id="lo", bid=5.0),
            _pick(season=2020, franchise_id="FB", player_id="hi", bid=20.0),
        ]
        scoring = {
            (2020, "FA", "lo"): _score(
                season=2020, franchise_id="FA", player_id="lo",
                total=50.0, weeks=14, starters=14,
            ),
            (2020, "FB", "hi"): _score(
                season=2020, franchise_id="FB", player_id="hi",
                total=200.0, weeks=14, starters=14,
            ),
        }
        result = compute_auction_bargain_hall_v1(picks, scoring)
        # Both ratios are 0.10; tie-break: higher total_points first.
        assert result[0].player_id == "hi"
        assert result[1].player_id == "lo"

    def test_top_n_caps_output(self):
        picks = []
        scoring = {}
        for i in range(10):
            pid = f"bargain_{i}"
            picks.append(_pick(
                season=2020, franchise_id="F1", player_id=pid,
                bid=1.0 + i * 0.1,
            ))
            scoring[(2020, "F1", pid)] = _score(
                season=2020, franchise_id="F1", player_id=pid,
                total=100.0, weeks=14, starters=14,
            )
        result = compute_auction_bargain_hall_v1(picks, scoring, top_n=3)
        assert len(result) == 3
        # First three have lowest bids - bargain_0, bargain_1, bargain_2.
        assert [r.player_id for r in result] == [
            "bargain_0", "bargain_1", "bargain_2",
        ]

    def test_cross_season_aggregation(self):
        picks = [
            _pick(season=2018, franchise_id="F1", player_id="A", bid=1.0),
            _pick(season=2020, franchise_id="F2", player_id="B", bid=2.0),
            _pick(season=2022, franchise_id="F3", player_id="C", bid=1.0),
        ]
        scoring = {
            (2018, "F1", "A"): _score(
                season=2018, franchise_id="F1", player_id="A",
                total=200.0, weeks=14, starters=14,
            ),  # 0.005
            (2020, "F2", "B"): _score(
                season=2020, franchise_id="F2", player_id="B",
                total=100.0, weeks=14, starters=14,
            ),  # 0.02
            (2022, "F3", "C"): _score(
                season=2022, franchise_id="F3", player_id="C",
                total=300.0, weeks=14, starters=14,
            ),  # 0.0033
        }
        result = compute_auction_bargain_hall_v1(picks, scoring)
        # Cross-season correct ordering.
        assert [r.player_id for r in result] == ["C", "A", "B"]

    def test_determinism_identical_inputs_produce_identical_outputs(self):
        picks = [
            _pick(season=2020, franchise_id="F1", player_id="P1", bid=3.0),
            _pick(season=2022, franchise_id="F2", player_id="P2", bid=5.0),
        ]
        scoring = {
            (2020, "F1", "P1"): _score(
                season=2020, franchise_id="F1", player_id="P1",
                total=100.0, weeks=14, starters=14,
            ),
            (2022, "F2", "P2"): _score(
                season=2022, franchise_id="F2", player_id="P2",
                total=150.0, weeks=14, starters=14,
            ),
        }
        a = compute_auction_bargain_hall_v1(picks, scoring)
        b = compute_auction_bargain_hall_v1(picks, scoring)
        assert a == b


# -- Module-level invariants -----------------------------------------


class TestDataclassInvariants:
    """Frozen-dataclass behavior."""

    def test_most_expensive_pick_is_frozen(self):
        pick = MostExpensivePick(
            season=2020, franchise_id="F1", player_id="P1",
            bid_amount=50.0, position="RB",
        )
        with pytest.raises((AttributeError, Exception)):
            pick.bid_amount = 99.0  # type: ignore[misc]

    def test_bust_entry_is_frozen(self):
        entry = BustEntry(
            season=2020, franchise_id="F1", player_id="P1",
            bid_amount=80.0, player_avg=2.0, league_starter_avg=10.0,
            starter_weeks=8, severity_signal=640.0,
        )
        with pytest.raises((AttributeError, Exception)):
            entry.severity_signal = 999.0  # type: ignore[misc]

    def test_bargain_entry_is_frozen(self):
        entry = BargainEntry(
            season=2020, franchise_id="F1", player_id="P1",
            bid_amount=1.0, total_points=100.0, dollar_per_point=0.01,
        )
        with pytest.raises((AttributeError, Exception)):
            entry.dollar_per_point = 99.0  # type: ignore[misc]
