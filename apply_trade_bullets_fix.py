#!/usr/bin/env python3
"""Apply: Fix trade bullet rendering + MAX_BULLETS counting.

Three issues fixed:
1. Trade payloads not normalized — raw_mfl_json has the data but the
   renderer only looks for from_franchise_id/to_franchise_id/player_id
2. MAX_BULLETS counts skipped events — BBID and empty-payload events
   waste bullet slots, truncating real events
3. Duplicate bullets — trade events ingested 3x produce identical bullets

Changes:
  src/squadvault/core/recaps/render/deterministic_bullets_v1.py
  Tests/test_deterministic_bullets_v1.py
"""

import pathlib

ROOT = pathlib.Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────
# 1. Rewrite deterministic_bullets_v1.py
# ─────────────────────────────────────────────────────────────────────

bullets_path = ROOT / "src" / "squadvault" / "core" / "recaps" / "render" / "deterministic_bullets_v1.py"
bullets_path.write_text('''\
"""Deterministic factual bullet generation from canonical events."""

from __future__ import annotations

import json
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
    """Normalize curly quotes and unicode dashes to ASCII equivalents."""
    return (
        s.replace("\\u2019", "'")
        .replace("\\u2013", "-")
        .replace("\\u2014", "-")
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
    except Exception:
        return "Unknown team"


def _player(res_player: Callable[[Any], str] | None, raw: Any) -> str:
    """Resolve player ID to display name via resolver, with fallback."""
    if res_player is None:
        return _ascii_punct(_safe(raw, "Unknown player"))
    try:
        return _ascii_punct(_safe(res_player(raw), "Unknown player"))
    except Exception:
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
) -> list[str]:
    """
    Deterministic factual bullets derived from canonical events.

    Output is stable given the same input rows and resolvers.
    No LLM, no randomness, no inference.
    """
    rows = list(events)
    rows.sort(key=lambda r: (r.occurred_at, r.event_type, r.canonical_id))

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
                player = _player(player_resolver, pid)
                bullet = f"{to_team} acquired {player} from {from_team}."
            else:
                # MFL trade format: extract from raw_mfl_json
                mfl = _extract_mfl_trade(p)
                if mfl:
                    t1 = _team(team_resolver, mfl["franchise1_id"])
                    t2 = _team(team_resolver, mfl["franchise2_id"])
                    gave1 = [_player(player_resolver, pid) for pid in mfl["franchise1_gave_up_ids"]]
                    gave2 = [_player(player_resolver, pid) for pid in mfl["franchise2_gave_up_ids"]]
                    if gave1 and gave2:
                        players1 = ", ".join(gave1)
                        players2 = ", ".join(gave2)
                        bullet = f"{t1} traded {players1} to {t2} for {players2}."
                    else:
                        bullet = f"{t1} and {t2} completed a trade."

        elif et in ("WAIVER_BID_AWARDED",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player(player_resolver, p.get("player_id") or p.get("player"))
            bid = _money(p.get("bid") or p.get("amount") or "")
            bid_txt = f" for {bid}" if bid else ""
            bullet = f"{team} won {player}{bid_txt} on waivers."

        elif et in ("TRANSACTION_FREE_AGENT",):
            team = _team(team_resolver, p.get("franchise_id") or p.get("team_id"))
            player = _player(player_resolver, p.get("player_id") or p.get("player"))
            bullet = f"{team} added {player} (free agent)."

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
''')
print(f"\\u2713 Wrote {bullets_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 2. Update tests
# ─────────────────────────────────────────────────────────────────────

test_path = ROOT / "Tests" / "test_deterministic_bullets_v1.py"
test_text = test_path.read_text()

# Add MFL trade tests and MAX_BULLETS fix test
# Find the end of the test file and append new test classes

new_tests = '''

# ── MFL trade rendering ─────────────────────────────────────────────

class TestMflTradeRendering:
    def test_mfl_trade_with_raw_json(self):
        # MFL trades store data in raw_mfl_json, not standard fields
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "franchise_id": "0004",
            "mfl_type": "TRADE",
            "player_id": None,
            "raw_mfl_json": '{"franchise":"0004","franchise2":"0010",'
                           '"franchise1_gave_up":"15754,","franchise2_gave_up":"16214,",'
                           '"timestamp":"1726111841","type":"TRADE"}',
        })
        bullets = render_deterministic_bullets_v1([row])
        assert len(bullets) == 1
        assert "0004" in bullets[0] and "0010" in bullets[0]
        assert "traded" in bullets[0]
        assert "15754" in bullets[0] and "16214" in bullets[0]

    def test_mfl_trade_with_resolvers(self):
        team_res = lambda fid: {"0004": "Eagles", "0010": "Hawks"}.get(fid, fid)
        player_res = lambda pid: {"15754": "Chris Olave", "16214": "Sam LaPorta"}.get(pid, pid)
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "franchise_id": "0004",
            "raw_mfl_json": '{"franchise":"0004","franchise2":"0010",'
                           '"franchise1_gave_up":"15754,","franchise2_gave_up":"16214,",'
                           '"timestamp":"1726111841","type":"TRADE"}',
        })
        bullets = render_deterministic_bullets_v1(
            [row], team_resolver=team_res, player_resolver=player_res,
        )
        assert bullets == ["Eagles traded Chris Olave to Hawks for Sam LaPorta."]

    def test_mfl_trade_no_raw_json_no_standard_fields(self):
        # No raw_mfl_json AND no standard trade fields = silence
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "franchise_id": "0004",
            "mfl_type": "TRADE",
        })
        bullets = render_deterministic_bullets_v1([row])
        # No from/to fields, no raw_mfl_json — cannot render
        assert bullets == []

    def test_standard_trade_still_works(self):
        # Standard from/to fields take priority over raw_mfl_json
        row = _row(event_type="TRADE", payload={
            "from_franchise_id": "F01",
            "to_franchise_id": "F02",
            "player_id": "P100",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["F02 acquired P100 from F01."]


# ── Duplicate bullet filtering ───────────────────────────────────────

class TestDuplicateFiltering:
    def test_identical_events_produce_one_bullet(self):
        # Same trade ingested 3 times produces 3 canonical events
        # but should render only 1 bullet
        payload = {
            "franchise_id": "0004",
            "raw_mfl_json": '{"franchise":"0004","franchise2":"0010",'
                           '"franchise1_gave_up":"15754,","franchise2_gave_up":"16214,",'
                           '"timestamp":"1726111841","type":"TRADE"}',
        }
        rows = [
            _row(canonical_id=f"trade_{i}", event_type="TRANSACTION_TRADE", payload=payload)
            for i in range(3)
        ]
        bullets = render_deterministic_bullets_v1(rows)
        assert len(bullets) == 1

    def test_different_events_not_deduped(self):
        rows = [
            _row(canonical_id="m1", event_type="MATCHUP_RESULT", payload={
                "winner_franchise_id": "W1", "loser_franchise_id": "L1",
                "winner_score": 100, "loser_score": 90,
            }),
            _row(canonical_id="m2", event_type="MATCHUP_RESULT", payload={
                "winner_franchise_id": "W2", "loser_franchise_id": "L2",
                "winner_score": 110, "loser_score": 95,
            }),
        ]
        bullets = render_deterministic_bullets_v1(rows)
        assert len(bullets) == 2


# ── MAX_BULLETS counts only rendered bullets ─────────────────────────

class TestMaxBulletsCountsRendered:
    def test_skipped_events_dont_consume_slots(self):
        # 10 BBID events (skipped) + 25 matchup events
        # Old behavior: only first 20 rows processed, 10 BBID consume slots = 10 matchups
        # New behavior: skip BBIDs, render up to 20 matchup bullets
        bbid_rows = [
            _row(canonical_id=f"bbid_{i}", occurred_at=f"2024-10-{(i % 28) + 1:02d}",
                 event_type="TRANSACTION_BBID_WAIVER", payload={"x": 1})
            for i in range(10)
        ]
        matchup_rows = [
            _row(canonical_id=f"match_{i}", occurred_at=f"2024-10-{(i % 28) + 1:02d}",
                 event_type="MATCHUP_RESULT", payload={
                     "winner_franchise_id": f"W{i}", "loser_franchise_id": f"L{i}",
                 })
            for i in range(25)
        ]
        bullets = render_deterministic_bullets_v1(bbid_rows + matchup_rows)
        assert len(bullets) == MAX_BULLETS
'''

# Append the new tests
test_text += new_tests
test_path.write_text(test_text)
print(f"\\u2713 Patched {test_path.relative_to(ROOT)}")


print()
print("Apply complete. Verify:")
print("  PYTHONPATH=src python -m pytest Tests/ -q")
