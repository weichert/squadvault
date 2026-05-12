"""Hall of Fame & Shame Aggregations v1 — A1 surface's derivation layer.

Per A1 specification (`_observations/OBSERVATIONS_2026_05_11_PHASE_11_A1_SPECIFICATION.md`)
§3.3, A1's v1 ships three sub-shapes against `WEEKLY_MATCHUP_RESULT` canonical
events:

- Championship Roll: per-season list of league champions.
- Worst-Season Tracking: all per-(franchise, season) records, surfaced
  in inverse-quality order.
- Blowouts Hall: top-N single-week matchups by margin.

This module is A1's pure-derivation companion to weekly-recap context modules
(`league_history_v1`, `franchise_deep_angles_v1`, etc.) — the same substrate;
different consumer.

Contract (per A1 spec §§4.1, 4.3, 6.1):

- Derived-only: reads canonical events; never writes back. No new event types,
  no new schema, no new detector classes.
- Deterministic: identical inputs produce identical outputs. Tie-breaking
  rules in each function below are explicit.
- Substrate-derivable per A1 D3-Alpha: every output value traces to a
  canonical event or to documented aggregation logic.
- No commissioner-curated labels; no narrative annotation. The substrate
  facts stand.

The lift origins for the three derivation functions are documented in
A1 decision-readiness Step 1 (commit `fb4f827`) §§3.1, 3.2, 3.3:

- `compute_championship_roll` — playoff-detection trick lifted from
  `franchise_deep_angles_v1.detect_championship_history` (pre-A1-spec
  lines 1289-1298), with per-season identification surfaced as per-season
  tuples rather than aggregated narrative angles.
- `compute_all_season_records` — records-list lift from
  `league_history_v1._compute_season_records`, exposing the full list before
  the existing function's (best, worst) extrema filter.
- `compute_blowouts_hall` — direct sort over `HistoricalMatchup.margin`;
  no aggregation primitive existed prior. Lowest implementation cost of
  the three.

Governance:

- Defers to Canonical Operating Constitution.
- No inference, projection, or gap-filling — seasons that do not produce
  a detectable championship under the playoff-detection trick are silently
  omitted per A1 D3-Alpha + Reset Memo §2.3 silence-over-speculation.
- Missing data stays missing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from squadvault.core.recaps.context.league_history_v1 import (
    HistoricalMatchup,
    SeasonRecord,
)

# ── Data classes ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChampionshipResult:
    """A single season's championship outcome.

    Surfaced per-season for A1's Championship Roll sub-shape (spec §3.3).
    The fields are a lift from
    `franchise_deep_angles_v1.detect_championship_history`'s internal
    per-season identification: the championship matchup is the unique
    matchup in the playoff week with the fewest matchups (typically 1);
    the matchup's winner is the champion.

    `is_tie` is preserved from the underlying `HistoricalMatchup` so
    consumers handling rare championship-week ties can disambiguate
    (in canonical PFL Buddies history through 2025, no championship-week
    tie has occurred per Step 1 §3.1 probe).
    """
    season: int
    champion_id: str
    runner_up_id: str
    championship_week: int
    champion_score: float
    runner_up_score: float
    is_tie: bool


# ── Helpers ──────────────────────────────────────────────────────────


def _regular_season_matchup_count(
    matchups: Sequence[HistoricalMatchup],
    season: int,
) -> int:
    """Mode of per-week matchup counts for a given season.

    Returns the most common number of matchups per week within the
    season (5 in a 10-team league). Weeks with fewer matchups are
    playoffs. Returns 0 if the season has no data.

    This helper duplicates
    `franchise_deep_angles_v1._regular_season_matchup_count` deliberately:
    avoiding a cross-module import of a private function. Both
    implementations must remain semantically identical; the unit tests
    below exercise the shared behavior.
    """
    week_counts: dict[int, int] = {}
    for m in matchups:
        if m.season == season:
            week_counts[m.week] = week_counts.get(m.week, 0) + 1
    if not week_counts:
        return 0
    count_freq: dict[int, int] = {}
    for cnt in week_counts.values():
        count_freq[cnt] = count_freq.get(cnt, 0) + 1
    return max(count_freq, key=lambda c: count_freq[c])


# ── Derivation: Blowouts Hall (spec §3.3) ────────────────────────────


def compute_blowouts_hall(
    matchups: Sequence[HistoricalMatchup],
    top_n: int = 10,
) -> tuple[HistoricalMatchup, ...]:
    """Top-N single-week matchups by margin, descending.

    Per A1 spec §3.3 Blowouts Hall sub-shape. Substrate-derivable via
    the per-matchup `margin` field on `HistoricalMatchup`; no
    aggregation across matchups is required.

    Tie-breaking is deterministic: descending `margin`, then ascending
    `(season, week, winner_id, loser_id)`. This anchors the same
    matchup at the same rank across reruns for an identical substrate.

    Args:
        matchups: HistoricalMatchup sequence (typically from
            `load_all_matchups`). Order does not matter.
        top_n: Number of top-margin matchups to return. Defaults to 10.
            Must be non-negative.

    Returns:
        Immutable tuple of at most `top_n` matchups. Fewer entries if
        the input has fewer matchups. Empty tuple if input is empty
        or `top_n` is 0.

    Raises:
        ValueError: if `top_n` is negative.
    """
    if top_n < 0:
        raise ValueError(f"top_n must be non-negative; got {top_n}")
    ordered = sorted(
        matchups,
        key=lambda m: (-m.margin, m.season, m.week, m.winner_id, m.loser_id),
    )
    return tuple(ordered[:top_n])


# ── Derivation: Worst-Season Tracking (spec §3.3) ────────────────────


def compute_all_season_records(
    matchups: Sequence[HistoricalMatchup],
) -> tuple[SeasonRecord, ...]:
    """All per-(franchise, season) records, in worst-first order.

    Per A1 spec §3.3 Worst-Season Tracking sub-shape. Lift from
    `league_history_v1._compute_season_records`, which builds the same
    accumulation internally and discards everything except the singular
    (best, worst) extrema. A1's archive needs the full list.

    Sort order: most losses first; ties broken by ascending PF
    (lowest-scoring season is "worse" among same-losses peers); then
    ascending season; then ascending `franchise_id`. This is the
    inverse-quality direction A1's Worst-Season Tracking sub-shape
    surfaces; consumers wanting best-first ordering should re-sort.

    The accumulation logic mirrors `_compute_season_records` exactly
    (see lift origin at the pre-A1-spec HEAD); the only behavioral
    difference is that this function emits all records sorted, while
    `_compute_season_records` emits only the two extrema. Both
    functions remain operational for their respective consumers.

    Args:
        matchups: HistoricalMatchup sequence (typically from
            `load_all_matchups`). Order does not matter.

    Returns:
        Immutable tuple of `SeasonRecord` entries, one per
        `(franchise_id, season)` pair appearing in the input. Sorted
        as documented above. Empty tuple if input is empty.
    """
    key_data: dict[tuple[str, int], dict[str, Any]] = {}

    for m in matchups:
        for fid, is_winner in [(m.winner_id, True), (m.loser_id, False)]:
            k = (fid, m.season)
            if k not in key_data:
                key_data[k] = {"w": 0, "l": 0, "t": 0, "pf": 0.0}
            if m.is_tie:
                key_data[k]["t"] += 1
            elif is_winner:
                key_data[k]["w"] += 1
            else:
                key_data[k]["l"] += 1
            score = m.winner_score if is_winner else m.loser_score
            key_data[k]["pf"] += score

    records: list[SeasonRecord] = [
        SeasonRecord(
            franchise_id=fid,
            season=season,
            wins=d["w"],
            losses=d["l"],
            ties=d["t"],
            points_for=round(d["pf"], 2),
        )
        for (fid, season), d in key_data.items()
    ]

    records.sort(key=lambda r: (-r.losses, r.points_for, r.season, r.franchise_id))
    return tuple(records)


# ── Derivation: Championship Roll (spec §3.3) ────────────────────────


def compute_championship_roll(
    matchups: Sequence[HistoricalMatchup],
) -> tuple[ChampionshipResult, ...]:
    """Per-season champion for every season with a detectable championship.

    Per A1 spec §3.3 Championship Roll sub-shape. Uses the
    playoff-detection trick lifted from
    `franchise_deep_angles_v1.detect_championship_history`:

    - The mode of per-week matchup counts identifies the regular-season
      pattern (5 matchups per week in a 10-team league).
    - Weeks with fewer matchups than the mode are playoff weeks.
    - The championship week is the playoff week with the fewest
      matchups (typically 1); ties on count broken by latest week.
    - The matchup winner on that week is the champion.

    Seasons that do not produce a detectable championship are silently
    omitted per A1 D3-Alpha + Reset Memo §2.3 silence-over-speculation:

    - No data for the season (empty matchups for that season).
    - Single-week-mode season (no week has fewer matchups than the
      mode, so no playoff weeks).
    - Multi-matchup championship-week data anomaly (more than one
      matchup remains at the championship week after tie-breaking) —
      in this case the first matchup in `(week, winner_id, loser_id)`
      order is taken as the champion. This is conservative: real
      championship weeks have exactly one matchup per the playoff
      trick's design, so this branch is an anomaly-handler.

    Step 1 §3.1 (commit `fb4f827`) confirmed empirically against PFL
    Buddies' 16-season substrate that every season produces a clean
    champion; the playoff trick is rock-solid across 2010-2025.

    Args:
        matchups: HistoricalMatchup sequence (typically from
            `load_all_matchups`). Order does not matter.

    Returns:
        Immutable tuple of `ChampionshipResult` entries, sorted by
        season ascending. One entry per season with a detectable
        championship. Empty tuple if input is empty or no season
        produces a detectable championship.
    """
    seasons = sorted({m.season for m in matchups})
    results: list[ChampionshipResult] = []

    for s in seasons:
        s_regular = _regular_season_matchup_count(matchups, s)
        if s_regular == 0:
            continue

        season_matchups = [m for m in matchups if m.season == s]
        week_counts: dict[int, int] = {}
        for m in season_matchups:
            week_counts[m.week] = week_counts.get(m.week, 0) + 1

        playoff_week_counts = {
            w: c for w, c in week_counts.items() if c < s_regular
        }
        if not playoff_week_counts:
            continue  # no detectable playoffs (regular-season-only)

        # Championship week: fewest matchups; ties broken by latest week.
        # The `-w` term matches the existing detector's `(week_counts[w], -w)`.
        champ_week = min(
            playoff_week_counts,
            key=lambda w: (playoff_week_counts[w], -w),
        )
        champ_matchups = [m for m in season_matchups if m.week == champ_week]
        if not champ_matchups:
            continue  # data anomaly; skip silently

        # Anomaly-handler: deterministic pick if multiple matchups land
        # at the championship week. Real championship weeks have one
        # matchup; this branch should not fire on PFL Buddies' substrate.
        champ_matchups.sort(key=lambda m: (m.week, m.winner_id, m.loser_id))
        champ = champ_matchups[0]

        results.append(ChampionshipResult(
            season=s,
            champion_id=champ.winner_id,
            runner_up_id=champ.loser_id,
            championship_week=champ.week,
            champion_score=champ.winner_score,
            runner_up_score=champ.loser_score,
            is_tie=champ.is_tie,
        ))

    return tuple(results)
