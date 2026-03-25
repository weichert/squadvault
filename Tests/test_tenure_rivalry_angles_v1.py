"""Tests for tenure-aware rivalry angle detection.

Verifies that rivalry angles only count matchups from the current
owner's tenure, not the full franchise slot history.
"""
from __future__ import annotations

import pytest


class TestTenureAwareRivalry:
    """Rivalry angles must filter by franchise tenure."""

    def test_filters_matchups_to_tenure(self):
        """When one franchise is new, only count meetings since they joined."""
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
            LeagueHistoryContextV1,
        )
        from squadvault.core.recaps.context.narrative_angles_v1 import _detect_rivalry_angles
        from squadvault.core.recaps.context.season_context_v1 import (
            SeasonContextV1, TeamRecord, WeekMatchupContext,
        )

        # 13 matchups from 2010-2022 (old ownership) — 0003 always wins
        old_matchups = [
            HistoricalMatchup(
                season=y, week=1,
                winner_id="0003", loser_id="0009",
                winner_score=100.0, loser_score=90.0,
                is_tie=False, margin=10.0,
            )
            for y in range(2010, 2023)
        ]
        # 2 matchups from 2023-2024 (new ownership) — split 1-1
        new_matchups = [
            HistoricalMatchup(
                season=2023, week=1,
                winner_id="0003", loser_id="0009",
                winner_score=110.0, loser_score=90.0,
                is_tie=False, margin=20.0,
            ),
            HistoricalMatchup(
                season=2024, week=5,
                winner_id="0009", loser_id="0003",
                winner_score=105.0, loser_score=100.0,
                is_tie=False, margin=5.0,
            ),
        ]
        all_matchups = old_matchups + new_matchups

        # Build minimal season context with a week 13 matchup
        tr_w = TeamRecord(
            franchise_id="0003", wins=7, losses=6, ties=0,
            points_for=1400.0, points_against=1300.0, current_streak=3,
        )
        tr_l = TeamRecord(
            franchise_id="0009", wins=5, losses=8, ties=0,
            points_for=1200.0, points_against=1350.0, current_streak=-2,
        )
        wm = WeekMatchupContext(
            winner_id="0003", loser_id="0009",
            winner_score=120.0, loser_score=95.0,
            margin=25.0, is_tie=False,
            winner_record_after=tr_w, loser_record_after=tr_l,
        )
        season_ctx = SeasonContextV1(
            league_id="70985",
            season=2024,
            through_week=13,
            standings=(tr_w, tr_l),
            week_matchups=(wm,),
            week_high_scorer=("0003", 120.0),
            week_low_scorer=("0009", 95.0),
            week_closest_game=None,
            week_biggest_blowout=("0003", "0009", 25.0),
            season_high=None,
            season_low=None,
            season_avg_score=None,
            total_matchups_through_week=65,
            matchups_this_week=1,
        )
        history_ctx = LeagueHistoryContextV1(
            league_id="70985",
            seasons_available=tuple(range(2010, 2025)),
            total_matchups_all_time=len(all_matchups),
            all_time_records=(),
            all_time_high=None, all_time_low=None, all_time_avg_score=None,
            longest_win_streak=None, longest_loss_streak=None,
            best_season_record=None, worst_season_record=None,
        )

        # Tenure map: 0003 changed name in 2023, 0009 has been around since 2010
        tenure_map = {"0003": 2023, "0009": 2010}

        # WITH tenure: only 2 meetings since 2023 (1-1 record).
        # Should NOT produce a dominance angle.
        angles = _detect_rivalry_angles(season_ctx, history_ctx, all_matchups, tenure_map)
        dominance = [a for a in angles if "leads" in a.headline]
        assert not dominance, (
            f"Should not claim dominance with only 2 tenure-period meetings: {dominance}"
        )

        # WITHOUT tenure: all 15 meetings show 14-1 dominance.
        # Should produce a dominance angle.
        angles_no_tenure = _detect_rivalry_angles(season_ctx, history_ctx, all_matchups, None)
        dominance_no_tenure = [a for a in angles_no_tenure if "leads" in a.headline]
        assert len(dominance_no_tenure) > 0, (
            "Without tenure filtering, old dominance should be detected"
        )

    def test_long_tenure_uses_all_time(self):
        """When both franchises have full tenure, use all-time label."""
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
            LeagueHistoryContextV1,
        )
        from squadvault.core.recaps.context.narrative_angles_v1 import _detect_rivalry_angles
        from squadvault.core.recaps.context.season_context_v1 import (
            SeasonContextV1, TeamRecord, WeekMatchupContext,
        )

        # 10 matchups, all won by 0001
        matchups = [
            HistoricalMatchup(
                season=2015 + i, week=1,
                winner_id="0001", loser_id="0002",
                winner_score=100.0, loser_score=90.0,
                is_tie=False, margin=10.0,
            )
            for i in range(10)
        ]

        tr_w = TeamRecord(
            franchise_id="0001", wins=10, losses=3, ties=0,
            points_for=1400.0, points_against=1200.0, current_streak=5,
        )
        tr_l = TeamRecord(
            franchise_id="0002", wins=6, losses=7, ties=0,
            points_for=1200.0, points_against=1300.0, current_streak=-1,
        )
        wm = WeekMatchupContext(
            winner_id="0001", loser_id="0002",
            winner_score=110.0, loser_score=90.0,
            margin=20.0, is_tie=False,
            winner_record_after=tr_w, loser_record_after=tr_l,
        )
        season_ctx = SeasonContextV1(
            league_id="70985", season=2024, through_week=8,
            standings=(tr_w, tr_l), week_matchups=(wm,),
            week_high_scorer=("0001", 110.0), week_low_scorer=("0002", 90.0),
            week_closest_game=None, week_biggest_blowout=("0001", "0002", 20.0),
            season_high=None, season_low=None, season_avg_score=None,
            total_matchups_through_week=40, matchups_this_week=1,
        )
        history_ctx = LeagueHistoryContextV1(
            league_id="70985",
            seasons_available=tuple(range(2015, 2025)),
            total_matchups_all_time=len(matchups),
            all_time_records=(), all_time_high=None, all_time_low=None,
            all_time_avg_score=None, longest_win_streak=None,
            longest_loss_streak=None, best_season_record=None,
            worst_season_record=None,
        )

        # Both franchises have full tenure
        tenure_map = {"0001": 2015, "0002": 2015}

        angles = _detect_rivalry_angles(season_ctx, history_ctx, matchups, tenure_map)
        dominance = [a for a in angles if "leads" in a.headline]
        assert len(dominance) == 1
        assert "all-time" in dominance[0].headline
