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

FAAB performer timelines (Finding 5 fix): for each player acquired via
FAAB who scored this week, the module pre-derives their post-acquisition
scoring history on the franchise. This removes the opportunity for
model-side temporal fabrication ("first week since", "Nth straight")
by providing pre-computed facts the model can cite directly.

Governance:
- Defers to Canonical Operating Constitution
- Implements PLAYER_WEEK_CONTEXT contract card (v1.0, Tier 2)
- Aligned with season_context_v1 derivation pattern
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

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
class FaabWeekAppearance:
    """A single week's scoring record for a FAAB-acquired player on a franchise."""
    week: int
    score: float
    is_starter: bool


@dataclass(frozen=True)
class FaabPerformerTimeline:
    """Pre-derived post-acquisition timeline for a FAAB pickup.

    Provides the creative layer with explicit temporal facts so it
    does not need to infer "first week since", "Nth start", etc.
    All fields are derived from canonical WEEKLY_PLAYER_SCORE events.
    """
    player_id: str
    franchise_id: str

    # All weeks this player appeared on this franchise (prior to current week),
    # sorted by week ascending.  Each entry is a FaabWeekAppearance.
    prior_weeks: tuple[FaabWeekAppearance, ...]

    # Derived counts (including current week)
    weeks_on_roster: int       # total weeks with a scoring record on this franchise
    starts_on_roster: int      # total weeks started (including current if starter)
    is_first_start: bool       # True if no prior week had is_starter=True and current is starter
    is_first_week_on_roster: bool  # True if this is the very first scoring week


@dataclass(frozen=True)
class FranchiseWeekContext:
    """Per-franchise player context for a single week."""
    franchise_id: str

    # All players sorted by score descending
    starters: tuple[PlayerScore, ...]
    bench: tuple[PlayerScore, ...]

    # Highlights (deterministic — derived from sorted lists)
    top_starter: PlayerScore | None     # highest-scoring starter
    bust_starter: PlayerScore | None    # lowest-scoring starter
    starter_total: float                   # sum of starter scores
    bench_total: float                     # sum of bench scores

    # Bench analysis
    bench_points_over_starters: float      # sum of bench scores where should_start=True
    best_bench_player: PlayerScore | None  # highest-scoring bench player

    # FAAB linkage (players acquired via FAAB who scored this week)
    faab_performers: tuple[tuple[PlayerScore, FaabPickup], ...]

    # FAAB performer timelines — pre-derived temporal context for each
    # FAAB performer, keyed by player_id for deterministic access.
    # Empty tuple when season history is unavailable (backward compat).
    faab_performer_timelines: tuple[FaabPerformerTimeline, ...] = field(default=())


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
    franchises: tuple[FranchiseWeekContext, ...]

    # Week-level highlights
    week_top_scorer: tuple[str, str, float] | None     # (franchise_id, player_id, score)
    week_lowest_starter: tuple[str, str, float] | None  # (franchise_id, player_id, score)

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
) -> list[dict[str, Any]]:
    """Load WEEKLY_PLAYER_SCORE events from canonical_events for a given week.

    Returns raw payload dicts sorted by (franchise_id, player_id).
    """
    payloads: list[dict[str, Any]] = []

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
) -> list[dict[str, Any]]:
    """Load WAIVER_BID_AWARDED events from canonical_events for a season.

    Returns raw payload dicts for all FAAB awards in the season.
    These are used to link FAAB spending to player performance.
    """
    payloads: list[dict[str, Any]] = []

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


def _load_season_player_history(
    db_path: str,
    league_id: str,
    season: int,
) -> dict[tuple[str, str], list[tuple[int, float, bool]]]:
    """Load all WEEKLY_PLAYER_SCORE events for a season, organized by (franchise_id, player_id).

    Returns a dict mapping (franchise_id, player_id) to a list of
    (week, score, is_starter) tuples, sorted by week ascending.

    Used for FAAB performer timeline derivation — provides the full
    season view needed to pre-compute temporal facts like "weeks on
    roster" and "first start" without inference.
    """
    raw: dict[tuple[str, str], list[tuple[int, float, bool]]] = {}

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

        franchise_id = str(p.get("franchise_id", "")).strip()
        player_id = str(p.get("player_id", "")).strip()
        if not franchise_id or not player_id:
            continue

        try:
            week = int(p.get("week", -1))
        except (ValueError, TypeError):
            continue
        if week < 0:
            continue

        try:
            score = float(p.get("score", 0))
        except (ValueError, TypeError):
            score = 0.0

        is_starter = bool(p.get("is_starter", False))

        key = (franchise_id, player_id)
        if key not in raw:
            raw[key] = []
        raw[key].append((week, score, is_starter))

    # Sort each player's history by week ascending for determinism
    for key in raw:
        raw[key].sort(key=lambda t: t[0])

    return raw


def _build_faab_lookup(
    faab_payloads: list[dict[str, Any]],
) -> dict[str, list[FaabPickup]]:
    """Build a lookup: player_id -> list of FaabPickup records.

    Since we don't have a direct week number on FAAB events, we use
    a placeholder week of 0. The linkage is by player_id + franchise_id,
    and the bid_amount is the key data for narrative context.
    """
    lookup: dict[str, list[FaabPickup]] = {}

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


# ── FAAB performer timeline derivation ───────────────────────────────


def _build_faab_performer_timelines(
    faab_performers: list[tuple[PlayerScore, FaabPickup]],
    franchise_id: str,
    current_week: int,
    season_history: dict[tuple[str, str], list[tuple[int, float, bool]]],
) -> tuple[FaabPerformerTimeline, ...]:
    """Build pre-derived timelines for FAAB performers on a franchise.

    For each FAAB-acquired player who scored this week, looks up their
    full scoring history on this franchise across the season and computes:
    - Prior weeks on the roster (before current week)
    - Total weeks/starts on roster (including current)
    - Whether current week is their first start

    Returns timelines sorted by player_id for determinism.

    Contract compliance:
    - Derived-only: reads from season_history (already loaded from canonical)
    - Deterministic: sorted outputs, no randomness
    - No inference: if season history is unavailable, returns empty
    """
    if not faab_performers or not season_history:
        return ()

    timelines: list[FaabPerformerTimeline] = []

    for ps, pickup in faab_performers:
        key = (franchise_id, ps.player_id)
        history = season_history.get(key, [])

        if not history:
            # No season history available — silence over fabrication
            continue

        # Separate prior weeks (before current) from current week
        prior: list[FaabWeekAppearance] = []
        total_weeks = 0
        total_starts = 0

        for week_num, score, is_starter in history:
            if week_num < current_week:
                prior.append(FaabWeekAppearance(
                    week=week_num,
                    score=score,
                    is_starter=is_starter,
                ))
                total_weeks += 1
                if is_starter:
                    total_starts += 1
            elif week_num == current_week:
                total_weeks += 1
                if is_starter:
                    total_starts += 1

        # Derive temporal facts
        prior_had_starts = any(pw.is_starter for pw in prior)

        timelines.append(FaabPerformerTimeline(
            player_id=ps.player_id,
            franchise_id=franchise_id,
            prior_weeks=tuple(prior),
            weeks_on_roster=total_weeks,
            starts_on_roster=total_starts,
            is_first_start=ps.is_starter and not prior_had_starts,
            is_first_week_on_roster=total_weeks == 1,
        ))

    # Sort by player_id for determinism
    timelines.sort(key=lambda t: t.player_id)
    return tuple(timelines)


# ── Core derivation ─────────────────────────────────────────────────


def _build_franchise_context(
    franchise_id: str,
    player_payloads: list[dict[str, Any]],
    faab_lookup: dict[str, list[FaabPickup]],
    season_history: dict[tuple[str, str], list[tuple[int, float, bool]]] | None = None,
    current_week: int | None = None,
) -> FranchiseWeekContext:
    """Build context for a single franchise from its player score payloads.

    Optional season_history + current_week enable FAAB performer timeline
    derivation. When not provided, timelines are empty (backward compat).
    """

    starters: list[PlayerScore] = []
    bench: list[PlayerScore] = []

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
    faab_performers: list[tuple[PlayerScore, FaabPickup]] = []
    all_players = list(starters) + list(bench)
    for ps in all_players:
        pickups = faab_lookup.get(ps.player_id, [])
        for pickup in pickups:
            if pickup.franchise_id == franchise_id:
                faab_performers.append((ps, pickup))
                break  # one pickup per player is enough

    # Sort FAAB performers by score descending
    faab_performers.sort(key=lambda x: (-x[0].score, x[0].player_id))

    # FAAB performer timelines — pre-derive temporal context
    timelines: tuple[FaabPerformerTimeline, ...] = ()
    if faab_performers and season_history is not None and current_week is not None:
        timelines = _build_faab_performer_timelines(
            faab_performers, franchise_id, current_week, season_history,
        )

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
        faab_performer_timelines=timelines,
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
    top/bust performers, bench analysis, FAAB linkage, and FAAB performer
    timelines (pre-derived temporal context).

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

    # Load season-wide player history for FAAB timeline derivation.
    # Only loaded when FAAB data exists to avoid unnecessary DB work.
    season_history: dict[tuple[str, str], list[tuple[int, float, bool]]] | None = None
    if faab_lookup:
        season_history = _load_season_player_history(db_path, league_id, season)

    # Group payloads by franchise
    by_franchise: dict[str, list[dict[str, Any]]] = {}
    for p in player_payloads:
        fid = str(p.get("franchise_id", "")).strip()
        if fid:
            if fid not in by_franchise:
                by_franchise[fid] = []
            by_franchise[fid].append(p)

    # Build per-franchise context
    franchise_contexts: list[FranchiseWeekContext] = []
    for fid in sorted(by_franchise.keys()):
        ctx = _build_franchise_context(
            fid, by_franchise[fid], faab_lookup,
            season_history=season_history,
            current_week=week,
        )
        franchise_contexts.append(ctx)

    # Week-level highlights
    all_starters: list[tuple[str, str, float]] = []
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
    team_resolver: Any | None = None,
    player_resolver: Any | None = None,
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

    lines: list[str] = []

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
        franchise_lines: list[str] = []

        # Top starter
        if fc.top_starter:
            franchise_lines.append(
                f"  Top: {_player(fc.top_starter.player_id)} [{team_name}] — {fc.top_starter.score:.2f} pts"
            )

        # Bust (only if different from top and there are multiple starters)
        if fc.bust_starter and fc.top_starter and fc.bust_starter != fc.top_starter:
            franchise_lines.append(
                f"  Bust: {_player(fc.bust_starter.player_id)} [{team_name}] — {fc.bust_starter.score:.2f} pts"
            )

        # Bench analysis — only if there are bench points worth mentioning
        if fc.best_bench_player and fc.bust_starter:
            if fc.best_bench_player.score > fc.bust_starter.score:
                franchise_lines.append(
                    f"  Bench > starter: {_player(fc.best_bench_player.player_id)}"
                    f" [{team_name}] ({fc.best_bench_player.score:.2f}) outscored"
                    f" {_player(fc.bust_starter.player_id)}"
                    f" [{team_name}] ({fc.bust_starter.score:.2f})"
                )

        # Points left on bench (shouldStart bench players)
        if fc.bench_points_over_starters > 0:
            franchise_lines.append(
                f"  Optimal lineup points left on bench: {fc.bench_points_over_starters:.2f}"
            )

        # FAAB performers — with pre-derived temporal context
        # Build a lookup for timelines by player_id
        timeline_by_pid: dict[str, FaabPerformerTimeline] = {
            t.player_id: t for t in fc.faab_performer_timelines
        }

        for ps, pickup in fc.faab_performers:
            status = "starter" if ps.is_starter else "bench"
            base = (
                f"  FAAB pickup ${pickup.bid_amount:.0f}: {_player(ps.player_id)}"
                f" [{team_name}] — {ps.score:.2f} pts ({status})"
            )

            timeline = timeline_by_pid.get(ps.player_id)
            if timeline is not None:
                temporal = _render_faab_timeline(timeline, player_resolver=_player)
                if temporal:
                    base += f". {temporal}"

            franchise_lines.append(base)

        if franchise_lines:
            lines.append(f"{team_name} (starters: {fc.starter_total:.2f}, bench: {fc.bench_total:.2f}):")
            lines.extend(franchise_lines)

    return "\n".join(lines) + "\n"


def _render_faab_timeline(
    timeline: FaabPerformerTimeline,
    *,
    player_resolver: Any | None = None,
) -> str:
    """Render a FAAB performer timeline as a compact string for the prompt.

    Produces factual, pre-derived temporal claims like:
        "Week 3 on roster. First start. Prior: W12 7.40 (bench), W13 16.30 (bench)"

    Returns empty string if there is nothing meaningful to add (e.g. first
    week on roster with no prior history — the base FAAB line is sufficient).
    """
    parts: list[str] = []

    if timeline.is_first_week_on_roster:
        parts.append("First week on roster")
    else:
        parts.append(f"Week {timeline.weeks_on_roster} on roster")

    if timeline.is_first_start:
        parts.append("first start")

    # Prior weeks — compact rendering
    if timeline.prior_weeks:
        prior_strs: list[str] = []
        for pw in timeline.prior_weeks:
            status = "starter" if pw.is_starter else "bench"
            prior_strs.append(f"W{pw.week} {pw.score:.2f} ({status})")
        parts.append("prior: " + ", ".join(prior_strs))

    return ". ".join(parts) if parts else ""
