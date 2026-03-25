"""Writer Room Context v1 — scoring deltas and FAAB spending derivation.

Contract:
- Derived-only: reads canonical events, never writes back.
- Deterministic: identical inputs produce identical outputs.
- Non-authoritative: context is for creative layer consumption, not fact.

This module computes:
- Week-over-week scoring deltas per team (momentum/collapse detection)
- Cumulative FAAB spending per franchise from WAIVER_BID_AWARDED events

These are the "details that make the writer sound like an insider" —
the difference between "Team X scored 145" and "Team X bounced back
from a 82-point dud to drop 145 — a 63-point swing."
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from squadvault.core.storage.session import DatabaseSession


# ── Scoring Deltas ───────────────────────────────────────────────────


@dataclass(frozen=True)
class ScoringDelta:
    """Week-over-week scoring change for a single franchise."""
    franchise_id: str
    this_week_score: float
    last_week_score: Optional[float]  # None if no prior week data
    delta: Optional[float]            # this_week - last_week, or None

    @property
    def has_delta(self) -> bool:
        """True if a week-over-week comparison is available."""
        return self.delta is not None


def derive_scoring_deltas(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Tuple[ScoringDelta, ...]:
    """Compute scoring deltas (this week vs last week) for all teams.

    Returns a tuple of ScoringDelta, one per franchise that played this week.
    If the franchise didn't play last week, delta is None.
    """
    this_week_scores: Dict[str, float] = {}
    last_week_scores: Dict[str, float] = {}

    with DatabaseSession(db_path) as con:
        # This week's scores
        rows = con.execute(
            """SELECT payload_json FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        week = None
        try:
            week = int(p.get("week", 0))
        except (ValueError, TypeError):
            continue

        winner_id = p.get("winner_franchise_id") or p.get("winner_team_id")
        loser_id = p.get("loser_franchise_id") or p.get("loser_team_id")

        try:
            winner_score = float(p.get("winner_score", 0))
            loser_score = float(p.get("loser_score", 0))
        except (ValueError, TypeError):
            continue

        if week == week_index:
            if winner_id:
                this_week_scores[str(winner_id).strip()] = winner_score
            if loser_id:
                this_week_scores[str(loser_id).strip()] = loser_score
        elif week == week_index - 1:
            if winner_id:
                last_week_scores[str(winner_id).strip()] = winner_score
            if loser_id:
                last_week_scores[str(loser_id).strip()] = loser_score

    deltas: List[ScoringDelta] = []
    for fid, score in sorted(this_week_scores.items()):
        last = last_week_scores.get(fid)
        delta = round(score - last, 2) if last is not None else None
        deltas.append(ScoringDelta(
            franchise_id=fid,
            this_week_score=score,
            last_week_score=last,
            delta=delta,
        ))

    return tuple(deltas)


# ── FAAB Spending ────────────────────────────────────────────────────


@dataclass(frozen=True)
class FaabSpending:
    """Cumulative FAAB spending for a single franchise through a given week."""
    franchise_id: str
    total_spent: float
    num_acquisitions: int
    budget: Optional[float]           # league budget if provided
    remaining: Optional[float]        # budget - total_spent, or None
    pct_spent: Optional[float]        # total_spent / budget, or None


def derive_faab_spending(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    faab_budget: Optional[float] = None,
) -> Tuple[FaabSpending, ...]:
    """Compute cumulative FAAB spending per franchise through a given week.

    Reads all WAIVER_BID_AWARDED canonical events for the season and sums
    bid amounts per franchise. Only includes events with occurred_at <= week boundary.

    faab_budget: if provided, computes remaining budget and % spent.
    """
    spending: Dict[str, float] = {}
    counts: Dict[str, int] = {}

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        fid = p.get("franchise_id") or p.get("team_id")
        if not fid:
            continue
        fid = str(fid).strip()

        # Extract bid amount from all known field names
        bid = p.get("bid") or p.get("bid_amount") or p.get("amount")
        if bid is None:
            continue
        try:
            bid_val = float(bid)
        except (ValueError, TypeError):
            continue
        if bid_val <= 0:
            continue

        spending[fid] = spending.get(fid, 0.0) + bid_val
        counts[fid] = counts.get(fid, 0) + 1

    results: List[FaabSpending] = []
    for fid in sorted(spending.keys()):
        total = round(spending[fid], 2)
        n = counts[fid]
        remaining = round(faab_budget - total, 2) if faab_budget is not None else None
        pct = round(total / faab_budget, 4) if faab_budget is not None and faab_budget > 0 else None
        results.append(FaabSpending(
            franchise_id=fid,
            total_spent=total,
            num_acquisitions=n,
            budget=faab_budget,
            remaining=remaining,
            pct_spent=pct,
        ))

    return tuple(results)


# ── Roster Activity (season cumulative) ──────────────────────────────


@dataclass(frozen=True)
class RosterActivity:
    """Cumulative roster activity for a franchise through a given season."""
    franchise_id: str
    waiver_wins: int      # WAIVER_BID_AWARDED count
    free_agent_adds: int  # TRANSACTION_FREE_AGENT count
    trades: int           # TRANSACTION_TRADE count
    total_moves: int      # sum of all above

    @property
    def is_active(self) -> bool:
        """True if the franchise has made any roster moves."""
        return self.total_moves > 0


def derive_roster_activity(
    *,
    db_path: str,
    league_id: str,
    season: int,
) -> Tuple[RosterActivity, ...]:
    """Compute cumulative roster activity per franchise for the entire season.

    Counts:
    - WAIVER_BID_AWARDED: paid waiver claims
    - TRANSACTION_FREE_AGENT: free agent pickups
    - TRANSACTION_TRADE: trades executed

    Returns a tuple of RosterActivity, one per franchise with any activity,
    sorted by total_moves descending.
    """
    waiver_counts: Dict[str, int] = {}
    fa_counts: Dict[str, int] = {}
    trade_counts: Dict[str, int] = {}

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT ce.event_type, me.payload_json
               FROM canonical_events ce
               JOIN memory_events me ON me.id = ce.best_memory_event_id
               WHERE ce.league_id = ? AND ce.season = ?
                 AND ce.event_type IN (
                     'WAIVER_BID_AWARDED',
                     'TRANSACTION_FREE_AGENT',
                     'TRANSACTION_TRADE'
                 )""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        event_type = str(row[0])
        try:
            p = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue

        fid = p.get("franchise_id") or p.get("team_id") or p.get("franchise")
        if not fid:
            # For trades, both sides have franchise references
            # Count the initiator if available, or skip
            fids = []
            for key in ("franchise1_id", "franchise2_id", "team1_id", "team2_id"):
                if p.get(key):
                    fids.append(str(p[key]).strip())
            if not fids:
                continue
            for f in fids:
                trade_counts[f] = trade_counts.get(f, 0) + 1
            continue

        fid = str(fid).strip()

        if event_type == "WAIVER_BID_AWARDED":
            waiver_counts[fid] = waiver_counts.get(fid, 0) + 1
        elif event_type == "TRANSACTION_FREE_AGENT":
            fa_counts[fid] = fa_counts.get(fid, 0) + 1
        elif event_type == "TRANSACTION_TRADE":
            trade_counts[fid] = trade_counts.get(fid, 0) + 1

    all_fids = set(waiver_counts) | set(fa_counts) | set(trade_counts)
    results: List[RosterActivity] = []
    for fid in sorted(all_fids):
        ww = waiver_counts.get(fid, 0)
        fa = fa_counts.get(fid, 0)
        tr = trade_counts.get(fid, 0)
        results.append(RosterActivity(
            franchise_id=fid,
            waiver_wins=ww,
            free_agent_adds=fa,
            trades=tr,
            total_moves=ww + fa + tr,
        ))

    results.sort(key=lambda r: -r.total_moves)
    return tuple(results)


# ── Prompt rendering ─────────────────────────────────────────────────


def render_writer_room_context_for_prompt(
    *,
    deltas: Sequence[ScoringDelta],
    faab: Sequence[FaabSpending],
    roster_activity: Sequence[RosterActivity] = (),
    name_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render scoring deltas, FAAB spending, and roster activity for the creative layer."""

    def _name(fid: str) -> str:
        """Resolve franchise ID to display name."""
        if name_map and fid in name_map:
            return name_map[fid]
        return fid

    lines: List[str] = []

    # Scoring deltas
    deltas_with_data = [d for d in deltas if d.has_delta]
    if deltas_with_data:
        lines.append("Week-over-week scoring changes:")
        # Sort by absolute delta descending (biggest swings first)
        sorted_deltas = sorted(deltas_with_data, key=lambda d: -abs(d.delta))
        for d in sorted_deltas:
            name = _name(d.franchise_id)
            direction = "+" if d.delta >= 0 else ""
            lines.append(
                f"  {name}: {d.this_week_score:.2f} (was {d.last_week_score:.2f}, {direction}{d.delta:.2f})"
            )

    # FAAB spending
    if faab:
        if lines:
            lines.append("")
        lines.append("FAAB spending this season:")
        sorted_faab = sorted(faab, key=lambda f: -f.total_spent)
        for f in sorted_faab:
            name = _name(f.franchise_id)
            budget_str = ""
            if f.remaining is not None and f.budget is not None:
                pct = f.pct_spent * 100 if f.pct_spent is not None else 0
                budget_str = f" (${f.remaining:.0f} remaining of ${f.budget:.0f}, {pct:.0f}% spent)"
            lines.append(
                f"  {name}: ${f.total_spent:.0f} on {f.num_acquisitions} acquisition(s){budget_str}"
            )

    # Roster activity (season cumulative)
    if roster_activity:
        if lines:
            lines.append("")
        lines.append("Season roster activity (verified counts — cite these, do not invent your own):")
        for r in roster_activity:
            name = _name(r.franchise_id)
            parts = []
            if r.waiver_wins:
                parts.append(f"{r.waiver_wins} waiver wins")
            if r.free_agent_adds:
                parts.append(f"{r.free_agent_adds} FA adds")
            if r.trades:
                parts.append(f"{r.trades} trades")
            detail = ", ".join(parts) if parts else "0 moves"
            lines.append(f"  {name}: {r.total_moves} total moves ({detail})")

    if not lines:
        return ""

    return "\n".join(lines) + "\n"
