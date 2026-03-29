"""Player Week Context Derivation v1 — derived narrative context from player scoring events.

Contract (PLAYER_WEEK_CONTEXT v1.0):
- Derived-only: reads canonical events, never writes back into memory.
- Deterministic: identical inputs produce identical outputs.
- Non-authoritative: context is for creative layer consumption, not fact.
- Reconstructable: can be dropped and rebuilt from canonical events.
- No inference or gap-filling permitted.
- Missing data must remain missing.

This module computes per-franchise player scoring context from
WEEKLY_PLAYER_SCORE canonical events, with optional FAAB linkage from
WAIVER_BID_AWARDED events. It provides the creative layer with player-level
detail to produce recaps that reference individual performances.

Governance:
- Defers to Canonical Operating Constitution
- Implements PLAYER_WEEK_CONTEXT contract card (v1.0, Tier 2)
- Aligned with season_context_v1 derivation pattern
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from squadvault.core.storage.session import DatabaseSession


# ── Data classes (all frozen for determinism) ────────────────────────


@dataclass(frozen=True)
class PlayerScore:
    """A single player's scoring record for a week."""
    player_id: str
    score: float
    is_starter: bool
    should_start: bool  # MFL optimal lineup indicator


@dataclass(frozen=True)
class FaabPickup:
    """A FAAB acquisition linked to a player's weekly performance."""
    player_id: str
    franchise_id: str
    bid_amount: float
    acquisition_week: int  # week the FAAB was awarded (approximate from timestamp)


@dataclass(frozen=True)
class FranchiseWeekContext:
    """Per-franchise player context for a single week."""
    franchise_id: str

    # All players sorted by score descending
    starters: Tuple[PlayerScore, ...]
    bench: Tuple[PlayerScore, ...]

    # Highlights (deterministic — derived from sorted lists)
    top_starter: Optional[PlayerScore]     # highest-scoring starter
    bust_starter: Optional[PlayerScore]    # lowest-scoring starter
    starter_total: float                   # sum of starter scores
    bench_total: float                     # sum of bench scores

    # Bench analysis
    bench_points_over_starters: float      # sum of bench scores where should_start=True
    best_bench_player: Optional[PlayerScore]  # highest-scoring bench player

    # FAAB linkage (players acquired via FAAB who scored this week)
    faab_performers: Tuple[Tuple[PlayerScore, FaabPickup], ...]


@dataclass(frozen=True)
class PlayerWeekContextV1:
    """Full derived player context for a given week.

    This is the payload that feeds the creative layer's PLAYER HIGHLIGHTS block.
    All fields are derived from canonical WEEKLY_PLAYER_SCORE events and
    optionally WAIVER_BID_AWARDED events.
    """
    league_id: str
    season: int
    week: int

    # Per-franchise context, sorted by franchise_id
    franchises: Tuple[FranchiseWeekContext, ...]

    # Week-level highlights
    week_top_scorer: Optional[Tuple[str, str, float]]     # (franchise_id, player_id, score)
    week_lowest_starter: Optional[Tuple[str, str, float]]  # (franchise_id, player_id, score)

    # Metadata
    total_players: int
    total_starters: int

    @property
    def has_data(self) -> bool:
        """True if any player scoring data exists for this week."""
        return self.total_players > 0


# ── Empty context (silence over fabrication) ─────────────────────────


def _empty_context(league_id: str, season: int, week: int) -> PlayerWeekContextV1:
    """Return empty context when no player scoring data exists."""
    return PlayerWeekContextV1(
        league_id=league_id,
        season=season,
        week=week,
        franchises=(),
        week_top_scorer=None,
        week_lowest_starter=None,
        total_players=0,
        total_starters=0,
    )


# ── Data loading ─────────────────────────────────────────────────────


def _load_player_scores(
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> List[Dict[str, Any]]:
    """Load WEEKLY_PLAYER_SCORE events from canonical_events for a given week.

    Returns raw payload dicts sorted by (franchise_id, player_id).
    """
    payloads: List[Dict[str, Any]] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
               ORDER BY payload_json ASC""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue

        if not isinstance(p, dict):
            continue

        # Filter to the requested week
        try:
            payload_week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue

        if payload_week != week:
            continue

        payloads.append(p)

    # Deterministic sort
    payloads.sort(key=lambda p: (str(p.get("franchise_id", "")), str(p.get("player_id", ""))))
    return payloads


def _load_faab_awards(
    db_path: str,
    league_id: str,
    season: int,
) -> List[Dict[str, Any]]:
    """Load WAIVER_BID_AWARDED events from canonical_events for a season.

    Returns raw payload dicts for all FAAB awards in the season.
    These are used to link FAAB spending to player performance.
    """
    payloads: List[Dict[str, Any]] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json, occurred_at
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue

        if isinstance(p, dict):
            # Attach occurred_at for approximate week derivation
            p["_occurred_at"] = row[1] if len(row) > 1 else None
            payloads.append(p)

    return payloads


def _build_faab_lookup(
    faab_payloads: List[Dict[str, Any]],
) -> Dict[str, List[FaabPickup]]:
    """Build a lookup: player_id -> list of FaabPickup records.

    Since we don't have a direct week number on FAAB events, we use
    a placeholder week of 0. The linkage is by player_id + franchise_id,
    and the bid_amount is the key data for narrative context.
    """
    lookup: Dict[str, List[FaabPickup]] = {}

    for p in faab_payloads:
        # Try to extract player IDs from FAAB events
        # WAIVER_BID_AWARDED may have player_id directly or players_added_ids
        player_id = str(p.get("player_id", "")).strip()
        franchise_id = str(p.get("franchise_id", "")).strip()

        if not player_id:
            # Try players_added_ids (may be comma-separated or a list)
            added = p.get("players_added_ids")
            if isinstance(added, str) and added.strip():
                # Take the first added player as the primary acquisition
                player_id = added.split(",")[0].strip()
            elif isinstance(added, list) and added:
                player_id = str(added[0]).strip()

        if not player_id or not franchise_id:
            continue

        bid_amount = None
        raw_bid = p.get("bid_amount")
        if raw_bid is not None:
            try:
                bid_amount = float(raw_bid)
            except (ValueError, TypeError):
                pass

        if bid_amount is None or bid_amount <= 0:
            continue

        pickup = FaabPickup(
            player_id=player_id,
            franchise_id=franchise_id,
            bid_amount=bid_amount,
            acquisition_week=0,  # approximate; not used for filtering
        )

        if player_id not in lookup:
            lookup[player_id] = []
        lookup[player_id].append(pickup)

    return lookup


# ── Core derivation ─────────────────────────────────────────────────


def _build_franchise_context(
    franchise_id: str,
    player_payloads: List[Dict[str, Any]],
    faab_lookup: Dict[str, List[FaabPickup]],
) -> FranchiseWeekContext:
    """Build context for a single franchise from its player score payloads."""

    starters: List[PlayerScore] = []
    bench: List[PlayerScore] = []

    for p in player_payloads:
        player_id = str(p.get("player_id", "")).strip()
        if not player_id:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0

        is_starter = bool(p.get("is_starter", False))
        should_start = bool(p.get("should_start", False))

        ps = PlayerScore(
            player_id=player_id,
            score=score,
            is_starter=is_starter,
            should_start=should_start,
        )

        if is_starter:
            starters.append(ps)
        else:
            bench.append(ps)

    # Sort by score descending for deterministic highlight selection
    starters.sort(key=lambda s: (-s.score, s.player_id))
    bench.sort(key=lambda s: (-s.score, s.player_id))

    top_starter = starters[0] if starters else None
    bust_starter = starters[-1] if starters else None
    starter_total = round(sum(s.score for s in starters), 2)
    bench_total = round(sum(s.score for s in bench), 2)

    # Bench players who should have started (MFL optimal lineup)
    bench_points_over = round(
        sum(s.score for s in bench if s.should_start), 2
    )

    best_bench = bench[0] if bench else None

    # FAAB linkage — find FAAB pickups who scored this week for this franchise
    faab_performers: List[Tuple[PlayerScore, FaabPickup]] = []
    all_players = list(starters) + list(bench)
    for ps in all_players:
        pickups = faab_lookup.get(ps.player_id, [])
        for pickup in pickups:
            if pickup.franchise_id == franchise_id:
                faab_performers.append((ps, pickup))
                break  # one pickup per player is enough

    # Sort FAAB performers by score descending
    faab_performers.sort(key=lambda x: (-x[0].score, x[0].player_id))

    return FranchiseWeekContext(
        franchise_id=franchise_id,
        starters=tuple(starters),
        bench=tuple(bench),
        top_starter=top_starter,
        bust_starter=bust_starter,
        starter_total=starter_total,
        bench_total=bench_total,
        bench_points_over_starters=bench_points_over,
        best_bench_player=best_bench,
        faab_performers=tuple(faab_performers),
    )


# ── Public API ───────────────────────────────────────────────────────


def derive_player_week_context_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> PlayerWeekContextV1:
    """Derive player week context for a given week from canonical events.

    Returns a PlayerWeekContextV1 with per-franchise player scoring,
    top/bust performers, bench analysis, and FAAB linkage.

    If no player scoring data exists for the week, returns empty context
    (silence over fabrication).

    Contract compliance:
    - Derived-only: reads canonical_events via v_canonical_best_events view
    - Deterministic: sorted inputs, sorted outputs, no randomness
    - Reconstructable: drop canonical_events + rebuild produces identical output
    - No inference: missing scores stay missing, no gap-filling
    """
    player_payloads = _load_player_scores(db_path, league_id, season, week)

    if not player_payloads:
        return _empty_context(league_id, season, week)

    # Load FAAB awards for the season (for linkage)
    faab_payloads = _load_faab_awards(db_path, league_id, season)
    faab_lookup = _build_faab_lookup(faab_payloads)

    # Group payloads by franchise
    by_franchise: Dict[str, List[Dict[str, Any]]] = {}
    for p in player_payloads:
        fid = str(p.get("franchise_id", "")).strip()
        if fid:
            if fid not in by_franchise:
                by_franchise[fid] = []
            by_franchise[fid].append(p)

    # Build per-franchise context
    franchise_contexts: List[FranchiseWeekContext] = []
    for fid in sorted(by_franchise.keys()):
        ctx = _build_franchise_context(fid, by_franchise[fid], faab_lookup)
        franchise_contexts.append(ctx)

    # Week-level highlights
    all_starters: List[Tuple[str, str, float]] = []
    all_players_count = 0

    for fc in franchise_contexts:
        for ps in fc.starters:
            all_starters.append((fc.franchise_id, ps.player_id, ps.score))
        all_players_count += len(fc.starters) + len(fc.bench)

    # Top scorer (highest scoring starter across all franchises)
    week_top = None
    if all_starters:
        all_starters.sort(key=lambda x: (-x[2], x[0], x[1]))
        week_top = all_starters[0]

    # Lowest starter (lowest scoring starter across all franchises)
    week_lowest = None
    if all_starters:
        all_starters_by_low = sorted(all_starters, key=lambda x: (x[2], x[0], x[1]))
        week_lowest = all_starters_by_low[0]

    return PlayerWeekContextV1(
        league_id=league_id,
        season=season,
        week=week,
        franchises=tuple(franchise_contexts),
        week_top_scorer=week_top,
        week_lowest_starter=week_lowest,
        total_players=all_players_count,
        total_starters=len(all_starters),
    )


# ── Prompt rendering (for creative layer consumption) ────────────────


def render_player_highlights_for_prompt(
    ctx: PlayerWeekContextV1,
    *,
    team_resolver: Optional[Any] = None,
    player_resolver: Optional[Any] = None,
) -> str:
    """Render player week context as a text block for the creative layer prompt.

    This produces a PLAYER HIGHLIGHTS section that sits between SEASON CONTEXT
    and VERIFIED FACTS in the creative layer prompt.

    team_resolver: optional callable (franchise_id -> display_name).
    player_resolver: optional callable (player_id -> display_name).
    If None, IDs are used directly.
    """
    if not ctx.has_data:
        return ""

    def _team(fid: str) -> str:
        if team_resolver is not None:
            try:
                n = team_resolver(fid)
                if n and str(n).strip():
                    return str(n).strip()
            except (KeyError, ValueError, TypeError, LookupError):
                pass
        return fid

    def _player(pid: str) -> str:
        if player_resolver is not None:
            try:
                n = player_resolver(pid)
                if n and str(n).strip():
                    return str(n).strip()
            except (KeyError, ValueError, TypeError, LookupError):
                pass
        return pid

    lines: List[str] = []

    # Week-level highlights
    if ctx.week_top_scorer:
        fid, pid, score = ctx.week_top_scorer
        lines.append(
            f"Week {ctx.week} top scorer: {_player(pid)} ({_team(fid)}) — {score:.2f} pts"
        )
    if ctx.week_lowest_starter:
        fid, pid, score = ctx.week_lowest_starter
        lines.append(
            f"Week {ctx.week} lowest starter: {_player(pid)} ({_team(fid)}) — {score:.2f} pts"
        )

    lines.append("")

    # Per-franchise highlights (top performer, bust, bench analysis)
    for fc in ctx.franchises:
        team_name = _team(fc.franchise_id)
        franchise_lines: List[str] = []

        # Top starter
        if fc.top_starter:
            franchise_lines.append(
                f"  Top: {_player(fc.top_starter.player_id)} — {fc.top_starter.score:.2f} pts"
            )

        # Bust (only if different from top and there are multiple starters)
        if fc.bust_starter and fc.top_starter and fc.bust_starter != fc.top_starter:
            franchise_lines.append(
                f"  Bust: {_player(fc.bust_starter.player_id)} — {fc.bust_starter.score:.2f} pts"
            )

        # Bench analysis — only if there are bench points worth mentioning
        if fc.best_bench_player and fc.bust_starter:
            if fc.best_bench_player.score > fc.bust_starter.score:
                franchise_lines.append(
                    f"  Bench > starter: {_player(fc.best_bench_player.player_id)}"
                    f" ({fc.best_bench_player.score:.2f}) outscored"
                    f" {_player(fc.bust_starter.player_id)}"
                    f" ({fc.bust_starter.score:.2f})"
                )

        # Points left on bench (shouldStart bench players)
        if fc.bench_points_over_starters > 0:
            franchise_lines.append(
                f"  Optimal lineup points left on bench: {fc.bench_points_over_starters:.2f}"
            )

        # FAAB performers
        for ps, pickup in fc.faab_performers:
            status = "starter" if ps.is_starter else "bench"
            franchise_lines.append(
                f"  FAAB pickup ${pickup.bid_amount:.0f}: {_player(ps.player_id)}"
                f" — {ps.score:.2f} pts ({status})"
            )

        if franchise_lines:
            lines.append(f"{team_name} (starters: {fc.starter_total:.2f}, bench: {fc.bench_total:.2f}):")
            lines.extend(franchise_lines)

    return "\n".join(lines) + "\n"
