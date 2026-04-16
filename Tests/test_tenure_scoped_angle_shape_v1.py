"""Tests for tenure-scoped rivalry angle shape + verifier tenure-skip.

Covers the W10 Purple Haze failure mode: the model stripped the trailing
"(under current ownership)" parenthetical from a tenure-scoped rivalry
headline, producing a "leads the series 8-2" claim that read as an
all-time record and failed verification against the actual all-time
9-12. The structural response:

1. narrative_angles_v1 now prefixes tenure-scoped rivalry headlines with
   "Under current ownership only:" so scope is grammatically
   load-bearing instead of a droppable trailing parenthetical, and
   surfaces the prior-era split in the detail with an explicit
   prohibition on stating a combined all-time record.

2. recap_verifier_v1 tenure-skip regex is widened: "current ownership"
   no longer requires a leading "under", so paraphrases like "in the
   current ownership era" also trigger the skip.

Governance: data-layer shape changes carry the constraint into the
model's output; prompt guardrails alone are insufficient.
"""
from __future__ import annotations

# ── Helpers ──────────────────────────────────────────────────────────


def _build_contexts(tenure_w: int | None, tenure_l: int | None,
                     matchups_a_wins: int, matchups_b_wins: int,
                     first_season: int = 2010, last_season: int = 2024):
    """Build season/history/all_matchups contexts for a two-franchise pair.

    Returns (season_ctx, history_ctx, all_matchups, tenure_map).
    Tenure dates are interpreted as the first season of current ownership
    for each franchise; None means the franchise has been present since
    first_season (no tenure filter applies from that side).
    """
    from squadvault.core.recaps.context.league_history_v1 import (
        HistoricalMatchup,
        LeagueHistoryContextV1,
    )
    from squadvault.core.recaps.context.season_context_v1 import (
        SeasonContextV1,
        TeamRecord,
        WeekMatchupContext,
    )

    # Distribute wins across seasons: alternate winners for a clean split.
    total_meetings = matchups_a_wins + matchups_b_wins
    seasons = list(range(first_season, last_season + 1))
    # Pad to at least total_meetings seasons (1 game/season for simplicity).
    while len(seasons) < total_meetings:
        seasons.append(seasons[-1] + 1)

    matchups = []
    a_used = 0
    b_used = 0
    for i, season in enumerate(seasons[:total_meetings]):
        if a_used < matchups_a_wins and (i % 2 == 0 or b_used >= matchups_b_wins):
            matchups.append(HistoricalMatchup(
                season=season, week=1,
                winner_id="0001", loser_id="0002",
                winner_score=100.0, loser_score=90.0,
                is_tie=False, margin=10.0,
            ))
            a_used += 1
        else:
            matchups.append(HistoricalMatchup(
                season=season, week=1,
                winner_id="0002", loser_id="0001",
                winner_score=100.0, loser_score=90.0,
                is_tie=False, margin=10.0,
            ))
            b_used += 1

    tr_w = TeamRecord(
        franchise_id="0001", wins=8, losses=5, ties=0,
        points_for=1400.0, points_against=1300.0, current_streak=3,
    )
    tr_l = TeamRecord(
        franchise_id="0002", wins=5, losses=8, ties=0,
        points_for=1200.0, points_against=1350.0, current_streak=-2,
    )
    # This week's matchup: 0001 beats 0002.
    wm = WeekMatchupContext(
        winner_id="0001", loser_id="0002",
        winner_score=120.0, loser_score=95.0,
        margin=25.0, is_tie=False,
        winner_record_after=tr_w, loser_record_after=tr_l,
    )
    season_ctx = SeasonContextV1(
        league_id="70985", season=last_season, through_week=10,
        standings=(tr_w, tr_l), week_matchups=(wm,),
        week_high_scorer=("0001", 120.0), week_low_scorer=("0002", 95.0),
        week_closest_game=None, week_biggest_blowout=("0001", "0002", 25.0),
        season_high=None, season_low=None, season_avg_score=None,
        total_matchups_through_week=total_meetings, matchups_this_week=1,
    )
    history_ctx = LeagueHistoryContextV1(
        league_id="70985",
        seasons_available=tuple(range(first_season, last_season + 1)),
        total_matchups_all_time=len(matchups),
        all_time_records=(), all_time_high=None, all_time_low=None,
        all_time_avg_score=None, longest_win_streak=None,
        longest_loss_streak=None, best_season_record=None,
        worst_season_record=None,
    )
    tenure_map: dict[str, int] = {}
    if tenure_w is not None:
        tenure_map["0001"] = tenure_w
    if tenure_l is not None:
        tenure_map["0002"] = tenure_l
    return season_ctx, history_ctx, matchups, tenure_map


# ── narrative_angles_v1: scope-prefix + prior-era exposure ───────────


class TestTenureScopedHeadlineShape:
    """Tenure-scoped rivalry angles use a structural scope prefix."""

    def test_dominance_headline_has_scope_prefix(self):
        """When tenure applies, dominance headline starts with the prefix."""
        from squadvault.core.recaps.context.narrative_angles_v1 import (
            _detect_rivalry_angles,
        )

        # Prior era (2010-2018, 9 seasons): 1-8 for 0001.
        # Current era (2019-2024, 6 seasons): 6-0 for 0001.
        # Overall: 7-8 (0001), current-era-only: 6-0 (dominance fires with 100%).
        season_ctx, history_ctx, matchups, tenure_map = _build_contexts(
            tenure_w=2019, tenure_l=2010,
            matchups_a_wins=7, matchups_b_wins=8,
            first_season=2010, last_season=2024,
        )
        # Force the exact split we want by replacing matchups.
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
        )
        # 9 losses for 0001 from 2010-2018, 6 wins from 2019-2024
        matchups = (
            [HistoricalMatchup(
                season=y, week=1, winner_id="0002", loser_id="0001",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            ) for y in range(2010, 2018)]
            + [HistoricalMatchup(
                season=2018, week=1, winner_id="0001", loser_id="0002",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            )]
            + [HistoricalMatchup(
                season=y, week=1, winner_id="0001", loser_id="0002",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            ) for y in range(2019, 2025)]
        )

        angles = _detect_rivalry_angles(season_ctx, history_ctx, matchups, tenure_map)
        rivalry = [a for a in angles if a.category == "RIVALRY"]
        assert len(rivalry) == 1, f"expected one rivalry angle, got {len(rivalry)}"
        angle = rivalry[0]

        assert angle.headline.startswith("Under current ownership only: "), (
            f"headline must start with scope prefix; got: {angle.headline!r}"
        )
        # Record is still present
        assert "6-0" in angle.headline
        # Existing-test markers still present for the branch
        assert "leads the series" in angle.headline

    def test_tenure_scoped_detail_exposes_prior_era(self):
        """Detail surfaces prior-era split with explicit combined-record prohibition."""
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
        )
        from squadvault.core.recaps.context.narrative_angles_v1 import (
            _detect_rivalry_angles,
        )

        season_ctx, history_ctx, _matchups, tenure_map = _build_contexts(
            tenure_w=2019, tenure_l=2010,
            matchups_a_wins=7, matchups_b_wins=8,
        )
        # Prior era 2010-2018: 0002 wins all 8; current 2019-2024: 0001 wins all 6
        matchups = (
            [HistoricalMatchup(
                season=y, week=1, winner_id="0002", loser_id="0001",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            ) for y in range(2010, 2018)]
            + [HistoricalMatchup(
                season=y, week=1, winner_id="0001", loser_id="0002",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            ) for y in range(2019, 2025)]
        )

        angles = _detect_rivalry_angles(season_ctx, history_ctx, matchups, tenure_map)
        angle = [a for a in angles if a.category == "RIVALRY"][0]

        assert "Prior era under different ownership" in angle.detail, (
            f"detail missing prior-era split; got: {angle.detail!r}"
        )
        # Prior era was 0-8 for 0001 (0002 won all 8); detail should
        # cite the leading side with the correct record.
        assert "0002 8-0" in angle.detail
        assert "Do NOT state a combined all-time record" in angle.detail

    def test_tenure_scoped_detail_omits_prior_note_when_no_prior_meetings(self):
        """If the pair has no meetings before tenure start, prior-era note absent."""
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
        )
        from squadvault.core.recaps.context.narrative_angles_v1 import (
            _detect_rivalry_angles,
        )

        # Both franchises "new" in 2020, meetings only from 2020 onward.
        # But league history extends back to 2010 — tenure filter WILL
        # engage because newer_start (2020) > earliest (2010). No prior
        # meetings to report.
        season_ctx, history_ctx, _m, tenure_map = _build_contexts(
            tenure_w=2020, tenure_l=2020,
            matchups_a_wins=4, matchups_b_wins=1,
            first_season=2010, last_season=2024,
        )
        matchups = [HistoricalMatchup(
            season=y, week=1,
            winner_id="0001" if y != 2020 else "0002",
            loser_id="0002" if y != 2020 else "0001",
            winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
        ) for y in range(2021, 2025)]
        # 4 wins for 0001 from 2021-2024 (all)
        matchups = [HistoricalMatchup(
            season=y, week=1, winner_id="0001", loser_id="0002",
            winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
        ) for y in range(2020, 2024)] + [HistoricalMatchup(
            season=2024, week=1, winner_id="0002", loser_id="0001",
            winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
        )]

        angles = _detect_rivalry_angles(season_ctx, history_ctx, matchups, tenure_map)
        if not angles:
            # Below thresholds — acceptable, skip.
            return
        angle = [a for a in angles if a.category == "RIVALRY"][0]

        # Scope prefix present because tenure filter fired.
        assert angle.headline.startswith("Under current ownership only: ")
        # No prior-era note because no prior meetings exist.
        assert "Prior era" not in angle.detail

    def test_all_time_case_unchanged(self):
        """When tenure_map is None or all-time applies, headlines are unchanged."""
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
        )
        from squadvault.core.recaps.context.narrative_angles_v1 import (
            _detect_rivalry_angles,
        )

        season_ctx, history_ctx, _m, _tm = _build_contexts(
            tenure_w=None, tenure_l=None,
            matchups_a_wins=10, matchups_b_wins=2,
        )
        matchups = (
            [HistoricalMatchup(
                season=y, week=1, winner_id="0001", loser_id="0002",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            ) for y in range(2010, 2020)]
            + [HistoricalMatchup(
                season=y, week=1, winner_id="0002", loser_id="0001",
                winner_score=100.0, loser_score=90.0, is_tie=False, margin=10.0,
            ) for y in range(2020, 2022)]
        )

        # No tenure map → all-time case.
        angles = _detect_rivalry_angles(season_ctx, history_ctx, matchups, None)
        rivalry = [a for a in angles if a.category == "RIVALRY"]
        assert len(rivalry) == 1
        angle = rivalry[0]

        # No scope prefix.
        assert not angle.headline.startswith("Under current ownership only: ")
        # Existing all-time format markers.
        assert "(all-time)" in angle.headline
        assert "leads the series" in angle.headline
        # No prior-era note in all-time case.
        assert "Prior era" not in angle.detail


# ── recap_verifier_v1: widened tenure-skip regex ─────────────────────


class TestVerifierTenureSkipPatterns:
    """The verifier's tenure-skip regex matches paraphrases of scope."""

    def _run_series_verify(self, recap_text, matchups, name_map):
        from squadvault.core.recaps.verification.recap_verifier_v1 import (
            verify_series_records,
        )
        return verify_series_records(recap_text, matchups, name_map)

    def _make_matchup(self, season, week, winner_id, loser_id):
        from squadvault.core.recaps.context.league_history_v1 import (
            HistoricalMatchup,
        )
        return HistoricalMatchup(
            season=season, week=week,
            winner_id=winner_id, loser_id=loser_id,
            winner_score=100.0, loser_score=90.0,
            is_tie=False, margin=10.0,
        )

    def test_under_current_ownership_still_skips(self):
        """Backwards compat: the original 'under current ownership' still skips."""
        # All-time is Alpha 2-5 Beta, but prose claims Alpha 5-2 "under current ownership"
        matchups = [
            self._make_matchup(2015 + i, 1, "A", "B") for i in range(2)
        ] + [
            self._make_matchup(2017 + i, 1, "B", "A") for i in range(5)
        ]
        reverse = {
            "Alpha Team": "A", "alpha team": "A",
            "Beta Squad": "B", "beta squad": "B",
        }
        text = "Alpha Team leads the series 5-2 under current ownership over Beta Squad."
        failures = self._run_series_verify(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"skip should fire on 'under current ownership'; got: {series_failures}"
        )

    def test_bare_current_ownership_skips(self):
        """'in the current ownership era' triggers the skip.

        The original regex second alternative `current\\s+owner` already
        prefix-matches "current ownership" because "owner" is a literal
        substring of "ownership" — so this works without any regex
        change. Verified as protection against future refactors that
        might tighten the pattern.
        """
        matchups = [
            self._make_matchup(2015 + i, 1, "A", "B") for i in range(2)
        ] + [
            self._make_matchup(2017 + i, 1, "B", "A") for i in range(5)
        ]
        reverse = {
            "Alpha Team": "A", "alpha team": "A",
            "Beta Squad": "B", "beta squad": "B",
        }
        # "leads the series 5-2" triggers the series-record pattern.
        # "current ownership" sits within the 80-char post-window.
        text = (
            "Alpha Team leads the series 5-2 in the current ownership era "
            "against Beta Squad."
        )
        failures = self._run_series_verify(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"bare 'current ownership' should trigger skip; got: {series_failures}"
        )

    def test_tenure_keyword_still_skips(self):
        """Backwards compat: 'tenure' still skips."""
        matchups = [
            self._make_matchup(2015 + i, 1, "A", "B") for i in range(2)
        ] + [
            self._make_matchup(2017 + i, 1, "B", "A") for i in range(5)
        ]
        reverse = {
            "Alpha Team": "A", "alpha team": "A",
            "Beta Squad": "B", "beta squad": "B",
        }
        text = "During Pat's tenure, Alpha Team leads the series 5-2 vs Beta Squad."
        failures = self._run_series_verify(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert series_failures == [], (
            f"'tenure' keyword should trigger skip; got: {series_failures}"
        )

    def test_no_scope_qualifier_still_fails(self):
        """Negative control: without scope language, a wrong record still fails.

        Note: verifier accepts either direction (A beats B or B beats A),
        so the claimed record must not match reversed — use 6-1 against
        actual 2-5 (neither 6-1 nor 1-6 matches).
        """
        # All-time: Alpha 2-5 Beta; prose claims "leads 6-1" with no scope.
        matchups = [
            self._make_matchup(2015 + i, 1, "A", "B") for i in range(2)
        ] + [
            self._make_matchup(2017 + i, 1, "B", "A") for i in range(5)
        ]
        reverse = {
            "Alpha Team": "A", "alpha team": "A",
            "Beta Squad": "B", "beta squad": "B",
        }
        text = "Alpha Team leads the all-time series 6-1 against Beta Squad."
        failures = self._run_series_verify(text, matchups, reverse)
        series_failures = [f for f in failures if f.category == "SERIES"]
        assert len(series_failures) == 1, (
            f"series failure should fire without scope; got: {series_failures}"
        )
