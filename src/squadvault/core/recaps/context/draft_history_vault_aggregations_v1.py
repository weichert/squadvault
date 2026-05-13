"""Draft History Vault Aggregations v1 - A2 surface's derivation layer.

Per A2 specification (`_observations/OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md`)
section 3.1, A2's v1 ships three sub-shapes against `DRAFT_PICK` plus
`WEEKLY_PLAYER_SCORE` canonical events:

- Auction-Most-Expensive History: overall record (all-time most-expensive
  pick across the auction era) plus per-position records (top-1 per
  position present in the substrate). Lift of D28's internal `pos_max`
  exposed publicly per section 3.8.
- Auction-Bust Hall: top-N cross-era picks ranked by combined severity
  signal `(season_league_starter_avg - player_avg) * bid_amount`, with
  `starter_weeks >= 4` and `player_avg < season_league_starter_avg * 0.5`
  as inclusion filters. Cross-season lift of D22's per-season logic at
  `auction_draft_angles_v1.detect_auction_bust`.
- Auction-Bargain Hall: top-N cross-era picks ranked by lowest
  `bid_amount / total_points` at a minimum-production threshold of
  `total_points >= 50`. Cross-season lift of D21 territory.

This module is A2's pure-derivation companion to the auction angle
detector module (`auction_draft_angles_v1`) - the same substrate;
different consumer. The angle detector renders per-season narrative
angles for the weekly recap pipeline; this module renders cross-era
aggregations for the A2 browse-cadenced archive.

Contract (per A2 spec sections 4.1, 4.3, 6.1):

- Derived-only: reads `AuctionPick` and `PlayerSeasonScoring`
  collections produced by `auction_draft_angles_v1.load_all_auction_picks`
  and `load_player_season_scoring`; never writes back. No new event
  types, no new schema, no new detector classes.
- Deterministic: identical inputs produce identical outputs.
  Tie-breaking rules in each function below are explicit.
- Substrate-derivable per A2 D3-Alpha: every output value traces to
  a canonical event or to documented aggregation logic. No
  commissioner-curated labels.
- No frozen ordinal claims per A2 spec section 6.8: rank ordering
  is computed at render time. This module emits sorted tuples with
  documented ordering; consumers display the ordering as the
  current substrate state. Caching of rank claims is forbidden.
- Honest framing per section 3.6: the 2021 substrate gap is not
  papered over. Aggregations naturally skip seasons absent from
  the substrate; the render layer carries the framing copy.

Governance:

- Defers to Canonical Operating Constitution.
- No inference, projection, or gap-filling - picks lacking position
  metadata are excluded from per-position records (per the
  silence-over-speculation principle); picks lacking scoring entries
  are silently omitted from bust/bargain aggregations.
- Missing data stays missing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    AuctionPick,
    PlayerSeasonScoring,
)

# -- Data classes ----------------------------------------------------


@dataclass(frozen=True)
class MostExpensivePick:
    """A single most-expensive auction pick record.

    Per A2 spec section 3.1 / section 3.8: surfaced both at the
    overall record position (the single all-time most-expensive pick
    across positions) and at per-position record positions (the
    all-time most-expensive pick per position present in the
    substrate). The same dataclass is used in both contexts; the
    `position` field disambiguates.
    """
    season: int
    franchise_id: str
    player_id: str
    bid_amount: float
    position: str  # may be empty for the overall record only if the
                   # underlying pick has no position metadata; per-
                   # position records always have a non-empty position.


@dataclass(frozen=True)
class MostExpensiveResult:
    """Overall plus per-position most-expensive records.

    Per A2 spec section 3.8 per-position-records-exposure: surfaces
    the overall record (the single all-time top bid) plus the
    per-position records (the top bid at each position present in
    the substrate). Top-1 per position at v1; the spec admits top-3
    per position as a revision-point expansion (section 7 governance).

    `overall` is None only when the input picks list is empty or
    contains no picks with `bid_amount > 0`.

    `per_position` is sorted by position ascending for determinism.
    Each entry's `position` field is non-empty. Picks lacking
    position metadata contribute to the overall record (if applicable)
    but are excluded from per-position records.
    """
    overall: MostExpensivePick | None
    per_position: tuple[MostExpensivePick, ...]


@dataclass(frozen=True)
class BustEntry:
    """A single cross-era auction bust hall entry.

    Per A2 spec section 3.1 Auction-Bust Hall: surfaces picks where
    a high bid produced dramatically below-starter-average
    production. The `severity_signal` is the ranking field:
    `(league_starter_avg - player_avg) * bid_amount`, higher meaning
    worse.

    Inclusion required `starter_weeks >= 4` and `player_avg <
    league_starter_avg * 0.5` per section 3.3 spec-stage gap
    landing. The `league_starter_avg` field is the season-specific
    league mean, computed cross-substrate per season.
    """
    season: int
    franchise_id: str
    player_id: str
    bid_amount: float
    player_avg: float
    league_starter_avg: float
    starter_weeks: int
    severity_signal: float


@dataclass(frozen=True)
class BargainEntry:
    """A single cross-era auction bargain hall entry.

    Per A2 spec section 3.1 Auction-Bargain Hall: surfaces picks
    where a low bid produced substantial production. The
    `dollar_per_point` is the ranking field, ascending (lower
    being a better bargain).

    Inclusion required `total_points >= min_points` (default 50,
    per section 3.3 spec-stage gap landing). Picks at or below
    the threshold are filtered before ranking; `$1 - $1` picks
    that scored 0 points are excluded by this filter.
    """
    season: int
    franchise_id: str
    player_id: str
    bid_amount: float
    total_points: float
    dollar_per_point: float


# -- Derivation: Auction-Most-Expensive History (spec section 3.1 / 3.8) --


def compute_auction_most_expensive_v1(
    picks: Sequence[AuctionPick],
) -> MostExpensiveResult:
    """Compute overall plus per-position most-expensive auction records.

    Per A2 spec sections 3.1 and 3.8. Lifts D28's internal `pos_max`
    accumulation pattern at `auction_draft_angles_v1.detect_auction_most_expensive_history`
    (line 818) and surfaces both the overall maximum AND the per-
    position maxima as a structured result.

    Tie-breaking is deterministic across all three rank surfaces:
    descending `bid_amount`, then ascending `(season, franchise_id,
    player_id)`. This anchors the same pick at the same rank across
    reruns for an identical substrate.

    Per A2 spec section 6.8 narrative-claim drift principle: this
    function emits the *current* rank. Consumers must call it at
    render time, not cache the result across archive updates.

    Args:
        picks: Auction picks sequence (typically from
            `load_all_auction_picks`). Order does not matter.

    Returns:
        MostExpensiveResult with overall record (may be None if no
        picks have `bid_amount > 0`) and per-position records
        (sorted by position ascending). Per-position entries always
        have non-empty `position`; the overall record may have an
        empty `position` if the top-bid pick has no position metadata
        in `player_directory`.
    """
    # Filter to picks with positive bids only - the loader already
    # filters these, but defensively re-filter for direct callers.
    valid_picks = [pk for pk in picks if pk.bid_amount > 0]
    if not valid_picks:
        return MostExpensiveResult(overall=None, per_position=())

    # Stable tie-break key: descending bid, then ascending substrate
    # identifiers. min() picks the smallest key; we negate bid_amount
    # so larger bids sort first.
    def _rank_key(pk: AuctionPick) -> tuple[float, int, str, str]:
        return (-pk.bid_amount, pk.season, pk.franchise_id, pk.player_id)

    overall_pick = min(valid_picks, key=_rank_key)
    overall = MostExpensivePick(
        season=overall_pick.season,
        franchise_id=overall_pick.franchise_id,
        player_id=overall_pick.player_id,
        bid_amount=overall_pick.bid_amount,
        position=overall_pick.position,
    )

    # Per-position: accumulate the lowest _rank_key per position
    # (which equals the highest bid; ties broken deterministically).
    # Picks with empty position are excluded from per-position records
    # per the dataclass contract.
    per_position_best: dict[str, AuctionPick] = {}
    for pk in valid_picks:
        if not pk.position:
            continue
        current = per_position_best.get(pk.position)
        if current is None or _rank_key(pk) < _rank_key(current):
            per_position_best[pk.position] = pk

    per_position = tuple(
        MostExpensivePick(
            season=pk.season,
            franchise_id=pk.franchise_id,
            player_id=pk.player_id,
            bid_amount=pk.bid_amount,
            position=pk.position,
        )
        for pos, pk in sorted(per_position_best.items())
    )

    return MostExpensiveResult(overall=overall, per_position=per_position)


# -- Derivation: Auction-Bust Hall (spec section 3.1) ----------------


def compute_auction_bust_hall_v1(
    picks: Sequence[AuctionPick],
    scoring: dict[tuple[int, str, str], PlayerSeasonScoring],
    *,
    min_starter_weeks: int = 4,
    avg_threshold_ratio: float = 0.5,
    top_n: int = 20,
) -> tuple[BustEntry, ...]:
    """Compute the cross-era Auction-Bust Hall.

    Per A2 spec section 3.1 Auction-Bust Hall and section 3.3
    spec-stage gap landings. Cross-season lift of D22's per-season
    logic at `auction_draft_angles_v1.detect_auction_bust`.

    For each pick:
    1. Look up `(season, franchise_id, player_id)` in `scoring`. Skip
       if no entry exists.
    2. Require `starter_weeks >= min_starter_weeks` (default 4 per
       spec section 3.3).
    3. Compute `player_avg = total_points / starter_weeks`.
    4. Compute the season's `league_starter_avg` as the simple mean
       across all (player, franchise) entries in `scoring` with
       `starter_weeks > 0` in that season.
    5. Skip if `player_avg >= league_starter_avg * avg_threshold_ratio`
       (default 0.5).
    6. Compute `severity_signal = (league_starter_avg - player_avg)
       * bid_amount`.

    Tie-breaking: descending `severity_signal`, then ascending
    `(season, franchise_id, player_id)` for substrate-stable order.

    Per A2 spec section 6.8 narrative-claim drift principle: rank
    ordering computes at call time. Consumers must call this at
    render time, not cache the result across archive updates.

    Args:
        picks: Auction picks sequence (typically from
            `load_all_auction_picks`). Order does not matter.
        scoring: Player-season scoring map (typically from
            `load_player_season_scoring` called with `current_season=0`
            for cross-season unfiltered loading). Keyed by
            (season, franchise_id, player_id).
        min_starter_weeks: Minimum starter weeks for inclusion.
            Defaults to 4 per spec section 3.3.
        avg_threshold_ratio: `player_avg < league_avg * ratio` is the
            inclusion threshold. Defaults to 0.5 per D22's default.
        top_n: Maximum number of entries to return. Defaults to 20
            per spec section 3.3 implementation-elected default.
            Must be non-negative.

    Returns:
        Immutable tuple of at most `top_n` BustEntry items, sorted
        by severity descending then by substrate identifiers
        ascending. Empty tuple if no picks meet the inclusion
        filters.

    Raises:
        ValueError: if `top_n` is negative.
    """
    if top_n < 0:
        raise ValueError(f"top_n must be non-negative; got {top_n}")
    if top_n == 0:
        return ()

    # Pre-compute per-season league_starter_avg from the scoring map.
    # Mean is taken across all (player, franchise) entries with
    # starter_weeks > 0. Matches D22's single-season computation
    # lifted per season for cross-era operation.
    starters_by_season: dict[int, list[float]] = {}
    for (season, _, _), entry in scoring.items():
        if entry.starter_weeks > 0:
            starters_by_season.setdefault(season, []).append(
                entry.total_points / entry.starter_weeks,
            )

    season_avg: dict[int, float] = {}
    for season, avgs in starters_by_season.items():
        if avgs:
            season_avg[season] = sum(avgs) / len(avgs)

    candidates: list[BustEntry] = []
    for pk in picks:
        if pk.bid_amount <= 0:
            continue
        sc: PlayerSeasonScoring | None = scoring.get(
            (pk.season, pk.franchise_id, pk.player_id),
        )
        if sc is None or sc.starter_weeks < min_starter_weeks:
            continue
        league_avg = season_avg.get(pk.season)
        if league_avg is None or league_avg < 1.0:
            continue
        player_avg = sc.total_points / sc.starter_weeks
        if player_avg >= league_avg * avg_threshold_ratio:
            continue
        severity = (league_avg - player_avg) * pk.bid_amount
        candidates.append(BustEntry(
            season=pk.season,
            franchise_id=pk.franchise_id,
            player_id=pk.player_id,
            bid_amount=pk.bid_amount,
            player_avg=round(player_avg, 4),
            league_starter_avg=round(league_avg, 4),
            starter_weeks=sc.starter_weeks,
            severity_signal=round(severity, 4),
        ))

    candidates.sort(key=lambda b: (
        -b.severity_signal, b.season, b.franchise_id, b.player_id,
    ))
    return tuple(candidates[:top_n])


# -- Derivation: Auction-Bargain Hall (spec section 3.1) -------------


def compute_auction_bargain_hall_v1(
    picks: Sequence[AuctionPick],
    scoring: dict[tuple[int, str, str], PlayerSeasonScoring],
    *,
    min_points: float = 50.0,
    top_n: int = 20,
) -> tuple[BargainEntry, ...]:
    """Compute the cross-era Auction-Bargain Hall.

    Per A2 spec section 3.1 Auction-Bargain Hall and section 3.3
    spec-stage gap landings. Cross-season lift in the D21 family.

    For each pick:
    1. Look up `(season, franchise_id, player_id)` in `scoring`. Skip
       if no entry exists.
    2. Require `total_points >= min_points` (default 50 per spec
       section 3.3). This excludes picks with no meaningful
       production - including the cluster of `$1` picks that scored
       0 or near-0 points whose `dollar_per_point` ratio would
       otherwise rank artificially favorably.
    3. Compute `dollar_per_point = bid_amount / total_points`. Lower
       is better.

    Tie-breaking: ascending `dollar_per_point`, then descending
    `total_points` (among equal ratios, more total points is the
    better bargain), then ascending `(season, franchise_id,
    player_id)` for substrate-stable order.

    Per A2 spec section 6.8 narrative-claim drift principle: rank
    ordering computes at call time. Consumers must call this at
    render time, not cache the result across archive updates.

    Args:
        picks: Auction picks sequence (typically from
            `load_all_auction_picks`). Order does not matter.
        scoring: Player-season scoring map (typically from
            `load_player_season_scoring` called with `current_season=0`
            for cross-season unfiltered loading). Keyed by
            (season, franchise_id, player_id).
        min_points: Minimum total_points for inclusion. Defaults to
            50 per spec section 3.3.
        top_n: Maximum number of entries to return. Defaults to 20
            per spec section 3.3 implementation-elected default.
            Must be non-negative.

    Returns:
        Immutable tuple of at most `top_n` BargainEntry items,
        sorted by dollar_per_point ascending then by total_points
        descending then by substrate identifiers ascending. Empty
        tuple if no picks meet the inclusion filter.

    Raises:
        ValueError: if `top_n` is negative.
    """
    if top_n < 0:
        raise ValueError(f"top_n must be non-negative; got {top_n}")
    if top_n == 0:
        return ()

    candidates: list[BargainEntry] = []
    for pk in picks:
        if pk.bid_amount <= 0:
            continue
        sc: PlayerSeasonScoring | None = scoring.get(
            (pk.season, pk.franchise_id, pk.player_id),
        )
        if sc is None or sc.total_points < min_points:
            continue
        # Defensive: total_points must be > 0 to avoid division
        # error. min_points >= 0 guards against ZeroDivisionError
        # only at min_points > 0; cover the boundary explicitly.
        if sc.total_points <= 0:
            continue
        dpp = pk.bid_amount / sc.total_points
        candidates.append(BargainEntry(
            season=pk.season,
            franchise_id=pk.franchise_id,
            player_id=pk.player_id,
            bid_amount=pk.bid_amount,
            total_points=round(sc.total_points, 2),
            dollar_per_point=round(dpp, 6),
        ))

    candidates.sort(key=lambda b: (
        b.dollar_per_point,
        -b.total_points,
        b.season,
        b.franchise_id,
        b.player_id,
    ))
    return tuple(candidates[:top_n])
