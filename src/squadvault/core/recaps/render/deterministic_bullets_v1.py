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
    """Split a comma-separated string of IDs, stripping whitespace."""
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _extract_mfl_trade(p: dict[str, Any]) -> dict[str, Any] | None:
    """Extract normalized trade fields from raw_mfl_json if present.

    MFL trades have: franchise, franchise2, franchise1_gave_up, franchise2_gave_up.
    Returns a dict with franchise1_id, franchise2_id, franchise1_gave_up_ids,
    franchise2_gave_up_ids, or None if raw_mfl_json is absent/unparseable.
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
        "franchise1_id": str(f1).strip(),
        "franchise2_id": str(f2).strip(),
        "franchise1_gave_up_ids": _csv_ids(raw.get("franchise1_gave_up", "")),
        "franchise2_gave_up_ids": _csv_ids(raw.get("franchise2_gave_up", "")),
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
            # Try standard fields first
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
                # MFL trade format: extract from raw_mfl_json
                mfl = _extract_mfl_trade(p)
                if mfl:
                    t1 = _team(team_resolver, mfl["franchise1_id"])
                    t2 = _team(team_resolver, mfl["franchise2_id"])
                    gave1 = [_player_pos(pid) for pid in mfl["franchise1_gave_up_ids"]]
                    gave2 = [_player_pos(pid) for pid in mfl["franchise2_gave_up_ids"]]
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
