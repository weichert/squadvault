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
from collections.abc import Sequence
from dataclasses import dataclass

from squadvault.core.storage.session import DatabaseSession

# ── Scoring Deltas ───────────────────────────────────────────────────


@dataclass(frozen=True)
class ScoringDelta:
    """Week-over-week scoring change for a single franchise."""
    franchise_id: str
    this_week_score: float
    last_week_score: float | None  # None if no prior week data
    delta: float | None            # this_week - last_week, or None

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
) -> tuple[ScoringDelta, ...]:
    """Compute scoring deltas (this week vs last week) for all teams.

    Returns a tuple of ScoringDelta, one per franchise that played this week.
    If the franchise didn't play last week, delta is None.
    """
    this_week_scores: dict[str, float] = {}
    last_week_scores: dict[str, float] = {}

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

    deltas: list[ScoringDelta] = []
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
    budget: float | None           # league budget if provided
    remaining: float | None        # budget - total_spent, or None
    pct_spent: float | None        # total_spent / budget, or None


def derive_faab_spending(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    faab_budget: float | None = None,
    through_occurred_at: str | None = None,
) -> tuple[FaabSpending, ...]:
    """Compute cumulative FAAB spending per franchise through a given week.

    Reads all WAIVER_BID_AWARDED canonical events for the season and sums
    bid amounts per franchise.

    If through_occurred_at is provided, only includes events with
    occurred_at <= that timestamp (ISO-8601).

    faab_budget: if provided, computes remaining budget and % spent.
    """
    spending: dict[str, float] = {}
    counts: dict[str, int] = {}

    sql = """SELECT payload_json FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'"""
    params: list = [str(league_id), int(season)]

    if through_occurred_at:
        sql += " AND occurred_at IS NOT NULL AND occurred_at <= ?"
        params.append(through_occurred_at)

    with DatabaseSession(db_path) as con:
        rows = con.execute(sql, params).fetchall()

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

    results: list[FaabSpending] = []
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


# ── Individual FAAB Acquisitions ─────────────────────────────────────


@dataclass(frozen=True)
class FaabAcquisition:
    """A single FAAB acquisition: player picked up by a franchise."""
    franchise_id: str
    player_id: str
    bid_amount: float
    occurred_at: str | None


def derive_faab_acquisitions(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    through_occurred_at: str | None = None,
) -> tuple[FaabAcquisition, ...]:
    """Derive individual FAAB acquisitions (franchise, player, bid) through a week.

    Returns one FaabAcquisition per WAIVER_BID_AWARDED event, ordered by
    occurred_at ascending (earliest first).  Player names are NOT resolved
    here — callers must resolve via PlayerResolver if display names are needed.
    """
    sql = """SELECT payload_json, occurred_at
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'"""
    params: list = [str(league_id), int(season)]

    if through_occurred_at:
        sql += " AND occurred_at IS NOT NULL AND occurred_at <= ?"
        params.append(through_occurred_at)

    sql += " ORDER BY occurred_at ASC NULLS LAST"

    acquisitions: list[FaabAcquisition] = []

    with DatabaseSession(db_path) as con:
        rows = con.execute(sql, params).fetchall()

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

        # Resolve player_id (single or first-of-many)
        pid = str(p.get("player_id", "")).strip()
        if not pid:
            added = p.get("players_added_ids")
            if isinstance(added, str) and added.strip():
                pid = added.split(",")[0].strip()
            elif isinstance(added, list) and added:
                pid = str(added[0]).strip()
        if not pid:
            continue

        bid = p.get("bid") or p.get("bid_amount") or p.get("amount")
        if bid is None:
            continue
        try:
            bid_val = float(bid)
        except (ValueError, TypeError):
            continue
        if bid_val <= 0:
            continue

        occurred_at = str(row[1]) if row[1] else None

        acquisitions.append(FaabAcquisition(
            franchise_id=fid,
            player_id=pid,
            bid_amount=round(bid_val, 2),
            occurred_at=occurred_at,
        ))

    return tuple(acquisitions)


# ── Prompt rendering ─────────────────────────────────────────────────



@dataclass(frozen=True)
class FaabRoiEntry:
    """FAAB return-on-investment for a single acquisition.

    Computes total fantasy points scored by the player for the acquiring
    franchise since the acquisition week, giving a deterministic
    post-acquisition performance figure the creative layer can cite.
    """
    franchise_id: str
    player_id: str
    bid_amount: float
    total_points_since_acquisition: float
    weeks_scored: int                # weeks with score > 0 since acquisition
    acquisition_week: int            # approximate week of acquisition


def derive_faab_roi(
    acquisitions: Sequence[FaabAcquisition],
    *,
    player_season_history: dict[tuple[str, str], list[tuple[int, float, bool]]],
    current_week: int,
) -> tuple[FaabRoiEntry, ...]:
    """Compute FAAB ROI for each acquisition using season player history.

    player_season_history: {(franchise_id, player_id): [(week, score, is_starter), ...]}
    Typically derived from _load_season_player_history in player_week_context_v1.

    acquisition_week is approximated from occurred_at; we use the week of the
    player's first appearance on the franchise roster after the acquisition date
    as a proxy. If occurred_at is not available, week 1 is assumed.

    Only acquisitions with bid_amount > 0 and at least one scored week are included.
    """
    results: list[FaabRoiEntry] = []

    for acq in acquisitions:
        if acq.bid_amount <= 0:
            continue

        key = (acq.franchise_id, acq.player_id)
        history = player_season_history.get(key, [])
        if not history:
            continue

        # Find the first week the player scored for this franchise
        scored_entries = [(w, s) for (w, s, _) in history if s > 0 and w <= current_week]
        if not scored_entries:
            continue

        total_pts = round(sum(s for (_, s) in scored_entries), 2)
        weeks_scored = len(scored_entries)
        first_week = scored_entries[0][0]

        results.append(FaabRoiEntry(
            franchise_id=acq.franchise_id,
            player_id=acq.player_id,
            bid_amount=acq.bid_amount,
            total_points_since_acquisition=total_pts,
            weeks_scored=weeks_scored,
            acquisition_week=first_week,
        ))

    return tuple(results)


def render_writer_room_context_for_prompt(
    *,
    deltas: Sequence[ScoringDelta],
    faab: Sequence[FaabSpending],
    acquisitions: Sequence[FaabAcquisition] | None = None,
    roi: Sequence[FaabRoiEntry] | None = None,
    name_map: dict[str, str] | None = None,
    player_name_map: dict[str, str] | None = None,
) -> str:
    """Render scoring deltas, FAAB spending, individual acquisitions, and ROI for the creative layer.

    acquisitions: individual FAAB bids from derive_faab_acquisitions().
    roi: post-acquisition performance from derive_faab_roi().
    player_name_map: player_id -> display_name for resolving player names.
    """

    def _name(fid: str) -> str:
        """Resolve franchise ID to display name."""
        if name_map and fid in name_map:
            return name_map[fid]
        return fid

    lines: list[str] = []

    # Scoring deltas
    deltas_with_data = [d for d in deltas if d.has_delta]
    if deltas_with_data:
        lines.append("Week-over-week scoring changes:")
        # Sort by absolute delta descending (biggest swings first)
        sorted_deltas = sorted(deltas_with_data, key=lambda d: -abs(d.delta or 0.0))
        for d in sorted_deltas:
            assert d.delta is not None  # guaranteed by has_delta filter
            name = _name(d.franchise_id)
            direction = "+" if d.delta >= 0 else ""
            lines.append(
                f"  {name}: {d.this_week_score:.2f} (was {d.last_week_score:.2f}, {direction}{d.delta:.2f})"
            )

    # FAAB spending
    if faab:
        if lines:
            lines.append("")
        lines.append("FAAB spending through this week:")
        sorted_faab = sorted(faab, key=lambda f: -f.total_spent)
        for f in sorted_faab:
            name = _name(f.franchise_id)
            budget_str = ""
            if f.remaining is not None and f.budget is not None:
                pct = f.pct_spent * 100 if f.pct_spent is not None else 0
                budget_str = f" (${f.remaining:.0f} remaining of ${f.budget:.0f}, {pct:.0f}% spent)"
            lines.append(
                f"  {name}: ${f.total_spent:.0f} spent{budget_str}"
            )

    # Individual FAAB acquisitions: per-franchise list of player+bid pairs
    # These are the ONLY dollar figures the creative layer may attribute to
    # individual players. Any amount not present here must not appear in prose.
    if acquisitions:
        # Group by franchise
        by_franchise: dict[str, list[FaabAcquisition]] = {}
        for acq in acquisitions:
            by_franchise.setdefault(acq.franchise_id, []).append(acq)

        acq_lines: list[str] = []
        for fid in sorted(by_franchise.keys()):
            fname = _name(fid)
            fid_acqs = sorted(by_franchise[fid], key=lambda a: -a.bid_amount)
            for acq in fid_acqs:
                if player_name_map and acq.player_id in player_name_map:
                    raw = player_name_map[acq.player_id]
                    # Convert "Last, First" storage format to "First Last"
                    if ", " in raw:
                        parts = raw.split(", ", 1)
                        player_display = f"{parts[1]} {parts[0]}"
                    else:
                        player_display = raw
                else:
                    player_display = acq.player_id
                acq_lines.append(
                    f"  {fname}: ${acq.bid_amount:.0f} for {player_display}"
                )

        if acq_lines:
            if lines:
                lines.append("")
            lines.append(
                "FAAB COPY-ONLY: the dollar amounts below are the ONLY FAAB figures "
                "that exist this season. Cite a player's FAAB amount ONLY by copying "
                "one of these exact lines. Any player NOT listed here received NO FAAB "
                "bid — never attach a dollar amount to them. Never invent or estimate a "
                "FAAB amount."
            )
            lines.extend(acq_lines)
    elif faab:
        # Explicit absence (fork b): FAAB spending exists but no per-player
        # acquisitions to cite -> say so, so the model has a "none" to land on
        # instead of a void it fills. (Truly-empty input still renders empty.)
        if lines:
            lines.append("")
        lines.append(
            "No individual FAAB acquisitions on record — do not cite any FAAB "
            "dollar amount for any player this week."
        )

    # FAAB ROI: post-acquisition points scored per player
    # Gives the model a factual basis for "paid off" or "hasn't delivered" claims.
    if roi:
        roi_lines: list[str] = []
        for r in sorted(roi, key=lambda x: -x.total_points_since_acquisition):
            fname = _name(r.franchise_id)
            if player_name_map and r.player_id in player_name_map:
                raw = player_name_map[r.player_id]
                if ", " in raw:
                    parts = raw.split(", ", 1)
                    pname = f"{parts[1]} {parts[0]}"
                else:
                    pname = raw
            else:
                pname = r.player_id
            roi_lines.append(
                f"  {fname}: {pname} — ${r.bid_amount:.0f} bid, "
                f"{r.total_points_since_acquisition:.2f} pts in {r.weeks_scored} week(s)"
            )

        if roi_lines:
            if lines:
                lines.append("")
            lines.append(
                "FAAB post-acquisition performance "
                "(total pts scored for this franchise since pickup):"
            )
            lines.extend(roi_lines)

    if not lines:
        return ""

    return "\n".join(lines) + "\n"


# ── Manager Identity Context (Arc 2 Phase D) ──────────────────────────


@dataclass(frozen=True)
class ManagerIdentity:
    """Resolved manager identity for a single franchise."""
    franchise_id: str
    team_name: str          # full franchise display name
    owner_name: str | None  # full owner name from franchise_directory
    owner_first: str | None # owner first name (first word of owner_name)
    nickname: str | None    # commissioner-curated short-form (e.g. "KP")

    @property
    def preferred_short_form(self) -> str | None:
        """Return the best short-form identifier: nickname > owner_first > None."""
        return self.nickname or self.owner_first


def derive_manager_identities(
    *,
    db_path: str,
    league_id: str,
    season: int,
    name_map: dict[str, str] | None = None,
) -> tuple[ManagerIdentity, ...]:
    """Resolve manager identities (team name + owner name + nickname) per franchise.

    Reads franchise_directory (owner_name) and franchise_nicknames (curated
    short-form) to build a complete identity record for each franchise.

    name_map: optional pre-built franchise_id -> display_name dict; if None,
    team names are loaded from franchise_directory.
    """
    with DatabaseSession(db_path) as con:
        # Owner names from franchise_directory
        owner_rows = con.execute(
            """SELECT franchise_id, name, owner_name
               FROM franchise_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()

        # Curated nicknames from franchise_nicknames
        nick_rows = con.execute(
            """SELECT franchise_id, nickname
               FROM franchise_nicknames
               WHERE league_id = ?""",
            (str(league_id),),
        ).fetchall()

    nick_map: dict[str, str] = {
        str(r[0]).strip(): str(r[1]).strip()
        for r in nick_rows
        if r[0] and r[1] and str(r[1]).strip()
    }

    identities: list[ManagerIdentity] = []
    for row in owner_rows:
        fid = str(row[0]).strip()
        if not fid:
            continue

        team = name_map.get(fid, str(row[1] or fid).strip()) if name_map else str(row[1] or fid).strip()
        raw_owner = str(row[2]).strip() if row[2] else None
        owner_first = raw_owner.split()[0] if raw_owner and raw_owner.split() else None
        nickname = nick_map.get(fid)

        identities.append(ManagerIdentity(
            franchise_id=fid,
            team_name=team,
            owner_name=raw_owner,
            owner_first=owner_first,
            nickname=nickname,
        ))

    identities.sort(key=lambda m: m.franchise_id)
    return tuple(identities)


def render_manager_identities_for_prompt(
    identities: Sequence[ManagerIdentity],
) -> str:
    """Render manager identity block for the creative layer prompt.

    Provides short-form identifiers so the model can address managers
    by their preferred name rather than the full franchise name.
    Format:
        Manager identity (use short-form when writing about managers):
          <team_name> (<franchise_id>): short-form = "<preferred_short_form>"
    """
    if not identities:
        return ""

    lines: list[str] = [
        "Manager identity "
        "(use the short-form when addressing or referring to a manager — "
        "it's how the league talks about them):"
    ]
    for m in identities:
        short = m.preferred_short_form
        if short:
            lines.append(f"  {m.team_name} ({m.franchise_id}): short-form = \"{short}\"")

    if len(lines) == 1:
        return ""  # no short forms available

    return "\n".join(lines) + "\n"
