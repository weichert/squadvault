"""Tests for squadvault.core.recaps.render.deterministic_bullets_v1

Covers: every event type bullet format, deterministic ordering,
skip/silence rules, resolver callbacks, _money edge cases,
unicode normalization, MAX_BULLETS truncation, empty input.
"""
from __future__ import annotations

from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    MAX_BULLETS,
    CanonicalEventRow,
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

    def test_trade_missing_fields_produces_silence(self):
        # Empty payload means no participants identifiable — silence preferred.
        row = _row(event_type="TRADE", payload={})
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == [], "Empty payload should produce silence"


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
        # Score format updated from "120-95" (hyphen-separated, ambiguous
        # decimal vs. score separator) to "120.00 to 95.00" (unambiguous
        # "to" format from score_strings_v1.format_matchup_score_str).
        # See _observations/OBSERVATIONS_2026_05_03_SCORE_RENDERING_PRE_FIX_DIAGNOSTIC.md.
        assert bullets == ["F10 beat F11 120.00 to 95.00."]

    def test_matchup_alternate_type(self):
        row = _row(event_type="WEEKLY_MATCHUP_RESULT", payload={
            "winner_team_id": "Champs",
            "loser_team_id": "Underdogs",
            "winner_score": 110,
            "loser_score": 105,
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Champs beat Underdogs 110.00 to 105.00."]

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

    def test_unknown_non_transaction_type_empty_payload_silent(self):
        # Empty payload — silence preferred even for unknown event types.
        row = _row(event_type="LEAGUE_EXPANSION", payload={})
        assert render_deterministic_bullets_v1([row]) == []

    def test_unknown_non_transaction_type_with_payload_gets_generic_bullet(self):
        # Non-empty payload — generic bullet still produced.
        row = _row(event_type="LEAGUE_EXPANSION", payload={"detail": "added team"})
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
    def test_none_payload_produces_silence(self):
        # None payload becomes empty dict, which produces silence.
        row = _row(event_type="MATCHUP_RESULT", payload=None)
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == [], "Empty payload should produce silence, not a fabricated bullet"

    def test_empty_dict_payload_produces_silence(self):
        # Explicit empty dict payload produces silence.
        row = _row(event_type="TRANSACTION_FREE_AGENT", payload={})
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == [], "Empty payload should produce silence, not '? added <?>'"

    def test_empty_payload_skipped_among_valid_events(self):
        # Empty payload events are skipped; valid events still render.
        rows = [
            _row(canonical_id="empty", event_type="TRANSACTION_FREE_AGENT", payload={}),
            _row(canonical_id="valid", event_type="TRANSACTION_FREE_AGENT", payload={
                "franchise_id": "F01", "player_id": "P100",
            }),
        ]
        bullets = render_deterministic_bullets_v1(rows)
        assert len(bullets) == 1
        assert "F01 added P100 (free agent)." == bullets[0]


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


# ── Canonical trade-fields path (post-S10 leak #2/#4) ────────────────

class TestTradeCanonicalPath:
    """Verifies the canonical-first trade rendering path introduced by
    S10 leak #4 resolution. Post-promotion trade events carry
    ``trade_franchise_a_gave_up`` / ``trade_franchise_b_gave_up`` on
    the canonical envelope; the renderer must consume these directly
    without reaching into ``raw_mfl_json``.
    """

    def test_canonical_path_renders_bullet_with_resolvers(self):
        # Canonical fields only; no raw_mfl_json.
        team_res = lambda fid: {"0004": "Eagles", "0010": "Hawks"}.get(fid, fid)
        player_res = lambda pid: {
            "15754": "Chris Olave", "16214": "Sam LaPorta",
        }.get(pid, pid)
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "mfl_type": "TRADE",
            "franchise_id": "0004",
            "franchise_ids_involved": ["0004", "0010"],
            "player_id": None,
            "trade_franchise_a_gave_up": ["15754"],
            "trade_franchise_b_gave_up": ["16214"],
        })
        bullets = render_deterministic_bullets_v1(
            [row], team_resolver=team_res, player_resolver=player_res,
        )
        assert bullets == ["Eagles traded Chris Olave to Hawks for Sam LaPorta."]

    def test_canonical_priority_over_raw_mfl_json(self):
        # Both canonical and raw_mfl_json present, with distinct IDs so
        # a raw-parse result would produce a visibly different bullet.
        # Canonical must win.
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "mfl_type": "TRADE",
            "franchise_id": "0004",
            "franchise_ids_involved": ["0004", "0010"],
            "trade_franchise_a_gave_up": ["CANON_A"],
            "trade_franchise_b_gave_up": ["CANON_B"],
            "raw_mfl_json": (
                '{"franchise":"0004","franchise2":"0010",'
                '"franchise1_gave_up":"RAW_A,","franchise2_gave_up":"RAW_B,",'
                '"type":"TRADE"}'
            ),
        })
        bullets = render_deterministic_bullets_v1([row])
        assert len(bullets) == 1
        assert "CANON_A" in bullets[0]
        assert "CANON_B" in bullets[0]
        assert "RAW_A" not in bullets[0]
        assert "RAW_B" not in bullets[0]

    def test_canonical_one_side_empty_produces_completed_trade(self):
        # Post-promotion event with one side's gave-up list empty.
        # Matches existing raw_mfl_json fallback behavior: emit
        # "completed a trade" rather than a partial sentence.
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "mfl_type": "TRADE",
            "franchise_id": "0004",
            "franchise_ids_involved": ["0004", "0010"],
            "trade_franchise_a_gave_up": ["15754"],
            "trade_franchise_b_gave_up": [],
        })
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["0004 and 0010 completed a trade."]

    def test_canonical_missing_franchise_b_falls_back_to_raw(self):
        # Canonical key is present (post-promotion signal) but
        # franchise_ids_involved contains only A, so B cannot be
        # derived. Renderer falls back to raw_mfl_json parsing.
        row = _row(event_type="TRANSACTION_TRADE", payload={
            "mfl_type": "TRADE",
            "franchise_id": "0004",
            "franchise_ids_involved": ["0004"],  # no B
            "trade_franchise_a_gave_up": ["15754"],
            "trade_franchise_b_gave_up": ["16214"],
            "raw_mfl_json": (
                '{"franchise":"0004","franchise2":"0010",'
                '"franchise1_gave_up":"15754,","franchise2_gave_up":"16214,",'
                '"type":"TRADE"}'
            ),
        })
        bullets = render_deterministic_bullets_v1([row])
        assert len(bullets) == 1
        assert "0004" in bullets[0]
        assert "0010" in bullets[0]
        assert "15754" in bullets[0]
        assert "16214" in bullets[0]
