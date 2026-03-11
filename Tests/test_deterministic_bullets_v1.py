"""Tests for squadvault.recaps.deterministic_bullets_v1

Covers: every event type bullet format, deterministic ordering,
skip/silence rules, resolver callbacks, _money edge cases,
unicode normalization, MAX_BULLETS truncation, empty input.
"""
from __future__ import annotations

import pytest

from squadvault.recaps.deterministic_bullets_v1 import (
    CanonicalEventRow,
    MAX_BULLETS,
    _ascii_punct,
    _money,
    _safe,
    render_deterministic_bullets_v1,
)


def _row(
    canonical_id: str = "c1",
    occurred_at: str = "2024-10-01T12:00:00Z",
    event_type: str = "MATCHUP_RESULT",
    payload: dict | None = None,
) -> CanonicalEventRow:
    return CanonicalEventRow(
        canonical_id=canonical_id,
        occurred_at=occurred_at,
        event_type=event_type,
        payload=payload or {},
    )


# ── Empty input ──────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_list(self):
        assert render_deterministic_bullets_v1([]) == []

    def test_generator_empty(self):
        assert render_deterministic_bullets_v1(iter([])) == []


# ── Event type: TRADE ────────────────────────────────────────────────

class TestTradeBullet:
    def test_trade_basic(self):
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "from_franchise_id": "F01",
            "to_franchise_id": "F02",
            "player_id": "P100",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert len(bullets) == 1
        assert "F02" in bullets[0]
        assert "acquired" in bullets[0]
        assert "P100" in bullets[0]
        assert "from F01" in bullets[0]

    def test_trade_alternate_event_type(self):
        row = _row(event_type="TRADE", payload={
            "from_team_id": "TeamA",
            "to_team_id": "TeamB",
            "player": "Joe Burrow",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert len(bullets) == 1
        assert "TeamB acquired Joe Burrow from TeamA." == bullets[0]

    def test_trade_missing_fields_uses_fallbacks(self):
        row = _row(event_type="TRADE", payload={})
        bullets = render_deterministic_bullets_v1([row])
        assert "Unknown team acquired Unknown player from Unknown team." == bullets[0]


# ── Event type: WAIVER_BID_AWARDED ───────────────────────────────────

class TestWaiverBidBullet:
    def test_waiver_with_bid(self):
        row = _row(event_type="WAIVER_BID_AWARDED", payload={
            "franchise_id": "F03",
            "player_id": "P200",
            "bid": 42,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["F03 won P200 for $42 on waivers."]

    def test_waiver_alternate_keys(self):
        row = _row(event_type="WAIVER_BID_AWARDED", payload={
            "team_id": "TeamC",
            "player": "Lamar Jackson",
            "amount": 15,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["TeamC won Lamar Jackson for $15 on waivers."]

    def test_waiver_no_bid(self):
        row = _row(event_type="WAIVER_BID_AWARDED", payload={
            "franchise_id": "F03",
            "player_id": "P200",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["F03 won P200 on waivers."]


# ── Event type: FREE_AGENT ───────────────────────────────────────────

class TestFreeAgentBullet:
    def test_free_agent(self):
        row = _row(event_type="TRANSACTION_FREE_AGENT", payload={
            "team_id": "TeamD",
            "player": "Justin Fields",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["TeamD added Justin Fields (free agent)."]


# ── Event type: DRAFT_PICK ───────────────────────────────────────────

class TestDraftPickBullet:
    def test_draft_with_round_and_pick(self):
        row = _row(event_type="DRAFT_PICK", payload={
            "franchise_id": "F05",
            "player_id": "P300",
            "round": 1,
            "pick": 3,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Draft: F05 selected P300 (Round 1, Pick 3)."]

    def test_draft_round_only(self):
        row = _row(event_type="DRAFT_PICK", payload={
            "franchise_id": "F05",
            "player_id": "P300",
            "round": 2,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Draft: F05 selected P300 (Round 2)."]

    def test_draft_no_round_no_pick(self):
        row = _row(event_type="DRAFT_PICK", payload={
            "franchise_id": "F05",
            "player_id": "P300",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Draft: F05 selected P300."]


# ── Event type: MATCHUP_RESULT ───────────────────────────────────────

class TestMatchupResultBullet:
    def test_matchup_with_scores(self):
        row = _row(event_type="MATCHUP_RESULT", payload={
            "winner_franchise_id": "F10",
            "loser_franchise_id": "F11",
            "winner_score": 120,
            "loser_score": 95,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["F10 beat F11 120-95."]

    def test_matchup_alternate_type(self):
        row = _row(event_type="WEEKLY_MATCHUP_RESULT", payload={
            "winner_team_id": "Champs",
            "loser_team_id": "Underdogs",
            "winner_score": 110,
            "loser_score": 105,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Champs beat Underdogs 110-105."]

    def test_matchup_no_scores(self):
        row = _row(event_type="MATCHUP_RESULT", payload={
            "winner_franchise_id": "F10",
            "loser_franchise_id": "F11",
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["F10 beat F11."]


# ── Skip / silence rules ────────────────────────────────────────────

class TestSkipRules:
    def test_bbid_waiver_skipped(self):
        row = _row(event_type="TRANSACTION_BBID_WAIVER", payload={"x": 1})
        assert render_deterministic_bullets_v1([row]) == []

    def test_generic_transaction_skipped(self):
        """TRANSACTION_* prefixed events not matching known types are silent."""
        row = _row(event_type="TRANSACTION_SOME_NOISE", payload={})
        assert render_deterministic_bullets_v1([row]) == []

    def test_unknown_non_transaction_type_gets_generic_bullet(self):
        row = _row(event_type="LEAGUE_EXPANSION", payload={})
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["League Expansion recorded."]


# ── Deterministic ordering ───────────────────────────────────────────

class TestDeterministicOrdering:
    def test_sorted_by_occurred_at_then_type_then_id(self):
        rows = [
            _row(canonical_id="c3", occurred_at="2024-10-03", event_type="MATCHUP_RESULT",
                 payload={"winner_franchise_id": "W3", "loser_franchise_id": "L3"}),
            _row(canonical_id="c1", occurred_at="2024-10-01", event_type="MATCHUP_RESULT",
                 payload={"winner_franchise_id": "W1", "loser_franchise_id": "L1"}),
            _row(canonical_id="c2", occurred_at="2024-10-02", event_type="DRAFT_PICK",
                 payload={"franchise_id": "F", "player_id": "P"}),
        ]
        bullets = render_deterministic_bullets_v1(rows)
        assert len(bullets) == 3
        assert "W1 beat L1" in bullets[0]
        assert "Draft:" in bullets[1]
        assert "W3 beat L3" in bullets[2]

    def test_same_input_same_output(self):
        """Determinism: repeated calls yield identical results."""
        rows = [
            _row(canonical_id="a", occurred_at="2024-10-01", event_type="MATCHUP_RESULT",
                 payload={"winner_franchise_id": "W", "loser_franchise_id": "L",
                          "winner_score": 100, "loser_score": 90}),
            _row(canonical_id="b", occurred_at="2024-10-01", event_type="WAIVER_BID_AWARDED",
                 payload={"franchise_id": "T", "player_id": "P", "bid": 5}),
        ]
        result1 = render_deterministic_bullets_v1(rows)
        result2 = render_deterministic_bullets_v1(rows)
        assert result1 == result2


# ── Resolver callbacks ───────────────────────────────────────────────

class TestResolvers:
    def test_team_resolver_applied(self):
        resolver = lambda fid: {"F01": "Eagles", "F02": "Hawks"}.get(fid, fid)
        row = _row(event_type="TRADE", payload={
            "from_franchise_id": "F01",
            "to_franchise_id": "F02",
            "player_id": "P1",
        })
        bullets = render_deterministic_bullets_v1([row], team_resolver=resolver)
        assert "Hawks acquired P1 from Eagles." == bullets[0]

    def test_player_resolver_applied(self):
        resolver = lambda pid: {"P1": "Patrick Mahomes"}.get(pid, pid)
        row = _row(event_type="TRANSACTION_FREE_AGENT", payload={
            "franchise_id": "F01",
            "player_id": "P1",
        })
        bullets = render_deterministic_bullets_v1([row], player_resolver=resolver)
        assert "F01 added Patrick Mahomes (free agent)." == bullets[0]

    def test_resolver_exception_returns_fallback(self):
        def bad_resolver(_):
            raise ValueError("boom")

        row = _row(event_type="TRANSACTION_FREE_AGENT", payload={
            "franchise_id": "F01",
            "player_id": "P1",
        })
        bullets = render_deterministic_bullets_v1(
            [row], team_resolver=bad_resolver, player_resolver=bad_resolver,
        )
        assert "Unknown team added Unknown player (free agent)." == bullets[0]

    def test_resolver_returns_none_uses_fallback(self):
        row = _row(event_type="TRADE", payload={
            "from_franchise_id": "F01",
            "to_franchise_id": "F02",
            "player_id": "P1",
        })
        bullets = render_deterministic_bullets_v1(
            [row],
            team_resolver=lambda _: None,
            player_resolver=lambda _: None,
        )
        assert "Unknown team acquired Unknown player from Unknown team." == bullets[0]


# ── _money edge cases ────────────────────────────────────────────────

class TestMoney:
    def test_integer(self):
        assert _money(42) == "$42"

    def test_string_integer(self):
        assert _money("100") == "$100"

    def test_zero(self):
        assert _money(0) == "$0"

    def test_none(self):
        assert _money(None) == ""

    def test_empty_string(self):
        assert _money("") == ""

    def test_non_numeric(self):
        assert _money("abc") == "abc"


# ── _safe edge cases ─────────────────────────────────────────────────

class TestSafe:
    def test_none_returns_fallback(self):
        assert _safe(None, "fb") == "fb"

    def test_empty_string_returns_fallback(self):
        assert _safe("", "fb") == "fb"

    def test_whitespace_only_returns_fallback(self):
        assert _safe("   ", "fb") == "fb"

    def test_valid_string_stripped(self):
        assert _safe("  hello  ", "fb") == "hello"

    def test_integer_converted(self):
        assert _safe(42, "fb") == "42"


# ── Unicode normalization ────────────────────────────────────────────

class TestAsciiPunct:
    def test_curly_apostrophe(self):
        assert _ascii_punct("it\u2019s") == "it's"

    def test_en_dash(self):
        assert _ascii_punct("10\u201320") == "10-20"

    def test_em_dash(self):
        assert _ascii_punct("hello\u2014world") == "hello-world"

    def test_plain_ascii_unchanged(self):
        assert _ascii_punct("hello world") == "hello world"


# ── MAX_BULLETS truncation ───────────────────────────────────────────

class TestMaxBullets:
    def test_truncation_at_max(self):
        rows = [
            _row(
                canonical_id=f"c{i:04d}",
                occurred_at=f"2024-10-{(i % 28) + 1:02d}",
                event_type="MATCHUP_RESULT",
                payload={
                    "winner_franchise_id": f"W{i}",
                    "loser_franchise_id": f"L{i}",
                },
            )
            for i in range(30)
        ]
        bullets = render_deterministic_bullets_v1(rows)
        assert len(bullets) == MAX_BULLETS


# ── None payload ─────────────────────────────────────────────────────

class TestNonePayload:
    def test_none_payload_matchup(self):
        row = _row(event_type="MATCHUP_RESULT", payload=None)
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Unknown team beat Unknown team."]
