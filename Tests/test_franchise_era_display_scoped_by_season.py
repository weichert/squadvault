"""Regression test: franchise era-mapping fix.

Verifies that render_championship_roll_markdown attributes historical
results to the name that existed in that season, not the current
occupant of the franchise slot. Covers the specific case that triggered
the fix: slot 0010 was SS Express in 2016 and Brandon Knows Ball from
2023 onward.
"""
from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    ChampionshipResult,
)
from squadvault.core.recaps.render.hall_of_fame_render_v1 import (
    render_championship_roll_markdown,
)


class TestFranchiseEraMapping:
    """Regression: season-scoped name resolution for franchise slots."""

    def test_2016_champion_is_ss_express_not_brandon(self):
        """Slot 0010 was SS Express in 2016; Brandon Knows Ball from 2023.

        Before the fix, build_cross_season_name_resolver returned the
        most-recent name (Brandon Knows Ball) for slot 0010, causing
        the 2016 championship to be attributed to Brandon Knows Ball.
        """
        results = [
            ChampionshipResult(
                season=2016,
                champion_id="0010",
                runner_up_id="0005",
                championship_week=16,
                champion_score=107.0,
                runner_up_score=100.0,
                is_tie=False,
            ),
        ]
        # Season-scoped map: slot 0010 in 2016 was SS Express
        season_map = {
            ("0010", 2016): "SS Express",
            ("0005", 2016): "Weichert's Warmongers",
        }
        md = render_championship_roll_markdown(results, season_map)

        assert "SS Express" in md, "2016 champion must be SS Express"
        assert "Brandon Knows Ball" not in md, (
            "Brandon Knows Ball must not appear — he was not in the league in 2016"
        )
        assert "107.00 to 100.00" in md

    def test_era_change_same_slot_different_names(self):
        """Two eras of slot 0010: SS Express wins 2016, Brandon wins 2023+.

        The titles-by-franchise section must show them as separate rows
        with correct title counts.
        """
        results = [
            ChampionshipResult(
                season=2016,
                champion_id="0010",
                runner_up_id="0005",
                championship_week=16,
                champion_score=107.0,
                runner_up_score=100.0,
                is_tie=False,
            ),
            ChampionshipResult(
                season=2025,
                champion_id="0002",
                runner_up_id="0005",
                championship_week=18,
                champion_score=139.4,
                runner_up_score=118.65,
                is_tie=False,
            ),
        ]
        season_map = {
            ("0010", 2016): "SS Express",
            ("0005", 2016): "Weichert's Warmongers",
            ("0002", 2025): "Paradis' Playmakers",
            ("0005", 2025): "Weichert's Warmongers",
            # Slot 0010 in 2025 era would be Brandon Knows Ball
            ("0010", 2025): "Brandon Knows Ball",
        }
        md = render_championship_roll_markdown(results, season_map)

        titles_section = md[md.index("Titles by Franchise"):]
        # SS Express appears with 1 title in 2016
        assert "SS Express" in titles_section
        ss_line = next(
            line for line in titles_section.splitlines()
            if line.startswith("| SS Express |")
        )
        assert "| 1 |" in ss_line
        assert "2016" in ss_line
        # Brandon Knows Ball must not appear in titles section
        assert "Brandon Knows Ball" not in titles_section
