from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

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
    return (
        s.replace("\u2019", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )


def _safe(s: Any, fallback: str) -> str:
    if s is None:
        return fallback
    s2 = str(s).strip()
    return s2 if s2 else fallback


def _team(res_team: Callable[[Any], str] | None, raw: Any) -> str:
    if res_team is None:
        return _ascii_punct(_safe(raw, "Unknown team"))
    try:
        return _ascii_punct(_safe(res_team(raw), "Unknown team"))
    except Exception:
        return "Unknown team"


def _player(res_player: Callable[[Any], str] | None, raw: Any) -> str:
    if res_player is None:
        return _ascii_punct(_safe(raw, "Unknown player"))
    try:
        return _ascii_punct(_safe(res_player(raw), "Unknown player"))
    except Exception:
        return "Unknown player"


def _money(raw: Any) -> str:
    try:
        n = int(raw)
        return f"${n}"
    except Exception:
        return _safe(raw, "")


def render_deterministic_bullets_v1(
    events: Iterable[CanonicalEventRow],
    *,
    team_resolver: Callable[[Any], str] | None = None,
    player_resolver: Callable[[Any], str] | None = None,
) -> list[str]:
    """
    Deterministic factual bullets derived from canonical events.

    Output is stable given the same input rows and resolvers.
    No LLM, no randomness, no inference.
    """
    rows = list(events)
    rows.sort(key=lambda r: (r.occurred_at, r.event_type, r.canonical_id))

    bullets: list[str] = []
    for r in rows[:MAX_BULLETS]:
        p = r.payload or {}
        et = r.event_type

        if et in _SKIP_EVENT_TYPES:
            continue

        if et in ("TRANSACTION_TRADE", "TRADE"):
            from_team = _team(team_resolver, p.get("from_franchise_id") or p.get("from_team_id"))
            to_team = _team(team_resolver, p.get("to_franchise_id") or p.get("to_team_id"))
            player = _player(player_resolver, p.get("player_id") or p.get("player"))
            bullets.append(_ascii_punct(f"{to_team} acquired {player} from {from_team}."))

        elif et in ("WAIVER_BID_AWARDED",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player(player_resolver, p.get("player_id") or p.get("player"))
            bid = _money(p.get("bid") or p.get("amount") or "")
            bid_txt = f" for {bid}" if bid else ""
            bullets.append(_ascii_punct(f"{team} won {player}{bid_txt} on waivers."))

        elif et in ("TRANSACTION_FREE_AGENT",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player(player_resolver, p.get("player_id") or p.get("player"))
            bullets.append(_ascii_punct(f"{team} added {player} (free agent)."))

        elif et in ("DRAFT_PICK",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player(player_resolver, p.get("player_id") or p.get("player"))
            rnd = _safe(p.get("round"), "")
            pick = _safe(p.get("pick"), "")
            suffix = ""
            if rnd and pick:
                suffix = f" (Round {rnd}, Pick {pick})"
            elif rnd:
                suffix = f" (Round {rnd})"
            bullets.append(_ascii_punct(f"Draft: {team} selected {player}{suffix}."))

        elif et in ("MATCHUP_RESULT", "WEEKLY_MATCHUP_RESULT"):
            winner = _team(team_resolver, p.get("winner_franchise_id") or p.get("winner_team_id"))
            loser = _team(team_resolver, p.get("loser_franchise_id") or p.get("loser_team_id"))
            w = _safe(p.get("winner_score"), "")
            l = _safe(p.get("loser_score"), "")
            score_txt = f" {w}-{l}" if (w and l) else ""
            bullets.append(_ascii_punct(f"{winner} beat {loser}{score_txt}."))

        else:
            # Conservative MVP: don't emit low-signal transaction noise.
            if et.startswith("TRANSACTION_"):
                continue
            bullets.append(_ascii_punct(f"{et.replace('_', ' ').title()} recorded."))

    return bullets
