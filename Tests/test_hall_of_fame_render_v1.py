"""Tests for Hall of Fame & Shame Render v1 (A1 surface rendering).

Pure unit tests against synthetic aggregation outputs. No database
fixtures; no file I/O. Tests verify markdown structure, scope-
declaration invariant, column presence, ordering, and edge cases.

Integration of these render functions with `load_all_matchups` and
the canonical event ledger lives in
`scripts/generate_hall_of_fame_archive.py`; the script's behavior is
exercised by the layout-invariant test
(`test_hall_of_fame_archive_layout_v1.py`) once the archive exists.
"""
from __future__ import annotations

import pytest

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    ChampionshipResult,
)
from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    SeasonRecord,
)
from squadvault.core.recaps.render.hall_of_fame_render_v1 import (
    FORMAT_SHIFT_FOOTNOTE,
    SCOPE_DECLARATION_LINE,
    TITLE_BLOWOUTS_HALL,
    TITLE_CHAMPIONSHIP_ROLL,
    TITLE_INDEX,
    TITLE_WORST_SEASONS,
    render_blowouts_hall_markdown,
    render_championship_roll_markdown,
    render_index_markdown,
    render_worst_seasons_markdown,
)

# ── Test helpers ─────────────────────────────────────────────────────


def _name_map(**kwargs: str) -> dict[str, str]:
    """Convenience builder: dict of franchise_id → display name."""
    return dict(kwargs)


# ── Module-level invariants ──────────────────────────────────────────


class TestModuleConstants:
    """Tests for the load-bearing module-level constants."""

    def test_scope_declaration_mentions_digital_archive(self):
        assert "Digital Archive" in SCOPE_DECLARATION_LINE
        assert "2010" in SCOPE_DECLARATION_LINE
        assert "2025" in SCOPE_DECLARATION_LINE
        assert "1983" in SCOPE_DECLARATION_LINE
        assert "PFL Buddies" in SCOPE_DECLARATION_LINE

    def test_format_shift_footnote_describes_2021_change(self):
        assert "2021" in FORMAT_SHIFT_FOOTNOTE
        assert "14" in FORMAT_SHIFT_FOOTNOTE
        assert "15" in FORMAT_SHIFT_FOOTNOTE

    def test_titles_are_distinct(self):
        titles = {
            TITLE_INDEX,
            TITLE_CHAMPIONSHIP_ROLL,
            TITLE_WORST_SEASONS,
            TITLE_BLOWOUTS_HALL,
        }
        assert len(titles) == 4


# ── Unit: render_index_markdown ──────────────────────────────────────


class TestRenderIndex:
    def test_renders_h1_title(self):
        md = render_index_markdown()
        assert md.startswith(f"# {TITLE_INDEX}")

    def test_contains_scope_declaration(self):
        md = render_index_markdown()
        assert SCOPE_DECLARATION_LINE in md

    def test_links_three_sub_shape_pages(self):
        md = render_index_markdown()
        assert "./championship_roll.md" in md
        assert "./worst_seasons.md" in md
        assert "./blowouts_hall.md" in md

    def test_does_not_depend_on_data(self):
        # Index is data-free; consecutive calls produce identical output.
        assert render_index_markdown() == render_index_markdown()


# ── Unit: render_championship_roll_markdown ──────────────────────────


def _champ(
    *,
    season: int,
    champ: str,
    runner: str,
    week: int = 16,
    cs: float = 130.0,
    rs: float = 100.0,
    is_tie: bool = False,
) -> ChampionshipResult:
    return ChampionshipResult(
        season=season,
        champion_id=champ,
        runner_up_id=runner,
        championship_week=week,
        champion_score=cs,
        runner_up_score=rs,
        is_tie=is_tie,
    )


class TestRenderChampionshipRoll:
    def test_renders_h1_title(self):
        md = render_championship_roll_markdown([], {})
        assert md.startswith(f"# {TITLE_CHAMPIONSHIP_ROLL}")

    def test_contains_scope_declaration(self):
        md = render_championship_roll_markdown([], {})
        assert SCOPE_DECLARATION_LINE in md

    def test_empty_results_shows_no_data_message(self):
        md = render_championship_roll_markdown([], {})
        assert "No championship data available" in md

    def test_single_season_table_row(self):
        results = [_champ(season=2020, champ="A", runner="B")]
        md = render_championship_roll_markdown(
            results, _name_map(A="Alpha Team", B="Beta Team"),
        )
        assert "| 2020 |" in md
        assert "Alpha Team" in md
        assert "Beta Team" in md
        assert "130.00 to 100.00" in md

    def test_falls_back_to_franchise_id_when_name_missing(self):
        results = [_champ(season=2020, champ="A", runner="B")]
        md = render_championship_roll_markdown(results, {})
        # No name_map; A and B should appear as raw IDs.
        assert "| A |" in md
        assert "| B |" in md

    def test_tie_rendering(self):
        results = [
            _champ(season=2020, champ="A", runner="B", cs=120.0, rs=120.0, is_tie=True),
        ]
        md = render_championship_roll_markdown(results, _name_map(A="Alpha", B="Beta"))
        assert "tie" in md.lower()

    def test_per_franchise_title_counts_section(self):
        results = [
            _champ(season=2020, champ="A", runner="B"),
            _champ(season=2021, champ="A", runner="C"),
            _champ(season=2022, champ="B", runner="A"),
        ]
        md = render_championship_roll_markdown(
            results, _name_map(A="Alpha", B="Beta", C="Gamma"),
        )
        assert "Titles by Franchise" in md
        # Alpha has 2; should sort before Beta which has 1.
        # Skip the Champions-by-Season table where Alpha appears first;
        # check ordering in the Titles-by-Franchise section.
        titles_section = md[md.index("Titles by Franchise"):]
        assert titles_section.index("Alpha") < titles_section.index("Beta")
        assert "2" in titles_section  # alpha's title count
        # The seasons list must include 2020 and 2021 for Alpha.
        alpha_row_line = next(
            line for line in titles_section.splitlines()
            if line.startswith("| Alpha |")
        )
        assert "2020" in alpha_row_line
        assert "2021" in alpha_row_line

    def test_multi_season_ordering_preserved(self):
        # The aggregation returns season ascending; the render preserves it.
        results = [
            _champ(season=2020, champ="A", runner="B"),
            _champ(season=2021, champ="C", runner="D"),
            _champ(season=2022, champ="E", runner="F"),
        ]
        md = render_championship_roll_markdown(results, {})
        idx_2020 = md.index("| 2020 |")
        idx_2021 = md.index("| 2021 |")
        idx_2022 = md.index("| 2022 |")
        assert idx_2020 < idx_2021 < idx_2022


# ── Unit: render_worst_seasons_markdown ──────────────────────────────


def _season_record(
    *, fid: str, season: int, w: int, losses: int, t: int = 0, pf: float = 1000.0,
) -> SeasonRecord:
    return SeasonRecord(
        franchise_id=fid,
        season=season,
        wins=w,
        losses=losses,
        ties=t,
        points_for=pf,
    )


class TestRenderWorstSeasons:
    def test_renders_h1_title(self):
        md = render_worst_seasons_markdown([], {})
        assert md.startswith(f"# {TITLE_WORST_SEASONS}")

    def test_contains_scope_declaration(self):
        md = render_worst_seasons_markdown([], {})
        assert SCOPE_DECLARATION_LINE in md

    def test_empty_records_shows_no_data_message(self):
        md = render_worst_seasons_markdown([], {})
        assert "No season-record data available" in md

    def test_top_n_truncates(self):
        records = [
            _season_record(fid=f"F{i}", season=2020, w=0, losses=14, t=0, pf=900.0 - i)
            for i in range(15)
        ]
        md = render_worst_seasons_markdown(records, {}, top_n=5)
        # Should render exactly 5 ranked rows.
        for rank in range(1, 6):
            assert f"| {rank} |" in md
        assert "| 6 |" not in md

    def test_default_top_n_is_ten(self):
        records = [
            _season_record(fid=f"F{i}", season=2020, w=0, losses=14, t=0, pf=900.0 - i)
            for i in range(15)
        ]
        md = render_worst_seasons_markdown(records, {})
        assert "| 10 |" in md
        assert "| 11 |" not in md

    def test_top_n_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            render_worst_seasons_markdown([], {}, top_n=-1)

    def test_includes_format_shift_footnote(self):
        records = [_season_record(fid="A", season=2020, w=1, losses=13, pf=1300.0)]
        md = render_worst_seasons_markdown(records, {})
        assert FORMAT_SHIFT_FOOTNOTE in md

    def test_includes_win_pct_and_pf_per_game_columns(self):
        records = [_season_record(fid="A", season=2024, w=1, losses=13, pf=1392.75)]
        md = render_worst_seasons_markdown(records, _name_map(A="MGD"))
        # Win % column: 1 win in 14 games = 0.071
        assert "0.071" in md
        # PF/game: 1392.75 / 14 = 99.48
        assert "99.48" in md

    def test_record_with_ties_renders_three_part(self):
        records = [_season_record(fid="A", season=2020, w=5, losses=8, t=1)]
        md = render_worst_seasons_markdown(records, {})
        assert "5-8-1" in md

    def test_record_without_ties_renders_two_part(self):
        records = [_season_record(fid="A", season=2020, w=5, losses=9, t=0)]
        md = render_worst_seasons_markdown(records, {})
        assert "5-9" in md
        # Should not have a trailing -0 for ties.
        assert "5-9-0" not in md

    def test_falls_back_to_franchise_id_when_name_missing(self):
        records = [_season_record(fid="X", season=2020, w=0, losses=14)]
        md = render_worst_seasons_markdown(records, {})
        assert "| X |" in md


# ── Unit: render_blowouts_hall_markdown ──────────────────────────────


def _matchup(
    *,
    season: int,
    week: int,
    winner: str,
    loser: str,
    ws: float = 130.0,
    ls: float = 70.0,
) -> HistoricalMatchup:
    return HistoricalMatchup(
        season=season,
        week=week,
        winner_id=winner,
        loser_id=loser,
        winner_score=ws,
        loser_score=ls,
        is_tie=False,
        margin=ws - ls,
    )


class TestRenderBlowoutsHall:
    def test_renders_h1_title(self):
        md = render_blowouts_hall_markdown([], {})
        assert md.startswith(f"# {TITLE_BLOWOUTS_HALL}")

    def test_contains_scope_declaration(self):
        md = render_blowouts_hall_markdown([], {})
        assert SCOPE_DECLARATION_LINE in md

    def test_empty_matchups_shows_no_data_message(self):
        md = render_blowouts_hall_markdown([], {})
        assert "No matchup data available" in md

    def test_single_matchup_row(self):
        matchups = [_matchup(
            season=2025, week=14, winner="P", loser="B",
            ws=161.40, ls=54.80,
        )]
        md = render_blowouts_hall_markdown(
            matchups, _name_map(P="Paradis", B="Brandon"),
        )
        assert "| 2025 |" in md
        assert "Paradis" in md
        assert "Brandon" in md
        assert "161.40" in md
        assert "54.80" in md
        assert "106.60" in md  # margin

    def test_preserves_input_order(self):
        # Render preserves the order returned by compute_blowouts_hall
        # (which already sorts by margin descending).
        matchups = [
            _matchup(season=2025, week=14, winner="P", loser="B", ws=161.4, ls=54.8),
            _matchup(season=2020, week=3, winner="X", loser="Y", ws=150.0, ls=70.0),
            _matchup(season=2022, week=8, winner="M", loser="N", ws=140.0, ls=80.0),
        ]
        md = render_blowouts_hall_markdown(matchups, {})
        idx_1 = md.index("| 1 |")
        idx_2 = md.index("| 2 |")
        idx_3 = md.index("| 3 |")
        assert idx_1 < idx_2 < idx_3
        # Rank 1 row should have the 2025 entry.
        rank1_line = md[idx_1: md.index("\n", idx_1)]
        assert "2025" in rank1_line

    def test_falls_back_to_franchise_id_when_name_missing(self):
        matchups = [_matchup(season=2020, week=1, winner="X", loser="Y")]
        md = render_blowouts_hall_markdown(matchups, {})
        assert "| X |" in md
        assert "| Y |" in md
