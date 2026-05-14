"""Tests for Draft History Vault Render v1 (A2 surface rendering).

Pure unit tests against synthetic aggregation outputs. No database
fixtures; no file I/O. Tests verify markdown structure, scope-
declaration invariant, column presence, ordering, and edge cases.

Per A2 spec section 6.8 narrative-claim drift principle: render
functions are validated to produce NO frozen ordinal claims like
"the third-highest bid in league history" - only rank-derived
ordinals computed at call time.

Integration of these render functions with `load_all_auction_picks`,
`load_player_season_scoring`, and the canonical event ledger lives
in `scripts/generate_draft_history_vault_archive.py`; the script's
behavior is exercised by the layout-invariant test
(`test_draft_history_vault_archive_layout_v1.py`) once the archive
exists.
"""
from __future__ import annotations

from squadvault.core.recaps.context.draft_history_vault_aggregations_v1 import (
    BargainEntry,
    BustEntry,
    MostExpensivePick,
    MostExpensiveResult,
)
from squadvault.core.recaps.render.draft_history_vault_render_v1 import (
    RANK_DERIVATION_NOTE,
    SCOPE_DECLARATION_LINE,
    TITLE_BARGAIN_HALL,
    TITLE_BUST_HALL,
    TITLE_INDEX,
    TITLE_MOST_EXPENSIVE,
    render_bargain_hall_markdown,
    render_bust_hall_markdown,
    render_index_markdown,
    render_most_expensive_markdown,
)

# -- Module-level invariants -----------------------------------------


class TestModuleConstants:
    """Tests for the load-bearing module-level constants."""

    def test_scope_declaration_mentions_draft_history_vault(self):
        assert "Draft History Vault" in SCOPE_DECLARATION_LINE
        assert "PFL Buddies" in SCOPE_DECLARATION_LINE

    def test_scope_declaration_acknowledges_auction_era(self):
        # Per spec section 3.6 the auction era is 2018-2025.
        assert "2018" in SCOPE_DECLARATION_LINE
        assert "2025" in SCOPE_DECLARATION_LINE

    def test_scope_declaration_acknowledges_2021_gap_honestly(self):
        # Per spec section 3.6 / section 2.3 silence-over-speculation:
        # the 2021 gap framing is "not represented".
        assert "2021" in SCOPE_DECLARATION_LINE
        assert "not represented" in SCOPE_DECLARATION_LINE

    def test_rank_derivation_note_describes_substrate_recomputation(self):
        # Per spec section 6.8 narrative-claim drift principle.
        assert "substrate" in RANK_DERIVATION_NOTE
        assert "regenerat" in RANK_DERIVATION_NOTE  # "regeneration"

    def test_titles_are_distinct(self):
        titles = {
            TITLE_INDEX, TITLE_MOST_EXPENSIVE, TITLE_BUST_HALL,
            TITLE_BARGAIN_HALL,
        }
        assert len(titles) == 4


# -- render_index_markdown -------------------------------------------


class TestRenderIndexMarkdown:
    """A2 spec section 5.1 / section 6.4 layout invariant."""

    def test_starts_with_h1_title(self):
        md = render_index_markdown()
        assert md.startswith(f"# {TITLE_INDEX}")

    def test_contains_scope_declaration(self):
        md = render_index_markdown()
        assert SCOPE_DECLARATION_LINE in md

    def test_links_to_three_sub_shape_pages(self):
        md = render_index_markdown()
        assert "most_expensive.md" in md
        assert "bust_hall.md" in md
        assert "bargain_hall.md" in md

    def test_mentions_each_sub_shape_title(self):
        md = render_index_markdown()
        assert TITLE_MOST_EXPENSIVE in md
        assert TITLE_BUST_HALL in md
        assert TITLE_BARGAIN_HALL in md

    def test_independent_of_substrate_data(self):
        # Index page does not depend on aggregation inputs.
        a = render_index_markdown()
        b = render_index_markdown()
        assert a == b
        assert len(a) > 100  # non-empty content


# -- render_most_expensive_markdown ----------------------------------


class TestRenderMostExpensiveMarkdown:
    """A2 spec section 3.1 / section 3.8 / section 5.1 sub-shape."""

    def test_empty_result_produces_no_data_page(self):
        result = MostExpensiveResult(overall=None, per_position=())
        md = render_most_expensive_markdown(result, {}, {})
        assert md.startswith(f"# {TITLE_MOST_EXPENSIVE}")
        assert SCOPE_DECLARATION_LINE in md
        assert "No auction-pick data available" in md

    def test_renders_overall_record(self):
        result = MostExpensiveResult(
            overall=MostExpensivePick(
                season=2018, franchise_id="0002", player_id="9988",
                bid_amount=62.0, position="QB",
            ),
            per_position=(),
        )
        md = render_most_expensive_markdown(
            result,
            {"0002": "Italian Cavallini"},
            {"9988": "Patrick Mahomes"},
        )
        assert "Italian Cavallini" in md
        assert "Patrick Mahomes" in md
        assert "$62" in md
        assert "2018" in md
        assert "QB" in md
        assert "Overall Record" in md

    def test_renders_per_position_table(self):
        result = MostExpensiveResult(
            overall=MostExpensivePick(
                season=2020, franchise_id="F1", player_id="P_qb",
                bid_amount=80.0, position="QB",
            ),
            per_position=(
                MostExpensivePick(
                    season=2020, franchise_id="F1", player_id="P_qb",
                    bid_amount=80.0, position="QB",
                ),
                MostExpensivePick(
                    season=2022, franchise_id="F2", player_id="P_rb",
                    bid_amount=70.0, position="RB",
                ),
                MostExpensivePick(
                    season=2024, franchise_id="F3", player_id="P_wr",
                    bid_amount=60.0, position="WR",
                ),
            ),
        )
        md = render_most_expensive_markdown(
            result,
            {"F1": "Alpha", "F2": "Beta", "F3": "Gamma"},
            {"P_qb": "QB Player", "P_rb": "RB Player", "P_wr": "WR Player"},
        )
        assert "Per-Position Records" in md
        assert "| Position |" in md
        assert "| QB |" in md
        assert "| RB |" in md
        assert "| WR |" in md
        assert "QB Player" in md
        assert "RB Player" in md
        assert "WR Player" in md

    def test_falls_back_to_raw_ids_when_names_missing(self):
        result = MostExpensiveResult(
            overall=MostExpensivePick(
                season=2020, franchise_id="UNKNOWN_F", player_id="UNKNOWN_P",
                bid_amount=99.0, position="QB",
            ),
            per_position=(),
        )
        md = render_most_expensive_markdown(result, {}, {})
        assert "UNKNOWN_F" in md
        assert "UNKNOWN_P" in md
        assert "$99" in md

    def test_contains_rank_derivation_note(self):
        # Per spec section 6.8: every leaderboard page acknowledges
        # that ranks compute at render time.
        result = MostExpensiveResult(
            overall=MostExpensivePick(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=50.0, position="QB",
            ),
            per_position=(),
        )
        md = render_most_expensive_markdown(result, {}, {})
        assert RANK_DERIVATION_NOTE in md

    def test_no_frozen_ordinal_claims_in_output(self):
        # Per spec section 6.8: forbid markdown text like
        # "the third-highest bid in league history" - the cautionary
        # example from Step 1 section 4.5. The render output must
        # contain no ordinal claim that ranks a value across the
        # broader league history.
        result = MostExpensiveResult(
            overall=MostExpensivePick(
                season=2018, franchise_id="0002", player_id="9988",
                bid_amount=62.0, position="QB",
            ),
            per_position=(),
        )
        md = render_most_expensive_markdown(result, {}, {})
        forbidden_phrases = [
            "third-highest",
            "second-highest",
            "fifth-most-expensive",
            "twelfth-worst",
            "the third highest bid",
        ]
        for phrase in forbidden_phrases:
            assert phrase.lower() not in md.lower(), (
                f"Found forbidden frozen ordinal claim '{phrase}' "
                f"in markdown output - per spec section 6.8 these "
                f"phrasings drift across substrate updates and are "
                f"forbidden in archive markdown."
            )


# -- render_bust_hall_markdown ---------------------------------------


class TestRenderBustHallMarkdown:
    """A2 spec section 3.1 sub-shape rendering."""

    def test_empty_entries_produces_no_data_page(self):
        md = render_bust_hall_markdown((), {}, {})
        assert md.startswith(f"# {TITLE_BUST_HALL}")
        assert SCOPE_DECLARATION_LINE in md
        assert "No bust entries" in md

    def test_renders_leaderboard_with_rank_column(self):
        entries = (
            BustEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=80.0, player_avg=2.5,
                league_starter_avg=10.0, starter_weeks=8,
                severity_signal=600.0,
            ),
            BustEntry(
                season=2022, franchise_id="F2", player_id="P2",
                bid_amount=60.0, player_avg=3.0,
                league_starter_avg=10.0, starter_weeks=10,
                severity_signal=420.0,
            ),
        )
        md = render_bust_hall_markdown(
            entries,
            {"F1": "Alpha", "F2": "Beta"},
            {"P1": "Player One", "P2": "Player Two"},
        )
        assert "| Rank |" in md
        # First entry is rank 1, second is rank 2.
        assert "| 1 | 2020 |" in md
        assert "| 2 | 2022 |" in md
        assert "Alpha" in md
        assert "Player One" in md
        assert "$80" in md
        assert "600.0" in md  # severity signal

    def test_describes_inclusion_thresholds(self):
        entries = (
            BustEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=80.0, player_avg=2.5,
                league_starter_avg=10.0, starter_weeks=8,
                severity_signal=600.0,
            ),
        )
        md = render_bust_hall_markdown(entries, {}, {})
        assert "starter weeks" in md.lower()
        assert "severity" in md.lower()

    def test_contains_rank_derivation_note(self):
        entries = (
            BustEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=80.0, player_avg=2.5,
                league_starter_avg=10.0, starter_weeks=8,
                severity_signal=600.0,
            ),
        )
        md = render_bust_hall_markdown(entries, {}, {})
        assert RANK_DERIVATION_NOTE in md

    def test_no_frozen_ordinal_claims(self):
        entries = (
            BustEntry(
                season=2024, franchise_id="0009", player_id="13130",
                bid_amount=70.0, player_avg=10.1,
                league_starter_avg=12.0, starter_weeks=4,
                severity_signal=133.0,
            ),
        )
        md = render_bust_hall_markdown(entries, {}, {})
        forbidden_phrases = [
            "worst auction bust in PFL history",
            "the worst bust ever",
            "third-worst",
            "fourth-worst",
        ]
        for phrase in forbidden_phrases:
            assert phrase.lower() not in md.lower(), (
                f"Found forbidden frozen ordinal claim '{phrase}'."
            )


# -- render_bargain_hall_markdown ------------------------------------


class TestRenderBargainHallMarkdown:
    """A2 spec section 3.1 sub-shape rendering."""

    def test_empty_entries_produces_no_data_page(self):
        md = render_bargain_hall_markdown((), {}, {})
        assert md.startswith(f"# {TITLE_BARGAIN_HALL}")
        assert SCOPE_DECLARATION_LINE in md
        assert "No bargain entries" in md

    def test_renders_leaderboard_with_rank_column(self):
        entries = (
            BargainEntry(
                season=2018, franchise_id="F1", player_id="P1",
                bid_amount=1.0, total_points=200.0, dollar_per_point=0.005,
            ),
            BargainEntry(
                season=2020, franchise_id="F2", player_id="P2",
                bid_amount=2.0, total_points=100.0, dollar_per_point=0.020,
            ),
        )
        md = render_bargain_hall_markdown(
            entries,
            {"F1": "Alpha", "F2": "Beta"},
            {"P1": "Player One", "P2": "Player Two"},
        )
        assert "| Rank |" in md
        assert "| 1 | 2018 |" in md
        assert "| 2 | 2020 |" in md
        assert "Alpha" in md
        assert "Player One" in md
        assert "$1" in md
        assert "200.0" in md

    def test_describes_minimum_production_threshold(self):
        entries = (
            BargainEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=1.0, total_points=200.0, dollar_per_point=0.005,
            ),
        )
        md = render_bargain_hall_markdown(entries, {}, {})
        assert "50" in md  # min_points threshold
        assert "dollar" in md.lower() or "$" in md

    def test_contains_rank_derivation_note(self):
        entries = (
            BargainEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=1.0, total_points=200.0, dollar_per_point=0.005,
            ),
        )
        md = render_bargain_hall_markdown(entries, {}, {})
        assert RANK_DERIVATION_NOTE in md

    def test_no_frozen_ordinal_claims(self):
        entries = (
            BargainEntry(
                season=2018, franchise_id="F1", player_id="P1",
                bid_amount=1.0, total_points=300.0, dollar_per_point=0.003,
            ),
        )
        md = render_bargain_hall_markdown(entries, {}, {})
        forbidden_phrases = [
            "best bargain in PFL history",
            "the all-time greatest bargain",
            "second-best bargain ever",
        ]
        for phrase in forbidden_phrases:
            assert phrase.lower() not in md.lower(), (
                f"Found forbidden frozen ordinal claim '{phrase}'."
            )


# -- Determinism across render functions -----------------------------


class TestRenderDeterminism:
    """All render functions produce identical output for identical inputs."""

    def test_index_determinism(self):
        a = render_index_markdown()
        b = render_index_markdown()
        assert a == b

    def test_most_expensive_determinism(self):
        result = MostExpensiveResult(
            overall=MostExpensivePick(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=80.0, position="QB",
            ),
            per_position=(
                MostExpensivePick(
                    season=2020, franchise_id="F1", player_id="P1",
                    bid_amount=80.0, position="QB",
                ),
            ),
        )
        names_f = {"F1": "Alpha"}
        names_p = {"P1": "QB Player"}
        a = render_most_expensive_markdown(result, names_f, names_p)
        b = render_most_expensive_markdown(result, names_f, names_p)
        assert a == b

    def test_bust_hall_determinism(self):
        entries = (
            BustEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=80.0, player_avg=2.5,
                league_starter_avg=10.0, starter_weeks=8,
                severity_signal=600.0,
            ),
        )
        a = render_bust_hall_markdown(entries, {}, {})
        b = render_bust_hall_markdown(entries, {}, {})
        assert a == b

    def test_bargain_hall_determinism(self):
        entries = (
            BargainEntry(
                season=2020, franchise_id="F1", player_id="P1",
                bid_amount=1.0, total_points=200.0, dollar_per_point=0.005,
            ),
        )
        a = render_bargain_hall_markdown(entries, {}, {})
        b = render_bargain_hall_markdown(entries, {}, {})
        assert a == b
