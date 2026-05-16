"""Tests for Championship Timeline Render v1 (A3 surface rendering).

Pure unit tests against synthetic aggregation outputs. No database
fixtures; no file I/O. Tests verify markdown structure, the scope-
declaration invariant, the bracket-shape framing note, the
cross-link to A1's championship-roll page, column presence, ordering,
and edge cases.

Integration of these render functions with `load_all_matchups` and
the canonical event ledger lives in
`scripts/generate_championship_timeline_archive.py`; the script's
behavior is exercised by the layout-invariant test
(`test_championship_timeline_archive_layout_v1.py`) once the archive
exists.
"""
from __future__ import annotations

import pytest

from squadvault.core.recaps.context.championship_timeline_aggregations_v1 import (
    BridesmaidRecord,
    CrossSeasonPlayoffRecords,
    FranchisePlayoffRecord,
    PlayoffRound,
    SeasonBracket,
)
from squadvault.core.recaps.context.league_history_v1 import HistoricalMatchup
from squadvault.core.recaps.render.championship_timeline_render_v1 import (
    BRACKET_SHAPE_FRAMING,
    CHAMPIONSHIP_ROLL_CROSSLINK,
    RANK_DERIVATION_NOTE,
    SCOPE_DECLARATION_LINE,
    TITLE_BRIDESMAIDS,
    TITLE_INDEX,
    TITLE_PLAYOFF_BRACKETS,
    TITLE_PLAYOFF_RECORDS,
    render_bridesmaids_markdown,
    render_index_markdown,
    render_playoff_brackets_markdown,
    render_playoff_records_markdown,
)

# ── Helpers for synthetic data ───────────────────────────────────────


def _matchup(
    *,
    season: int,
    week: int,
    winner: str,
    loser: str,
    ws: float = 120.0,
    ls: float = 100.0,
    is_tie: bool = False,
) -> HistoricalMatchup:
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


def _sample_bracket(season: int = 2018) -> SeasonBracket:
    """A clean 3-round bracket for one season."""
    prelim = PlayoffRound(
        season=season, week=15, round_label="Preliminary",
        matchups=(
            _matchup(season=season, week=15, winner="A", loser="H"),
            _matchup(season=season, week=15, winner="B", loser="G"),
        ),
    )
    semifinal = PlayoffRound(
        season=season, week=16, round_label="Semifinal",
        matchups=(
            _matchup(season=season, week=16, winner="A", loser="B"),
        ),
    )
    championship = PlayoffRound(
        season=season, week=17, round_label="Championship",
        matchups=(
            _matchup(
                season=season, week=17, winner="A", loser="C",
                ws=130.0, ls=95.0,
            ),
        ),
    )
    return SeasonBracket(
        season=season, rounds=(prelim, semifinal, championship),
    )


def _sample_records() -> CrossSeasonPlayoffRecords:
    return CrossSeasonPlayoffRecords(
        per_franchise=(
            FranchisePlayoffRecord(
                franchise_id="A",
                playoff_season_count=14,
                championship_appearance_count=6,
                longest_active_streak=12,
                longest_drought_streak=1,
            ),
            FranchisePlayoffRecord(
                franchise_id="B",
                playoff_season_count=11,
                championship_appearance_count=3,
                longest_active_streak=5,
                longest_drought_streak=2,
            ),
            FranchisePlayoffRecord(
                franchise_id="C",
                playoff_season_count=8,
                championship_appearance_count=0,
                longest_active_streak=3,
                longest_drought_streak=2,
            ),
        ),
        total_seasons=16,
    )


def _sample_bridesmaids() -> tuple[BridesmaidRecord, ...]:
    return (
        BridesmaidRecord(
            franchise_id="C",
            runner_up_count=3,
            runner_up_seasons=(2014, 2017, 2021),
            championship_count=0,
        ),
        BridesmaidRecord(
            franchise_id="B",
            runner_up_count=3,
            runner_up_seasons=(2012, 2018, 2022),
            championship_count=2,
        ),
        BridesmaidRecord(
            franchise_id="D",
            runner_up_count=1,
            runner_up_seasons=(2019,),
            championship_count=1,
        ),
    )


# ── Module constants ─────────────────────────────────────────────────


class TestModuleConstants:
    def test_scope_declaration_mentions_championship_timeline(self):
        assert "Championship Timeline" in SCOPE_DECLARATION_LINE

    def test_scope_declaration_states_2010_2025_boundary(self):
        assert "2010" in SCOPE_DECLARATION_LINE
        assert "2025" in SCOPE_DECLARATION_LINE

    def test_scope_declaration_does_not_claim_seventeen_seasons(self):
        # Per spec section 3.6: A3 must not claim "17 seasons" — the
        # digital era is 16 seasons.
        assert "17 season" not in SCOPE_DECLARATION_LINE.lower()
        assert "sixteen" in SCOPE_DECLARATION_LINE.lower()

    def test_bracket_shape_framing_acknowledges_two_eras(self):
        # Per spec section 3.6: the framing notes the 2021 format shift.
        assert "2021" in BRACKET_SHAPE_FRAMING
        assert "14 to 15" in BRACKET_SHAPE_FRAMING

    def test_bracket_shape_framing_acknowledges_w18_collapse(self):
        # Per spec section 3.6 / section 6.2: the framing notes the
        # duplicate championship row is collapsed by content.
        assert "duplicate" in BRACKET_SHAPE_FRAMING.lower()
        assert "collapse" in BRACKET_SHAPE_FRAMING.lower()

    def test_crosslink_points_to_a1_championship_roll(self):
        # Per spec section 3.1 / section 6.4: A3 cross-links to A1's
        # championship-roll page rather than re-rendering it.
        assert CHAMPIONSHIP_ROLL_CROSSLINK == (
            "../hall_of_fame_and_shame/championship_roll.md"
        )

    def test_rank_derivation_note_describes_substrate_recomputation(self):
        assert "substrate" in RANK_DERIVATION_NOTE.lower()

    def test_titles_are_distinct(self):
        titles = {
            TITLE_INDEX,
            TITLE_PLAYOFF_BRACKETS,
            TITLE_PLAYOFF_RECORDS,
            TITLE_BRIDESMAIDS,
        }
        assert len(titles) == 4


# ── Index page ───────────────────────────────────────────────────────


class TestRenderIndexMarkdown:
    def test_starts_with_h1_title(self):
        md = render_index_markdown()
        assert md.startswith(f"# {TITLE_INDEX}")

    def test_contains_scope_declaration(self):
        assert SCOPE_DECLARATION_LINE in render_index_markdown()

    def test_links_to_three_sub_shape_pages(self):
        md = render_index_markdown()
        assert "./playoff_brackets.md" in md
        assert "./playoff_records.md" in md
        assert "./bridesmaids.md" in md

    def test_mentions_each_sub_shape_title(self):
        md = render_index_markdown()
        assert TITLE_PLAYOFF_BRACKETS in md
        assert TITLE_PLAYOFF_RECORDS in md
        assert TITLE_BRIDESMAIDS in md

    def test_independent_of_substrate_data(self):
        # The index does not depend on any input; two calls are equal.
        assert render_index_markdown() == render_index_markdown()


# ── Per-Season Playoff Brackets ──────────────────────────────────────


class TestRenderPlayoffBracketsMarkdown:
    def test_empty_brackets_produces_no_data_page(self):
        md = render_playoff_brackets_markdown([], {})
        assert md.startswith(f"# {TITLE_PLAYOFF_BRACKETS}")
        assert "No playoff bracket data available" in md

    def test_no_data_page_still_carries_scope_and_framing(self):
        md = render_playoff_brackets_markdown([], {})
        assert SCOPE_DECLARATION_LINE in md
        assert BRACKET_SHAPE_FRAMING in md

    def test_renders_season_section(self):
        md = render_playoff_brackets_markdown([_sample_bracket(2018)], {})
        assert "## 2018" in md

    def test_renders_each_round_with_week_label(self):
        md = render_playoff_brackets_markdown([_sample_bracket(2018)], {})
        assert "### Preliminary (Week 15)" in md
        assert "### Semifinal (Week 16)" in md
        assert "### Championship (Week 17)" in md

    def test_renders_matchup_rows(self):
        md = render_playoff_brackets_markdown(
            [_sample_bracket(2018)],
            {("A", 2018): "Team A", ("C", 2018): "Team C"},
        )
        # championship row: Team A 130.00 to 95.00 Team C
        assert "Team A" in md
        assert "Team C" in md
        assert "130.00 to 95.00" in md

    def test_includes_crosslink_to_championship_roll(self):
        md = render_playoff_brackets_markdown([_sample_bracket(2018)], {})
        assert CHAMPIONSHIP_ROLL_CROSSLINK in md

    def test_falls_back_to_raw_ids_when_names_missing(self):
        md = render_playoff_brackets_markdown([_sample_bracket(2018)], {})
        # No name_map entries; raw franchise ids appear.
        assert "| A |" in md

    def test_multiple_seasons_each_get_a_section(self):
        md = render_playoff_brackets_markdown(
            [_sample_bracket(2018), _sample_bracket(2019)], {},
        )
        assert "## 2018" in md
        assert "## 2019" in md

    def test_tie_score_formatting(self):
        tied = SeasonBracket(
            season=2015,
            rounds=(
                PlayoffRound(
                    season=2015, week=16, round_label="Championship",
                    matchups=(
                        _matchup(
                            season=2015, week=16, winner="A", loser="B",
                            ws=100.0, ls=100.0, is_tie=True,
                        ),
                    ),
                ),
            ),
        )
        md = render_playoff_brackets_markdown([tied], {})
        assert "(tie)" in md


# ── Cross-Season Playoff Records ─────────────────────────────────────


class TestRenderPlayoffRecordsMarkdown:
    def test_empty_records_produces_no_data_page(self):
        empty = CrossSeasonPlayoffRecords(per_franchise=(), total_seasons=0)
        md = render_playoff_records_markdown(empty, {})
        assert md.startswith(f"# {TITLE_PLAYOFF_RECORDS}")
        assert "No playoff-record data available" in md

    def test_renders_all_four_leaderboard_sections(self):
        # Per spec section 3.8: all four dimensions ship at v1.
        md = render_playoff_records_markdown(_sample_records(), {})
        assert "## Playoff-Season Appearances" in md
        assert "## Championship-Matchup Appearances" in md
        assert "## Longest Playoff-Active Streak" in md
        assert "## Longest Playoff-Drought Streak" in md

    def test_drought_section_is_shown_alongside_active(self):
        # Per spec section 3.8: the drought dimension is not suppressed;
        # the symmetry is substrate-honest.
        md = render_playoff_records_markdown(_sample_records(), {})
        active_idx = md.index("Longest Playoff-Active Streak")
        drought_idx = md.index("Longest Playoff-Drought Streak")
        assert active_idx < drought_idx

    def test_playoff_appearances_sorted_descending(self):
        md = render_playoff_records_markdown(
            _sample_records(),
            {"A": "Alpha", "B": "Bravo", "C": "Charlie"},
        )
        section = md.split("## Playoff-Season Appearances")[1]
        section = section.split("## ")[0]
        assert section.index("Alpha") < section.index("Bravo")
        assert section.index("Bravo") < section.index("Charlie")

    def test_total_seasons_in_framing(self):
        md = render_playoff_records_markdown(_sample_records(), {})
        assert "16 digital-era seasons" in md

    def test_top_n_truncates_each_leaderboard(self):
        md = render_playoff_records_markdown(
            _sample_records(), {}, top_n=1,
        )
        # only the rank-1 row should appear in each section
        section = md.split("## Playoff-Season Appearances")[1].split("## ")[0]
        assert "| 1 |" in section
        assert "| 2 |" not in section

    def test_top_n_negative_raises(self):
        with pytest.raises(ValueError):
            render_playoff_records_markdown(_sample_records(), {}, top_n=-1)

    def test_contains_rank_derivation_note(self):
        md = render_playoff_records_markdown(_sample_records(), {})
        assert RANK_DERIVATION_NOTE in md

    def test_falls_back_to_raw_ids_when_names_missing(self):
        md = render_playoff_records_markdown(_sample_records(), {})
        assert "| A |" in md


# ── Bridesmaids ──────────────────────────────────────────────────────


class TestRenderBridesmaidsMarkdown:
    def test_empty_bridesmaids_produces_no_data_page(self):
        md = render_bridesmaids_markdown([], {})
        assert md.startswith(f"# {TITLE_BRIDESMAIDS}")
        assert "No runner-up data available" in md

    def test_renders_leaderboard_with_rank_column(self):
        md = render_bridesmaids_markdown(_sample_bridesmaids(), {})
        assert "| Rank | Franchise | Runner-Up Finishes | Seasons | Titles |" in md
        assert "| 1 |" in md

    def test_surfaces_titles_column_for_bridesmaid_archetype(self):
        # Per spec section 3.7 / 4.5: the Titles column surfaces the
        # perennial-bridesmaid archetype (runner-ups, zero titles).
        # Franchise C earliest runner-up season is 2014; key accordingly.
        md = render_bridesmaids_markdown(
            _sample_bridesmaids(), {("C", 2014): "Charlie"},
        )
        # franchise C: 3 runner-ups, 0 titles
        c_line = next(
            line for line in md.splitlines() if "Charlie" in line
        )
        assert c_line.rstrip().endswith("| 0 |")

    def test_renders_runner_up_seasons(self):
        md = render_bridesmaids_markdown(_sample_bridesmaids(), {})
        assert "2014, 2017, 2021" in md

    def test_preserves_input_order(self):
        # compute_bridesmaids already sorts; the render keeps that order.
        # C earliest: 2014, B earliest: 2012, D earliest: 2019.
        md = render_bridesmaids_markdown(
            _sample_bridesmaids(),
            {
                ("C", 2014): "Charlie",
                ("B", 2012): "Bravo",
                ("D", 2019): "Delta",
            },
        )
        assert md.index("Charlie") < md.index("Bravo") < md.index("Delta")

    def test_era_correct_name_resolution(self):
        # The canonical residual from the predecessor session:
        # a franchise that changed names between eras is attributed
        # to the name it carried in its earliest runner-up season.
        # Slot 0010 was "SS Express" in 2013 and "Brandon Knows Ball"
        # in later seasons; the season_map key ("0010", 2013) resolves
        # to "SS Express" and must appear in the output.
        record = BridesmaidRecord(
            franchise_id="0010",
            runner_up_count=1,
            runner_up_seasons=(2013,),
            championship_count=1,
        )
        season_map = {("0010", 2013): "SS Express"}
        md = render_bridesmaids_markdown((record,), season_map)
        assert "SS Express" in md
        assert "Brandon Knows Ball" not in md

    def test_contains_rank_derivation_note(self):
        md = render_bridesmaids_markdown(_sample_bridesmaids(), {})
        assert RANK_DERIVATION_NOTE in md

    def test_falls_back_to_raw_ids_when_names_missing(self):
        md = render_bridesmaids_markdown(_sample_bridesmaids(), {})
        assert "| C |" in md


# ── Determinism ──────────────────────────────────────────────────────


class TestRenderDeterminism:
    def test_brackets_determinism(self):
        a = render_playoff_brackets_markdown([_sample_bracket()], {})
        b = render_playoff_brackets_markdown([_sample_bracket()], {})
        assert a == b

    def test_records_determinism(self):
        a = render_playoff_records_markdown(_sample_records(), {})
        b = render_playoff_records_markdown(_sample_records(), {})
        assert a == b

    def test_bridesmaids_determinism(self):
        a = render_bridesmaids_markdown(_sample_bridesmaids(), {})
        b = render_bridesmaids_markdown(_sample_bridesmaids(), {})
        assert a == b
