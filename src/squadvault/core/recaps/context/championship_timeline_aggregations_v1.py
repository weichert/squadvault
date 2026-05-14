"""Championship Timeline Aggregations v1 — A3 surface's derivation layer.

Per A3 specification (`_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_SPECIFICATION.md`)
§3.1, A3's v1 ships three sub-shapes against `WEEKLY_MATCHUP_RESULT`
canonical events, all derived via the playoff-detection trick:

- Per-Season Playoff Bracket: for each digital-era season, the full
  playoff bracket — every playoff-week matchup, grouped into rounds
  (preliminary → semifinal → championship). Generalizes
  `hall_of_fame_aggregations_v1.compute_championship_roll`, which
  narrows each season to the championship-week singleton; this module
  emits all playoff-week matchups per season. The post-2021 W17/W18
  duplicate championship rows are collapsed by content at the
  derivation layer (see `compute_playoff_bracket`).
- Cross-Season Playoff Records: all-time leaderboards across the
  digital era — per-franchise playoff-season appearances; per-franchise
  championship-matchup appearances; longest playoff-active streak;
  longest playoff-drought streak. The playoff-appearance count uses
  per-season set semantics (see `compute_cross_season_playoff_records`),
  NOT D39's internal per-matchup over-counting.
- Bridesmaids: cross-era championship-runner-up leaderboard, derived
  from `compute_championship_roll`'s `runner_up_id`. v1 ships the
  runner-up leg only; the "one-game-out-of-playoffs" almost leg
  (D50 `detect_the_almost`) is dropped from v1 per spec §3.7.

This module is A3's pure-derivation companion to weekly-recap context
modules (`league_history_v1`, `franchise_deep_angles_v1`, etc.) — the
same substrate; a different consumer (the browse-cadenced archive).

Contract (per A3 spec §§4.1, 4.3, 6.1):

- Derived-only: reads canonical events (via `HistoricalMatchup`
  sequences from `load_all_matchups`); never writes back. No new
  event types, no new schema, no new detector classes.
- Deterministic: identical inputs produce identical outputs.
  Tie-breaking rules in each function below are explicit.
- Substrate-derivable per A3 D3-Alpha: every output value traces to a
  canonical `WEEKLY_MATCHUP_RESULT` event or to documented aggregation
  logic. No commissioner-curated labels; no narrative annotation.

Dependency on `hall_of_fame_aggregations_v1` (A1's aggregation layer):

A3 intentionally and publicly depends on A1's module — `compute_playoff_bracket`
generalizes A1's `compute_championship_roll`, `compute_cross_season_playoff_records`
consumes `compute_championship_roll` for the championship dimension, and
`compute_bridesmaids` consumes A1's `ChampionshipResult` tuples. Because
that dependency edge already exists and is the whole point of A3
generalizing A1's primitive, this module also imports the *private*
helper `_regular_season_matchup_count` from `hall_of_fame_aggregations_v1`
rather than carrying a third copy. A1's commit message documented that
`_regular_season_matchup_count` was deliberately duplicated between
`franchise_deep_angles_v1` and `hall_of_fame_aggregations_v1` to avoid a
*cross-module* private import where no other dependency existed. A3's
situation is categorically different: the A3 → `hall_of_fame_aggregations_v1`
edge is already present and intentional, so riding it for the helper
adds no new coupling. A third verbatim copy would; this is the fourth
consumer of the playoff-detection trick (ARCHITECTURAL_AUDIT §8
entanglement hotspot #3), and promoting the helper to a shared
non-private location is the right *eventual* move — but that is a
separate refactor with its own topic, not part of A3's aggregation
layer.

Governance:

- Defers to Canonical Operating Constitution.
- No inference, projection, or gap-filling — seasons that do not
  produce detectable playoffs under the playoff-detection trick are
  silently omitted per A3 D3-Alpha + Reset Memo §2.3
  silence-over-speculation.
- Missing data stays missing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from squadvault.core.recaps.context.hall_of_fame_aggregations_v1 import (
    ChampionshipResult,
    _regular_season_matchup_count,
    compute_championship_roll,
)
from squadvault.core.recaps.context.league_history_v1 import HistoricalMatchup

# ── Round labels (spec §3.1 / §3.6) ──────────────────────────────────

#: Round labels assigned from the end of the bracket. Per A3 spec §3.1
#: and §3.6 the digital-era brackets present as a clean 3-round shape:
#: preliminary → semifinal → championship. The labels are assigned by
#: counting back from the last (fewest-matchups) playoff week.
ROUND_CHAMPIONSHIP = "Championship"
ROUND_SEMIFINAL = "Semifinal"
ROUND_PRELIMINARY = "Preliminary"


# ── Data classes ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlayoffRound:
    """One round of a single season's playoff bracket.

    `matchups` is the tuple of `HistoricalMatchup` records that occurred
    in this round's week, sorted by `(winner_id, loser_id)` for
    determinism. `round_label` is one of `ROUND_PRELIMINARY` /
    `ROUND_SEMIFINAL` / `ROUND_CHAMPIONSHIP`, or `"Round N"` for an
    anomalous bracket with more than three rounds (not expected on PFL
    Buddies' substrate; see `_label_for_round`).
    """
    season: int
    week: int
    round_label: str
    matchups: tuple[HistoricalMatchup, ...]


@dataclass(frozen=True)
class SeasonBracket:
    """A single season's full playoff bracket, earliest round first.

    Per A3 spec §3.1: the Per-Season Playoff Bracket sub-shape. `rounds`
    is ordered by week ascending — preliminary first, championship last.
    Post-2021 seasons have had their duplicate W17/W18 championship rows
    collapsed by content (spec §3.6 / §6.2) before round labeling, so
    both eras present as a clean 3-round bracket.
    """
    season: int
    rounds: tuple[PlayoffRound, ...]


@dataclass(frozen=True)
class FranchisePlayoffRecord:
    """Per-franchise cross-season playoff record (spec §3.1 / §3.8).

    All four dimensions ship at v1:

    - `playoff_season_count`: number of *seasons* the franchise
      appeared in any playoff week. Per-season set semantics — a
      franchise in N playoff weeks of one season counts as 1, not N
      (spec §3.8 / §6.3).
    - `championship_appearance_count`: number of seasons the franchise
      appeared in the championship matchup (as champion or runner-up).
    - `longest_active_streak`: longest run of calendar-consecutive
      seasons the franchise made the playoffs.
    - `longest_drought_streak`: longest run of calendar-consecutive
      seasons the franchise was active but missed the playoffs.
    """
    franchise_id: str
    playoff_season_count: int
    championship_appearance_count: int
    longest_active_streak: int
    longest_drought_streak: int


@dataclass(frozen=True)
class CrossSeasonPlayoffRecords:
    """All-time cross-season playoff records across the digital era.

    Per A3 spec §3.1 / §3.8 — A3's analog of A2's per-position-records
    subsection: a sub-shape with multiple internal dimensions. All four
    dimensions ship at v1; the streak dimensions are not gated.

    `per_franchise` is sorted by `playoff_season_count` descending, then
    `championship_appearance_count` descending, then
    `longest_active_streak` descending, then `franchise_id` ascending.
    The render layer re-sorts per dimension for the per-dimension
    leaderboards.

    `total_seasons` is the count of distinct seasons present in the
    input — the denominator for the render layer's "X of N seasons"
    framing.
    """
    per_franchise: tuple[FranchisePlayoffRecord, ...]
    total_seasons: int


@dataclass(frozen=True)
class BridesmaidRecord:
    """Per-franchise championship-runner-up record (spec §3.1 / §3.7).

    v1 ships the runner-up leg only. `championship_count` is carried
    alongside `runner_up_count` so the render layer can surface the
    perennial-bridesmaid archetype — a franchise with runner-up
    finishes and zero titles (spec §3.7 / §4.5).
    """
    franchise_id: str
    runner_up_count: int
    runner_up_seasons: tuple[int, ...]
    championship_count: int


# ── Helpers ──────────────────────────────────────────────────────────


def _label_for_round(idx: int, num_rounds: int) -> str:
    """Round label for the round at index `idx` of `num_rounds`, week-ascending.

    Labels are assigned by counting back from the last round (the
    fewest-matchups playoff week, typically the championship):

    - last round         → "Championship"
    - second-to-last     → "Semifinal"
    - third-to-last      → "Preliminary"
    - any earlier round  → "Round {idx + 1}"

    PFL Buddies' digital-era substrate produces exactly three rounds
    per season after the W17/W18 collapse (spec §3.6), so the
    "Round N" branch is anomaly-robustness only.
    """
    from_end = num_rounds - 1 - idx
    if from_end == 0:
        return ROUND_CHAMPIONSHIP
    if from_end == 1:
        return ROUND_SEMIFINAL
    if from_end == 2:
        return ROUND_PRELIMINARY
    return f"Round {idx + 1}"


def _matchup_content_key(
    matchups: Sequence[HistoricalMatchup],
) -> tuple[tuple[str, str, float, float], ...]:
    """Content signature of a week's matchups for the W17/W18 collapse rule.

    Per A3 spec §3.6 / §6.2: two consecutive playoff weeks are duplicates
    when they carry identical `(winner_id, loser_id, winner_score,
    loser_score)` tuples. Returns those tuples sorted, so the comparison
    is order-independent and multiset-aware.
    """
    return tuple(sorted(
        (m.winner_id, m.loser_id, m.winner_score, m.loser_score)
        for m in matchups
    ))


def _longest_consecutive_run(seasons: set[int]) -> int:
    """Length of the longest run of calendar-consecutive integers in `seasons`.

    Returns 0 for the empty set. Used for both the playoff-active streak
    (over a franchise's playoff seasons) and the playoff-drought streak
    (over a franchise's active-but-no-playoff seasons). Because both
    inputs are sets of actual seasons, a gap in a franchise's tenure is
    simply absent from the set and correctly breaks a run.
    """
    best = 0
    for s in seasons:
        if (s - 1) not in seasons:  # s starts a run
            length = 1
            while (s + length) in seasons:
                length += 1
            best = max(best, length)
    return best


def _playoff_weeks_for_season(
    matchups: Sequence[HistoricalMatchup],
    season: int,
) -> dict[int, list[HistoricalMatchup]]:
    """Map of playoff week → that week's matchups, for one season.

    A playoff week is a week whose matchup count is fewer than the
    season's regular-season mode (the playoff-detection trick). Returns
    an empty dict if the season has no data or no detectable playoff
    weeks.
    """
    s_regular = _regular_season_matchup_count(matchups, season)
    if s_regular == 0:
        return {}

    by_week: dict[int, list[HistoricalMatchup]] = {}
    for m in matchups:
        if m.season == season:
            by_week.setdefault(m.week, []).append(m)

    return {
        w: ms for w, ms in by_week.items() if len(ms) < s_regular
    }


# ── Derivation: Per-Season Playoff Bracket (spec §3.1) ───────────────


def compute_playoff_bracket(
    matchups: Sequence[HistoricalMatchup],
) -> tuple[SeasonBracket, ...]:
    """Full playoff bracket for every season with detectable playoffs.

    Per A3 spec §3.1 Per-Season Playoff Bracket sub-shape. Generalizes
    `hall_of_fame_aggregations_v1.compute_championship_roll`: where that
    function narrows each season to the championship-week singleton,
    this function emits *all* playoff-week matchups per season, grouped
    into rounds.

    Derivation:

    - The playoff-detection trick (`_regular_season_matchup_count`)
      identifies playoff weeks: weeks with fewer matchups than the
      season's regular-season mode.
    - The W17/W18 collapse-by-content rule (spec §3.6 / §6.2) is applied
      before round labeling: when two playoff weeks are consecutive in
      week number AND carry identical `(winner_id, loser_id,
      winner_score, loser_score)` content, the later week is dropped as
      a duplicate. This is content-based, not era-based — it is robust
      to substrate change (re-ingestion removing the duplication, or a
      genuine two-week structure with different scores appearing). It
      handles the post-2021 verbatim-identical championship rows; under
      collapse both eras present as a clean 3-round bracket.
    - The surviving playoff weeks are labeled by `_label_for_round`,
      counting back from the last week: Championship, Semifinal,
      Preliminary.

    Seasons with no detectable playoffs are silently omitted per A3
    D3-Alpha + Reset Memo §2.3 silence-over-speculation.

    Args:
        matchups: HistoricalMatchup sequence (typically from
            `load_all_matchups`). Order does not matter.

    Returns:
        Immutable tuple of `SeasonBracket` entries, sorted by season
        ascending. One entry per season with detectable playoffs.
        Empty tuple if input is empty or no season has detectable
        playoffs.
    """
    seasons = sorted({m.season for m in matchups})
    brackets: list[SeasonBracket] = []

    for s in seasons:
        playoff_weeks = _playoff_weeks_for_season(matchups, s)
        if not playoff_weeks:
            continue  # no detectable playoffs (regular-season-only / no data)

        ordered_weeks = sorted(playoff_weeks)

        # W17/W18 collapse-by-content (spec §3.6 / §6.2). Compare each
        # playoff week to the immediately-preceding playoff week in the
        # raw week-ascending sequence; drop the later week when the week
        # numbers are consecutive AND the matchup content is identical.
        # Comparing against the raw predecessor (not the last *kept*
        # week) means a hypothetical triple (W17 == W18 == W19) also
        # collapses correctly.
        kept_weeks: list[int] = [ordered_weeks[0]]
        for i in range(1, len(ordered_weeks)):
            w = ordered_weeks[i]
            prev = ordered_weeks[i - 1]
            same_content = (
                _matchup_content_key(playoff_weeks[w])
                == _matchup_content_key(playoff_weeks[prev])
            )
            if w == prev + 1 and same_content:
                continue  # duplicate of the prior week; drop
            kept_weeks.append(w)

        num_rounds = len(kept_weeks)
        rounds: list[PlayoffRound] = []
        for idx, w in enumerate(kept_weeks):
            week_matchups = tuple(sorted(
                playoff_weeks[w],
                key=lambda m: (m.winner_id, m.loser_id),
            ))
            rounds.append(PlayoffRound(
                season=s,
                week=w,
                round_label=_label_for_round(idx, num_rounds),
                matchups=week_matchups,
            ))

        brackets.append(SeasonBracket(season=s, rounds=tuple(rounds)))

    return tuple(brackets)


# ── Derivation: Cross-Season Playoff Records (spec §3.1 / §3.8) ───────


def compute_cross_season_playoff_records(
    matchups: Sequence[HistoricalMatchup],
) -> CrossSeasonPlayoffRecords:
    """Cross-season playoff records across the digital era.

    Per A3 spec §3.1 / §3.8 Cross-Season Playoff Records sub-shape.
    Four dimensions per franchise, all shipping at v1:

    1. Playoff-season appearances — **per-season set semantics** (spec
       §3.8 / §6.3). For each season, the set of franchises appearing
       in any playoff week is computed; each such franchise's count is
       incremented by exactly 1. This function does NOT consume D39's
       internal `playoff_appearances` dict, which increments
       per-matchup and silently over-counts (a franchise in 2 playoff
       weeks of one season would get +2). The invariant is specified
       explicitly so a future maintainer "lifting D39's logic" does not
       inherit the over-counting.
    2. Championship-matchup appearances — per franchise, the number of
       seasons it appeared in the championship matchup. Derived from
       `compute_championship_roll`'s `champion_id` / `runner_up_id`.
    3. Longest playoff-active streak — longest run of calendar-
       consecutive seasons the franchise made the playoffs.
    4. Longest playoff-drought streak — longest run of calendar-
       consecutive seasons the franchise was active (appeared in any
       matchup) but missed the playoffs.

    Args:
        matchups: HistoricalMatchup sequence (typically from
            `load_all_matchups`). Order does not matter.

    Returns:
        `CrossSeasonPlayoffRecords` with `per_franchise` sorted by
        playoff-season count descending, then championship-appearance
        count descending, then longest-active-streak descending, then
        franchise_id ascending. `total_seasons` is the count of
        distinct seasons in the input. An empty input yields an empty
        `per_franchise` tuple and `total_seasons == 0`.
    """
    seasons = sorted({m.season for m in matchups})

    # active_seasons: every season a franchise appeared in any matchup.
    active_seasons: dict[str, set[int]] = {}
    for m in matchups:
        for fid in (m.winner_id, m.loser_id):
            active_seasons.setdefault(fid, set()).add(m.season)

    # playoff_seasons: per-season set semantics (spec §3.8 / §6.3).
    playoff_seasons: dict[str, set[int]] = {}
    for s in seasons:
        playoff_weeks = _playoff_weeks_for_season(matchups, s)
        season_playoff_fids: set[str] = set()
        for week_matchups in playoff_weeks.values():
            for m in week_matchups:
                season_playoff_fids.add(m.winner_id)
                season_playoff_fids.add(m.loser_id)
        for fid in season_playoff_fids:
            playoff_seasons.setdefault(fid, set()).add(s)

    # championship appearances: from compute_championship_roll. Duplicate
    # W17/W18 rows carry identical franchises, so the per-season champion
    # / runner-up identification is unaffected by the duplication.
    champ_appearances: dict[str, int] = {}
    for result in compute_championship_roll(matchups):
        for fid in (result.champion_id, result.runner_up_id):
            champ_appearances[fid] = champ_appearances.get(fid, 0) + 1

    records: list[FranchisePlayoffRecord] = []
    for fid in sorted(active_seasons):
        fid_playoff = playoff_seasons.get(fid, set())
        fid_drought = active_seasons[fid] - fid_playoff
        records.append(FranchisePlayoffRecord(
            franchise_id=fid,
            playoff_season_count=len(fid_playoff),
            championship_appearance_count=champ_appearances.get(fid, 0),
            longest_active_streak=_longest_consecutive_run(fid_playoff),
            longest_drought_streak=_longest_consecutive_run(fid_drought),
        ))

    records.sort(key=lambda r: (
        -r.playoff_season_count,
        -r.championship_appearance_count,
        -r.longest_active_streak,
        r.franchise_id,
    ))

    return CrossSeasonPlayoffRecords(
        per_franchise=tuple(records),
        total_seasons=len(seasons),
    )


# ── Derivation: Bridesmaids (spec §3.1 / §3.7) ───────────────────────


def compute_bridesmaids(
    championship_roll: Sequence[ChampionshipResult],
) -> tuple[BridesmaidRecord, ...]:
    """Cross-era championship-runner-up leaderboard (runner-up leg only).

    Per A3 spec §3.1 / §3.7 Bridesmaids sub-shape. A clean group-by over
    `hall_of_fame_aggregations_v1.compute_championship_roll`'s output:
    the `runner_up_id` field is aggregated by franchise across the
    digital era. A3's Bridesmaids does NOT re-derive championships — it
    consumes A1's existing `compute_championship_roll` results, which
    the generation script computes once and threads through.

    v1 ships the runner-up leg ONLY. The "one-game-out-of-playoffs"
    almost leg (D50 `detect_the_almost`) is dropped from v1 on
    substrate-thinness grounds per spec §3.7 — it is a preserved
    future-expansion path, not a v1 deliverable, and is not implemented
    here.

    `championship_count` (titles) is carried alongside `runner_up_count`
    so the render layer can surface the perennial-bridesmaid archetype:
    a franchise with runner-up finishes and zero titles (spec §3.7 /
    §4.5).

    Args:
        championship_roll: `ChampionshipResult` sequence from
            `compute_championship_roll`. Order does not matter.

    Returns:
        Immutable tuple of `BridesmaidRecord`, one per franchise that
        appeared as a championship runner-up at least once, sorted by
        runner-up count descending, then championship count ascending
        (fewer titles ranks higher among equal runner-up counts — the
        bridesmaid signal), then franchise_id ascending. Empty tuple if
        no season has a runner-up (e.g. empty input).
    """
    runner_up_seasons: dict[str, list[int]] = {}
    title_counts: dict[str, int] = {}

    for result in championship_roll:
        runner_up_seasons.setdefault(result.runner_up_id, []).append(
            result.season
        )
        title_counts[result.champion_id] = (
            title_counts.get(result.champion_id, 0) + 1
        )

    records: list[BridesmaidRecord] = [
        BridesmaidRecord(
            franchise_id=fid,
            runner_up_count=len(seasons),
            runner_up_seasons=tuple(sorted(seasons)),
            championship_count=title_counts.get(fid, 0),
        )
        for fid, seasons in runner_up_seasons.items()
    ]

    records.sort(key=lambda r: (
        -r.runner_up_count,
        r.championship_count,
        r.franchise_id,
    ))

    return tuple(records)
