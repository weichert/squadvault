"""Tests for League History Context v1 — cross-season longitudinal derivation.

Uses multi-season synthetic matchup data to verify all-time records,
head-to-head, streaks spanning seasons, scoring records, and best/worst seasons.
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

from squadvault.core.recaps.context.league_history_v1 import (
    AllTimeRecord,
    HeadToHeadRecord,
    HistoricalMatchup,
    LeagueHistoryContextV1,
    StreakRecord,
    _compute_all_time_records,
    _compute_longest_streaks,
    _compute_scoring_records,
    _compute_season_records,
    build_cross_season_name_resolver,
    compute_head_to_head,
    derive_league_history_v1,
    load_all_matchups,
    render_league_history_for_prompt,
    resolve_franchise_name_any_season,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)

LEAGUE = "test_league"


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_matchup(
    con, *, league_id, season, week, winner_id, loser_id,
    winner_score, loser_score, is_tie=False,
):
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": is_tie,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"m_{league_id}_{season}_{week}_{winner_id}_{loser_id}"

    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_MATCHUP_RESULT",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_MATCHUP_RESULT",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


def _seed_multi_season(con, league_id=LEAGUE):
    """Seed 2 seasons of data for 4 teams.

    Season 2023 (3 weeks):
      W1: A beats B 120-100, C beats D 95-90
      W2: A beats C 110-105, B beats D 115-80
      W3: A beats D 130-70,  C beats B 100-98

    Season 2024 (3 weeks):
      W1: B beats A 105-100, C beats D 92-88
      W2: A beats B 140-90,  D beats C 110-105
      W3: A beats C 125-120, B beats D 108-95

    After all:
      A: 2023=3-0, 2024=2-1 → all-time 5-1
      B: 2023=1-2, 2024=2-1 → all-time 3-3
      C: 2023=2-1, 2024=1-2 → all-time 3-3
      D: 2023=0-3, 2024=1-2 → all-time 1-5
    """
    games = [
        # (season, week, winner, loser, w_score, l_score)
        (2023, 1, "A", "B", 120.0, 100.0),
        (2023, 1, "C", "D", 95.0, 90.0),
        (2023, 2, "A", "C", 110.0, 105.0),
        (2023, 2, "B", "D", 115.0, 80.0),
        (2023, 3, "A", "D", 130.0, 70.0),
        (2023, 3, "C", "B", 100.0, 98.0),
        (2024, 1, "B", "A", 105.0, 100.0),
        (2024, 1, "C", "D", 92.0, 88.0),
        (2024, 2, "A", "B", 140.0, 90.0),
        (2024, 2, "D", "C", 110.0, 105.0),
        (2024, 3, "A", "C", 125.0, 120.0),
        (2024, 3, "B", "D", 108.0, 95.0),
    ]
    for s, w, winner, loser, ws, ls in games:
        _insert_matchup(
            con, league_id=league_id, season=s, week=w,
            winner_id=winner, loser_id=loser,
            winner_score=ws, loser_score=ls,
        )
    con.commit()


def _seed_franchise_names(con, league_id=LEAGUE):
    """Seed franchise names across seasons (name changes between seasons)."""
    names = [
        (league_id, 2023, "A", "Alpha Squad"),
        (league_id, 2023, "B", "Beta Bombers"),
        (league_id, 2023, "C", "Charlie's Angels"),
        (league_id, 2023, "D", "Delta Dogs"),
        (league_id, 2024, "A", "Gopher Boys"),      # renamed
        (league_id, 2024, "B", "Hoosier Daddy"),     # renamed
        (league_id, 2024, "C", "Charlie's Angels"),   # kept name
        (league_id, 2024, "D", "Delta Dynasty"),      # renamed
    ]
    for lid, season, fid, name in names:
        con.execute(
            "INSERT OR REPLACE INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
            (lid, season, fid, name),
        )
    con.commit()


# ── Unit: all-time records ───────────────────────────────────────────


class TestAllTimeRecords:
    def _matchups(self):
        return [
            HistoricalMatchup(2023, 1, "A", "B", 120, 100, False, 20),
            HistoricalMatchup(2023, 2, "A", "C", 110, 105, False, 5),
            HistoricalMatchup(2024, 1, "B", "A", 105, 100, False, 5),
            HistoricalMatchup(2024, 2, "A", "B", 140, 90, False, 50),
        ]

    def test_cross_season_accumulation(self):
        records = _compute_all_time_records(self._matchups())
        assert records["A"].total_wins == 3
        assert records["A"].total_losses == 1
        assert records["A"].seasons_active == (2023, 2024)
        assert records["B"].total_wins == 1
        assert records["B"].total_losses == 2

    def test_points_accumulate(self):
        records = _compute_all_time_records(self._matchups())
        # A: scored 120+110+100+140=470
        assert records["A"].total_points_for == 470.0


# ── Unit: head-to-head ───────────────────────────────────────────────


class TestHeadToHead:
    def _matchups(self):
        return [
            HistoricalMatchup(2023, 1, "A", "B", 120, 100, False, 20),
            HistoricalMatchup(2023, 2, "A", "C", 110, 105, False, 5),
            HistoricalMatchup(2024, 1, "B", "A", 105, 100, False, 5),
            HistoricalMatchup(2024, 2, "A", "B", 140, 90, False, 50),
        ]

    def test_a_vs_b(self):
        h2h = compute_head_to_head(self._matchups(), "A", "B")
        assert h2h.a_wins == 2  # A beat B twice
        assert h2h.b_wins == 1  # B beat A once
        assert h2h.total_meetings == 3

    def test_chronological_order(self):
        h2h = compute_head_to_head(self._matchups(), "A", "B")
        assert len(h2h.meetings) == 3
        assert h2h.meetings[0].season == 2023  # first meeting
        assert h2h.meetings[2].season == 2024  # last meeting

    def test_no_meetings(self):
        h2h = compute_head_to_head(self._matchups(), "B", "C")
        assert h2h.total_meetings == 0

    def test_symmetry(self):
        """A vs B and B vs A should report same data."""
        h2h_ab = compute_head_to_head(self._matchups(), "A", "B")
        h2h_ba = compute_head_to_head(self._matchups(), "B", "A")
        assert h2h_ab.a_wins == h2h_ba.b_wins
        assert h2h_ab.b_wins == h2h_ba.a_wins
        assert h2h_ab.total_meetings == h2h_ba.total_meetings


# ── Unit: cross-season streaks ───────────────────────────────────────


class TestCrossSeasonStreaks:
    def test_streak_spans_seasons(self):
        """A wins last 2 of 2023, first 1 of 2024 → 3-game win streak."""
        matchups = [
            HistoricalMatchup(2023, 2, "A", "C", 110, 105, False, 5),
            HistoricalMatchup(2023, 3, "A", "D", 130, 70, False, 60),
            HistoricalMatchup(2024, 1, "A", "B", 105, 100, False, 5),
            HistoricalMatchup(2024, 2, "B", "A", 110, 100, False, 10),
        ]
        win, loss = _compute_longest_streaks(matchups)
        assert win is not None
        assert win.franchise_id == "A"
        assert win.length == 3
        assert win.start_season == 2023
        assert win.end_season == 2024

    def test_tie_ends_streak(self):
        matchups = [
            HistoricalMatchup(2023, 1, "A", "B", 100, 90, False, 10),
            HistoricalMatchup(2023, 2, "A", "B", 95, 95, True, 0),
            HistoricalMatchup(2023, 3, "A", "C", 110, 100, False, 10),
        ]
        win, _ = _compute_longest_streaks(matchups)
        # Streak is 1 (after tie), not 2 (tie breaks the first streak)
        assert win is not None
        assert win.length == 1

    def test_loss_streak(self):
        matchups = [
            HistoricalMatchup(2023, 1, "A", "D", 100, 90, False, 10),
            HistoricalMatchup(2023, 2, "A", "D", 110, 80, False, 30),
            HistoricalMatchup(2023, 3, "A", "D", 120, 70, False, 50),
        ]
        _, loss = _compute_longest_streaks(matchups)
        assert loss is not None
        assert loss.franchise_id == "D"
        assert loss.length == 3


# ── Unit: scoring records ────────────────────────────────────────────


class TestScoringRecords:
    def test_all_time_high_across_seasons(self):
        matchups = [
            HistoricalMatchup(2023, 1, "A", "B", 120, 100, False, 20),
            HistoricalMatchup(2024, 2, "A", "B", 155, 90, False, 65),
        ]
        high, low, avg = _compute_scoring_records(matchups)
        assert high.score == 155.0
        assert high.season == 2024
        assert low.score == 90.0
        assert avg is not None


# ── Unit: best/worst seasons ─────────────────────────────────────────


class TestSeasonRecords:
    def test_best_worst(self):
        matchups = [
            HistoricalMatchup(2023, 1, "A", "B", 120, 100, False, 20),
            HistoricalMatchup(2023, 2, "A", "C", 110, 105, False, 5),
            HistoricalMatchup(2023, 3, "A", "D", 130, 70, False, 60),
            HistoricalMatchup(2024, 1, "B", "A", 105, 100, False, 5),
            HistoricalMatchup(2024, 2, "B", "A", 110, 100, False, 10),
        ]
        best, worst = _compute_season_records(matchups)
        assert best.franchise_id == "A"
        assert best.season == 2023
        assert best.wins == 3
        assert best.losses == 0
        assert worst.losses >= 2


# ── Integration: full derivation ─────────────────────────────────────


class TestDeriveLeagueHistory:
    def test_multi_season(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_multi_season(con)
        con.close()

        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=3,
        )

        assert ctx.has_history
        assert ctx.is_multi_season
        assert ctx.seasons_available == (2023, 2024)
        assert ctx.total_matchups_all_time == 12

        # A is all-time leader: 5-1
        assert ctx.all_time_records[0].franchise_id == "A"
        assert ctx.all_time_records[0].total_wins == 5
        assert ctx.all_time_records[0].total_losses == 1

        # All-time high: A scored 140 in 2024 W2
        assert ctx.all_time_high is not None
        assert ctx.all_time_high.score == 140.0
        assert ctx.all_time_high.franchise_id == "A"

        # All-time low: D scored 70 in 2023 W3
        assert ctx.all_time_low is not None
        assert ctx.all_time_low.score == 70.0
        assert ctx.all_time_low.franchise_id == "D"

    def test_single_season(self, tmp_path):
        """With only one season, still produces valid context."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=2024, week=1,
                        winner_id="A", loser_id="B", winner_score=100, loser_score=90)
        con.commit()
        con.close()

        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=1,
        )
        assert ctx.has_history
        assert not ctx.is_multi_season
        assert ctx.seasons_available == (2024,)

    def test_no_data(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=1,
        )
        assert not ctx.has_history
        assert ctx.all_time_records == ()

    def test_deterministic(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_multi_season(con)
        con.close()

        ctx1 = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=3,
        )
        ctx2 = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=3,
        )
        assert ctx1 == ctx2


# ── Addendum conformance: as-of-week temporal scoping ────────────────
#
# The following tests are the behavioral expression of the Weekly Recap
# Context Temporal Scoping Addendum (v1.0) Hard Invariant: derived context
# composed into a weekly recap for approved week (season, week) must reflect
# ledger state as of that week's approved end — inclusive of that week,
# exclusive of every subsequent week. Regenerating a prior week's recap
# against a grown ledger must yield the same derived context block as the
# original generation.


def _seed_cutoff_fixture(
    con, league_id=LEAGUE, *, through_season: int, through_week: int,
):
    """Seed a 4-team fixture spanning 2024 W1–17 and 2025 W1–18.

    Only games at or before (through_season, through_week) are inserted.
    Callers set this to 2025 W18 for the full fixture, or to an earlier
    cutoff to simulate a ledger that has not yet grown past that point.

    Fixture invariants (relative to the full ledger):
    - Franchise D has a 15-game cross-season loss streak ending 2025 W14
      (2024 W17 plus 2025 W1–W14). At as_of=(2025, 13) the streak is
      only 14 games and does not terminate at W14.
    - Franchise A finishes 2025 with a 16-2 record. Reaching 16 wins
      requires W14–W18 to exist; at as_of=(2025, 13) A's 2025 record
      is at most 13-0.
    - Franchise B posts an all-time-high score of 250.0 in 2025 W17.
      At as_of=(2025, 13) that row is excluded and the highest score
      in the ledger is materially lower.
    """
    all_games: list[tuple[int, int, str, str, float, float]] = []

    # 2024 W1–W16: A beats B; D beats C. D accumulates wins so the loss
    # streak has a defined starting point at 2024 W17.
    for w in range(1, 17):
        all_games.append((2024, w, "A", "B", 120.0, 100.0))
        all_games.append((2024, w, "D", "C", 95.0, 85.0))
    # 2024 W17: D loses — streak begins here.
    all_games.append((2024, 17, "A", "D", 115.0, 80.0))
    all_games.append((2024, 17, "B", "C", 110.0, 105.0))

    # 2025 W1–W14: D loses every week. Streak hits 15 at end of W14.
    # A wins all 14 of these; key to reaching the 16-2 end state.
    for w in range(1, 15):
        all_games.append((2025, w, "A", "D", 125.0, 78.0))
        all_games.append((2025, w, "B", "C", 115.0, 95.0))
    # 2025 W15: D finally wins — streak ends at length 15.
    all_games.append((2025, 15, "D", "A", 105.0, 100.0))
    all_games.append((2025, 15, "B", "C", 115.0, 95.0))
    # 2025 W16
    all_games.append((2025, 16, "A", "B", 120.0, 100.0))
    all_games.append((2025, 16, "C", "D", 110.0, 90.0))
    # 2025 W17: B posts the all-time-high score.
    all_games.append((2025, 17, "B", "A", 250.0, 100.0))
    all_games.append((2025, 17, "C", "D", 110.0, 90.0))
    # 2025 W18: A closes its 16-2 line.
    all_games.append((2025, 18, "A", "B", 120.0, 100.0))
    all_games.append((2025, 18, "C", "D", 110.0, 90.0))

    for s, w, winner, loser, ws, ls in all_games:
        if s < through_season or (s == through_season and w <= through_week):
            _insert_matchup(
                con, league_id=league_id, season=s, week=w,
                winner_id=winner, loser_id=loser,
                winner_score=ws, loser_score=ls,
            )
    con.commit()


class TestAsOfCutoffCorrectness:
    """No derivation at cutoff may reference data from beyond the cutoff."""

    def test_loader_excludes_post_cutoff_matchups(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_cutoff_fixture(con, through_season=2025, through_week=18)
        con.close()

        # Sanity: without a cutoff, the full ledger loads.
        all_rows = load_all_matchups(db_path, LEAGUE)
        post_cutoff_all = [
            m for m in all_rows
            if m.season > 2025 or (m.season == 2025 and m.week > 13)
        ]
        assert len(post_cutoff_all) > 0, \
            "fixture regression: post-cutoff data is missing from the ledger"

        # With cutoff: no post-cutoff rows escape the filter.
        cut_rows = load_all_matchups(
            db_path, LEAGUE,
            as_of_season=2025, as_of_week=13,
        )
        post_cutoff_cut = [
            m for m in cut_rows
            if m.season > 2025 or (m.season == 2025 and m.week > 13)
        ]
        assert post_cutoff_cut == [], (
            "load_all_matchups leaked post-cutoff rows: "
            f"{[(m.season, m.week, m.winner_id, m.loser_id) for m in post_cutoff_cut]}"
        )

    def test_loader_mismatched_cutoff_args_raises(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        with pytest.raises(ValueError):
            load_all_matchups(db_path, LEAGUE, as_of_season=2025)  # type: ignore[call-arg]
        with pytest.raises(ValueError):
            load_all_matchups(db_path, LEAGUE, as_of_week=13)  # type: ignore[call-arg]

    def test_loss_streak_does_not_terminate_past_cutoff(self, tmp_path):
        """The 15-game streak ending 2025 W14 must not appear at as_of=(2025, 13)."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_cutoff_fixture(con, through_season=2025, through_week=18)
        con.close()

        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2025, as_of_week=13,
        )

        streaks = [s for s in (ctx.longest_win_streak, ctx.longest_loss_streak) if s is not None]
        past_cutoff_streaks = [
            s for s in streaks
            if s.end_season > 2025 or (s.end_season == 2025 and s.end_week > 13)
        ]
        assert past_cutoff_streaks == [], (
            "streak ends past cutoff: "
            f"{[(s.streak_type, s.length, s.end_season, s.end_week) for s in past_cutoff_streaks]}"
        )

        # Specific assertion against the fixture's post-cutoff 15-game streak.
        loss = ctx.longest_loss_streak
        if loss is not None:
            assert not (loss.length == 15 and loss.end_season == 2025 and loss.end_week == 14), (
                "longest_loss_streak at cutoff matches the fixture's post-cutoff "
                f"15-game streak ending 2025 W14: {loss!r}"
            )

    def test_best_season_record_does_not_span_post_cutoff_weeks(self, tmp_path):
        """best_season_record cannot reflect games that happened after cutoff."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_cutoff_fixture(con, through_season=2025, through_week=18)
        con.close()

        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2025, as_of_week=13,
        )

        offending = [
            r for r in (ctx.best_season_record, ctx.worst_season_record)
            if r is not None
            and r.season == 2025
            and (r.wins + r.losses + r.ties) > 13
        ]
        assert offending == [], (
            "best/worst season record spans post-cutoff weeks: "
            f"{[(r.franchise_id, r.season, r.wins, r.losses, r.ties) for r in offending]}"
        )

        # Specific assertion against the fixture's 16-2 end-state for A.
        best = ctx.best_season_record
        if best is not None:
            assert not (best.season == 2025 and best.wins == 16 and best.losses == 2), (
                "best_season_record at cutoff matches the fixture's post-cutoff "
                f"16-2 end state: {best!r}"
            )

    def test_scoring_record_not_from_post_cutoff_week(self, tmp_path):
        """The 250.0 score posted 2025 W17 must not be all_time_high at as_of=(2025, 13)."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_cutoff_fixture(con, through_season=2025, through_week=18)
        con.close()

        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2025, as_of_week=13,
        )

        offending = [
            r for r in (ctx.all_time_high, ctx.all_time_low)
            if r is not None
            and (r.season > 2025 or (r.season == 2025 and r.week > 13))
        ]
        assert offending == [], (
            "scoring record sourced from post-cutoff week: "
            f"{[(r.label, r.season, r.week, r.score) for r in offending]}"
        )

        high = ctx.all_time_high
        if high is not None:
            assert high.score != 250.0, (
                "all_time_high at cutoff equals the fixture's post-cutoff value 250.0"
            )


class TestRegenReproducibility:
    """A recap regenerated later must yield the same LEAGUE_HISTORY block.

    This is the behavioral expression of the addendum's Hard Invariant:
    the immutability guarantee attaches to the week as a temporal window,
    not to the first approved artifact alone.
    """

    def test_grown_ledger_preserves_as_of_derivation(self, tmp_path):
        db_path = _fresh_db(tmp_path)

        # First generation: ledger contains only through-W13 data.
        con = sqlite3.connect(db_path)
        _seed_cutoff_fixture(con, through_season=2025, through_week=13)
        con.close()

        ctx_first = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2025, as_of_week=13,
        )
        assert ctx_first.has_history, (
            "fixture regression: through-W13 seed produced empty history"
        )

        # Ledger grows: add all of W14–W18 for 2025.
        # Inline delta — cannot re-call _seed_cutoff_fixture because
        # the UNIQUE(external_source, external_id) index would reject
        # overlapping rows.
        remainder = [
            (2025, 14, "A", "D", 125.0, 78.0),
            (2025, 14, "B", "C", 115.0, 95.0),
            (2025, 15, "D", "A", 105.0, 100.0),
            (2025, 15, "B", "C", 115.0, 95.0),
            (2025, 16, "A", "B", 120.0, 100.0),
            (2025, 16, "C", "D", 110.0, 90.0),
            (2025, 17, "B", "A", 250.0, 100.0),
            (2025, 17, "C", "D", 110.0, 90.0),
            (2025, 18, "A", "B", 120.0, 100.0),
            (2025, 18, "C", "D", 110.0, 90.0),
        ]
        con = sqlite3.connect(db_path)
        for s, w, winner, loser, ws, ls in remainder:
            _insert_matchup(
                con, league_id=LEAGUE, season=s, week=w,
                winner_id=winner, loser_id=loser,
                winner_score=ws, loser_score=ls,
            )
        con.commit()
        con.close()

        # Regenerate the recap for the same approved week against the grown ledger.
        ctx_regen = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2025, as_of_week=13,
        )

        assert ctx_first == ctx_regen, (
            "LEAGUE_HISTORY derivation at as_of=(2025, 13) changed after the "
            "ledger grew — violates the Weekly Recap Context Temporal Scoping "
            "Addendum Hard Invariant"
        )


# ── Integration: franchise name resolution ───────────────────────────


class TestCrossSeasonNames:
    def test_most_recent_name_wins(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_franchise_names(con)
        con.close()

        name = resolve_franchise_name_any_season(db_path, LEAGUE, "A")
        assert name == "Gopher Boys"  # 2024 name, not 2023 "Alpha Squad"

    def test_unchanged_name(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_franchise_names(con)
        con.close()

        name = resolve_franchise_name_any_season(db_path, LEAGUE, "C")
        assert name == "Charlie's Angels"  # same in both seasons

    def test_unknown_franchise(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        name = resolve_franchise_name_any_season(db_path, LEAGUE, "ZZZZZ")
        assert name == "ZZZZZ"  # fallback to raw ID

    def test_build_name_map(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_franchise_names(con)
        con.close()

        name_map = build_cross_season_name_resolver(db_path, LEAGUE)
        assert name_map["A"] == "Gopher Boys"
        assert name_map["B"] == "Hoosier Daddy"
        assert name_map["D"] == "Delta Dynasty"


# ── Integration: prompt rendering ────────────────────────────────────


class TestHistoryPromptRendering:
    def test_renders_multi_season(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _seed_multi_season(con)
        _seed_franchise_names(con)
        con.close()

        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=3,
        )
        name_map = build_cross_season_name_resolver(db_path, LEAGUE)
        text = render_league_history_for_prompt(ctx, name_map=name_map)

        assert "2 season(s)" in text
        assert "Gopher Boys" in text
        assert "All-time records:" in text
        assert "5-1" in text  # A's all-time record
        assert "Highest score ever:" in text
        assert "140.00" in text
        assert "Lowest score ever:" in text
        assert "70.00" in text

    def test_empty_renders_cleanly(self, tmp_path):
        db_path = _fresh_db(tmp_path)
        ctx = derive_league_history_v1(
            db_path=db_path, league_id=LEAGUE,
            as_of_season=2024, as_of_week=1,
        )
        text = render_league_history_for_prompt(ctx)
        assert "No league history" in text
