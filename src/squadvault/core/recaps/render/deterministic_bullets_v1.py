"""Deterministic factual bullet generation from canonical events."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)
QUIET_WEEK_MIN_EVENTS = 3
MAX_BULLETS = 20

_SKIP_EVENT_TYPES = {
    "TRANSACTION_BBID_WAIVER",
}


@dataclass(frozen=True)
class CanonicalEventRow:
    canonical_id: str
    occurred_at: str
    event_type: str
    payload: dict[str, Any]


def _ascii_punct(s: str) -> str:
    # Normalize curly apostrophe and a couple common unicode dashes for stable exports/terminals.
    """Normalize curly quotes and unicode dashes to ASCII equivalents."""
    return (
        s.replace("\u2019", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )


def _safe(s: Any, fallback: str) -> str:
    """Return str(s).strip() or fallback if s is None/empty."""
    if s is None:
        return fallback
    s2 = str(s).strip()
    return s2 if s2 else fallback


def _team(res_team: Callable[[Any], str] | None, raw: Any) -> str:
    """Resolve team ID to display name via resolver, with fallback."""
    if res_team is None:
        return _ascii_punct(_safe(raw, "Unknown team"))
    try:
        return _ascii_punct(_safe(res_team(raw), "Unknown team"))
    except Exception as exc:
        logger.debug("%s", exc)
        return "Unknown team"


def _player(res_player: Callable[[Any], str] | None, raw: Any) -> str:
    """Resolve player ID to display name via resolver, with fallback."""
    if res_player is None:
        return _ascii_punct(_safe(raw, "Unknown player"))
    try:
        return _ascii_punct(_safe(res_player(raw), "Unknown player"))
    except Exception as exc:
        logger.debug("%s", exc)
        return "Unknown player"


def _money(raw: Any) -> str:
    """Format a raw value as dollar amount, or return fallback."""
    try:
        n = int(raw)
        return f"${n}"
    except (ValueError, TypeError):
        return _safe(raw, "")


def _csv_ids(raw: str) -> list[str]:
    """Split a comma-separated string of IDs, stripping whitespace.

    Retained only to support the pre-promotion ``raw_mfl_json`` fallback
    path in ``_extract_mfl_trade``. Post-promotion trade events carry
    player-ID lists as native ``list[str]`` on the canonical payload
    (``trade_franchise_a_gave_up`` / ``trade_franchise_b_gave_up``) and
    do not go through this helper.
    """
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _extract_canonical_trade(p: dict[str, Any]) -> dict[str, Any] | None:
    """Extract bilateral trade structure from canonical payload fields.

    Post-promotion (per S10 leak #2 resolution at b26e93f),
    TRANSACTION_TRADE envelopes carry ``trade_franchise_a_gave_up`` and
    ``trade_franchise_b_gave_up`` as native ``list[str]`` alongside the
    already-promoted ``franchise_id`` (the initiator) and
    ``franchise_ids_involved`` (all franchises referenced). Franchise B
    is derived as the first member of ``franchise_ids_involved`` that is
    not franchise A.

    Key-presence on ``trade_franchise_a_gave_up`` is the post-promotion
    signal. Returns None when the key is absent (caller should fall
    back to ``_extract_mfl_trade``) or when A/B cannot be resolved
    (no initiator, or ``franchise_ids_involved`` contains only A).
    """
    if "trade_franchise_a_gave_up" not in p:
        return None

    f_a = str(p.get("franchise_id") or "").strip()
    if not f_a:
        return None

    involved = p.get("franchise_ids_involved") or []
    if not isinstance(involved, list):
        return None
    f_b = ""
    for fid in involved:
        s = str(fid or "").strip()
        if s and s != f_a:
            f_b = s
            break
    if not f_b:
        return None

    gave_a_raw = p.get("trade_franchise_a_gave_up") or []
    gave_b_raw = p.get("trade_franchise_b_gave_up") or []
    if not isinstance(gave_a_raw, list) or not isinstance(gave_b_raw, list):
        return None
    gave_a = [str(x).strip() for x in gave_a_raw if str(x).strip()]
    gave_b = [str(x).strip() for x in gave_b_raw if str(x).strip()]

    return {
        "franchise_a_id": f_a,
        "franchise_b_id": f_b,
        "franchise_a_gave_up_ids": gave_a,
        "franchise_b_gave_up_ids": gave_b,
    }


def _extract_mfl_trade(p: dict[str, Any]) -> dict[str, Any] | None:
    """Extract normalized trade fields from ``raw_mfl_json`` (fallback).

    Pre-promotion fallback path for TRANSACTION_TRADE events ingested
    before the S10 leak #2 resolution promoted per-franchise trade
    structure into the canonical payload. Post-promotion events carry
    that structure as ``trade_franchise_a_gave_up`` /
    ``trade_franchise_b_gave_up`` on the envelope and are handled by
    ``_extract_canonical_trade``; this helper runs only when those
    canonical fields are absent from the payload (memory ledger is
    append-only, so old events retain their old shape).

    MFL raw trades have ``franchise``, ``franchise2``,
    ``franchise1_gave_up``, ``franchise2_gave_up``. Returns a dict with
    ``franchise_a_id``, ``franchise_b_id``, ``franchise_a_gave_up_ids``,
    ``franchise_b_gave_up_ids``, or None if ``raw_mfl_json`` is absent
    or unparseable.
    """
    raw_str = p.get("raw_mfl_json")
    if not raw_str or not isinstance(raw_str, str):
        return None
    try:
        raw = json.loads(raw_str)
    except (ValueError, TypeError):
        return None
    if not isinstance(raw, dict):
        return None
    f1 = raw.get("franchise")
    f2 = raw.get("franchise2")
    if not f1 or not f2:
        return None
    return {
        "franchise_a_id": str(f1).strip(),
        "franchise_b_id": str(f2).strip(),
        "franchise_a_gave_up_ids": _csv_ids(raw.get("franchise1_gave_up", "")),
        "franchise_b_gave_up_ids": _csv_ids(raw.get("franchise2_gave_up", "")),
    }


def render_deterministic_bullets_v1(
    events: Iterable[CanonicalEventRow],
    *,
    team_resolver: Callable[[Any], str] | None = None,
    player_resolver: Callable[[Any], str] | None = None,
    player_position_resolver: Callable[[Any], str] | None = None,
) -> list[str]:
    """
    Deterministic factual bullets derived from canonical events.

    Output is stable given the same input rows and resolvers.
    No LLM, no randomness, no inference.

    player_position_resolver: optional callable (player_id -> position string).
    When provided, bullets include position (e.g. "Patrick Mahomes (QB)").
    """
    rows = list(events)
    rows.sort(key=lambda r: (r.occurred_at, r.event_type, r.canonical_id))

    def _player_pos(raw_id: Any) -> str:
        """Resolve player to 'Name (POS)' or just 'Name' if no position available."""
        name = _player(player_resolver, raw_id)
        if player_position_resolver is not None and raw_id:
            try:
                pos = player_position_resolver(raw_id)
                if pos and str(pos).strip() and str(pos).strip() not in ("", "None"):
                    return f"{name} ({str(pos).strip()})"
            except (KeyError, ValueError, TypeError, LookupError):
                pass
        return name

    bullets: list[str] = []
    seen: set[str] = set()

    for r in rows:
        if len(bullets) >= MAX_BULLETS:
            break

        p = r.payload or {}
        et = r.event_type

        if et in _SKIP_EVENT_TYPES:
            continue

        # Silence over fabrication: skip events with empty payloads.
        # An empty payload means we cannot identify participants — producing
        # a bullet would yield "? added <?>" which erodes trust.
        if not p:
            continue

        bullet = None

        if et in ("TRANSACTION_TRADE", "TRADE"):
            # Try standard fields first (test fixtures / synthetic shapes)
            from_id = p.get("from_franchise_id") or p.get("from_team_id")
            to_id = p.get("to_franchise_id") or p.get("to_team_id")
            pid = p.get("player_id") or p.get("player")

            if from_id and to_id:
                # Standard trade format
                from_team = _team(team_resolver, from_id)
                to_team = _team(team_resolver, to_id)
                player = _player_pos(pid)
                bullet = f"{to_team} acquired {player} from {from_team}."
            else:
                # MFL trade: prefer canonical promoted fields; fall back to
                # raw_mfl_json parsing for events ingested pre-promotion
                # (S10 leak #2 at b26e93f / leak #4 at this commit).
                trade = _extract_canonical_trade(p) or _extract_mfl_trade(p)
                if trade:
                    t1 = _team(team_resolver, trade["franchise_a_id"])
                    t2 = _team(team_resolver, trade["franchise_b_id"])
                    gave1 = [_player_pos(x) for x in trade["franchise_a_gave_up_ids"]]
                    gave2 = [_player_pos(x) for x in trade["franchise_b_gave_up_ids"]]
                    if gave1 and gave2:
                        players1 = ", ".join(gave1)
                        players2 = ", ".join(gave2)
                        bullet = f"{t1} traded {players1} to {t2} for {players2}."
                    else:
                        bullet = f"{t1} and {t2} completed a trade."

        elif et in ("WAIVER_BID_AWARDED",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player_pos(p.get("player_id") or p.get("player"))
            bid = _money(p.get("bid") or p.get("bid_amount") or p.get("amount") or "")
            bid_txt = f" for {bid}" if bid else ""
            bullet = f"{team} won {player}{bid_txt} on waivers."

        elif et in ("TRANSACTION_FREE_AGENT",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player_pos(p.get("player_id") or p.get("player"))
            bullet = f"{team} added {player} (free agent)."

        elif et in ("DRAFT_PICK",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player_pos(p.get("player_id") or p.get("player"))
            rnd = _safe(p.get("round"), "")
            pick = _safe(p.get("pick"), "")
            suffix = ""
            if rnd and pick:
                suffix = f" (Round {rnd}, Pick {pick})"
            elif rnd:
                suffix = f" (Round {rnd})"
            bullet = f"Draft: {team} selected {player}{suffix}."

        elif et in ("MATCHUP_RESULT", "WEEKLY_MATCHUP_RESULT"):
            winner = _team(team_resolver, p.get("winner_franchise_id") or p.get("winner_team_id"))
            loser = _team(team_resolver, p.get("loser_franchise_id") or p.get("loser_team_id"))
            w = _safe(p.get("winner_score"), "")
            l = _safe(p.get("loser_score"), "")
            score_txt = f" {w}-{l}" if (w and l) else ""
            is_tie = p.get("is_tie", False)
            if is_tie:
                bullet = f"{winner} tied {loser}{score_txt}."
            else:
                bullet = f"{winner} beat {loser}{score_txt}."

        else:
            # Conservative MVP: don't emit low-signal transaction noise.
            if et.startswith("TRANSACTION_"):
                continue
            bullet = f"{et.replace('_', ' ').title()} recorded."

        if bullet is not None:
            bullet = _ascii_punct(bullet)
            # Deduplicate: same trade ingested multiple times produces identical bullets
            if bullet not in seen:
                seen.add(bullet)
                bullets.append(bullet)

    return bullets
