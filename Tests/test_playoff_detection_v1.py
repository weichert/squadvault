"""Tests for playoff detection in season context derivation.

The playoff detector works purely from matchup count progression:
- Regular season: consistent matchup count (N/2 for N teams)
- Playoffs: matchup count drops (8 teams -> 4 -> 2 -> 1)

No configuration needed — works for any league size and any
week-number boundary (handles NFL 2021 schedule expansion).
"""

from squadvault.core.recaps.context.season_context_v1 import (
    MatchupResult,
    PlayoffInfo,
    _detect_playoff_info,
    render_season_context_for_prompt,
    derive_season_context_v1,
)


def _matchup(week: int, winner: str, loser: str,
             w_score: float = 100.0, l_score: float = 90.0) -> MatchupResult:
    """Helper to create a matchup result."""
    return MatchupResult(
        week=week,
        winner_id=winner,
        loser_id=loser,
        winner_score=w_score,
        loser_score=l_score,
        is_tie=False,
        margin=w_score - l_score,
    )


class TestPlayoffDetection:
    """Test _detect_playoff_info with 10-team league (5 matchups/week)."""

    def _build_season(self):
        """Build a 10-team, 14-week regular season + 3-week playoff."""
        matchups = []
        teams = [("A", "B"), ("C", "D"), ("E", "F"), ("G", "H"), ("I", "J")]

        # Regular season: weeks 1-14, 5 matchups each
        for w in range(1, 15):
            for winner, loser in teams:
                matchups.append(_matchup(w, winner, loser))

        # Playoffs:
        # Week 15: quarterfinals — 4 matchups (8 teams)
        for winner, loser in [("A", "B"), ("C", "D"), ("E", "F"), ("G", "H")]:
            matchups.append(_matchup(15, winner, loser))

        # Week 16: semifinals — 2 matchups (4 teams)
        for winner, loser in [("A", "C"), ("E", "G")]:
            matchups.append(_matchup(16, winner, loser))

        # Week 17: championship — 1 matchup (2 teams)
        matchups.append(_matchup(17, "A", "E"))

        return matchups

    def test_regular_season_not_playoff(self):
        matchups = self._build_season()
        info = _detect_playoff_info(matchups, week_index=10)
        assert info is not None
        assert info.is_playoff is False
        assert info.regular_season_matchup_count == 5
        assert info.last_regular_season_week == 14

    def test_last_regular_season_week(self):
        matchups = self._build_season()
        info = _detect_playoff_info(matchups, week_index=14)
        assert info is not None
        assert info.is_playoff is False

    def test_quarterfinal_detected(self):
        matchups = self._build_season()
        info = _detect_playoff_info(matchups, week_index=15)
        assert info is not None
        assert info.is_playoff is True
        assert info.playoff_round == "QUARTERFINAL"
        assert info.playoff_round_label == "Quarterfinal"
        assert info.teams_remaining == 8
        assert info.last_regular_season_week == 14

    def test_semifinal_detected(self):
        matchups = self._build_season()
        info = _detect_playoff_info(matchups, week_index=16)
        assert info is not None
        assert info.is_playoff is True
        assert info.playoff_round == "SEMIFINAL"
        assert info.teams_remaining == 4

    def test_championship_detected(self):
        matchups = self._build_season()
        info = _detect_playoff_info(matchups, week_index=17)
        assert info is not None
        assert info.is_playoff is True
        assert info.playoff_round == "CHAMPIONSHIP"
        assert info.playoff_round_label == "Championship"
        assert info.teams_remaining == 2

    def test_empty_matchups(self):
        info = _detect_playoff_info([], week_index=1)
        assert info is None

    def test_week_with_no_matchups_beyond_season(self):
        """Week 18 with zero matchups — not in data at all."""
        matchups = self._build_season()
        # week_index=18 has zero matchups in the data
        info = _detect_playoff_info(matchups, week_index=18)
        assert info is not None
        # 0 matchups, week > last regular = playoff territory
        assert info.is_playoff is True
        assert info.teams_remaining == 0


class TestPlayoffAwareRendering:
    """Test that render_season_context_for_prompt includes playoff context."""

    def test_regular_season_no_playoff_header(self):
        """Regular season weeks should NOT show playoff header."""
        from squadvault.core.recaps.context.season_context_v1 import SeasonContextV1, TeamRecord
        ctx = SeasonContextV1(
            league_id="test",
            season=2024,
            through_week=10,
            standings=(
                TeamRecord("A", 8, 2, 0, 1000.0, 900.0, 3),
            ),
            week_matchups=(),
            week_high_scorer=None,
            week_low_scorer=None,
            week_closest_game=None,
            week_biggest_blowout=None,
            season_high=None,
            season_low=None,
            season_avg_score=None,
            total_matchups_through_week=50,
            matchups_this_week=5,
            playoff_info=PlayoffInfo(
                is_playoff=False,
                playoff_round=None,
                playoff_round_label=None,
                regular_season_matchup_count=5,
                last_regular_season_week=14,
                teams_remaining=None,
            ),
        )
        text = render_season_context_for_prompt(ctx)
        assert "PLAYOFF" not in text
        assert "Season standings through Week 10:" in text

    def test_playoff_week_has_header(self):
        """Playoff weeks should show explicit playoff header."""
        from squadvault.core.recaps.context.season_context_v1 import SeasonContextV1, TeamRecord
        ctx = SeasonContextV1(
            league_id="test",
            season=2024,
            through_week=17,
            standings=(
                TeamRecord("A", 12, 2, 0, 1500.0, 1000.0, 5),
            ),
            week_matchups=(),
            week_high_scorer=None,
            week_low_scorer=None,
            week_closest_game=None,
            week_biggest_blowout=None,
            season_high=None,
            season_low=None,
            season_avg_score=None,
            total_matchups_through_week=80,
            matchups_this_week=1,
            playoff_info=PlayoffInfo(
                is_playoff=True,
                playoff_round="CHAMPIONSHIP",
                playoff_round_label="Championship",
                regular_season_matchup_count=5,
                last_regular_season_week=14,
                teams_remaining=2,
            ),
        )
        text = render_season_context_for_prompt(ctx)
        assert "WEEK TYPE: PLAYOFF" in text
        assert "CHAMPIONSHIP" in text
        assert "ELIMINATED" in text
        assert "Final regular season standings" in text
        assert "through Week 14" in text
