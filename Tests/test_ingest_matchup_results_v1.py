"""Tests for squadvault.ingest.matchup_results.

Covers: _stable_external_id, _safe_float, _ensure_list,
derive_matchup_result_envelopes.
"""
from __future__ import annotations

from squadvault.ingest.matchup_results import (
    _ensure_list,
    _safe_float,
    _stable_external_id,
    derive_matchup_result_envelopes,
)

# ── _stable_external_id ─────────────────────────────────────────────

class TestStableExternalId:
    def test_deterministic(self):
        assert _stable_external_id("a", "b") == _stable_external_id("a", "b")

    def test_different_inputs_differ(self):
        assert _stable_external_id("a", "b") != _stable_external_id("a", "c")

    def test_length(self):
        assert len(_stable_external_id("x")) == 24

    def test_none_parts_handled(self):
        result = _stable_external_id("a", None, "b")
        assert len(result) == 24


# ── _safe_float ──────────────────────────────────────────────────────

class TestSafeFloat:
    def test_valid_float(self):
        assert _safe_float("142.60") == 142.60

    def test_valid_int(self):
        assert _safe_float("100") == 100.0

    def test_none(self):
        assert _safe_float(None) is None

    def test_invalid(self):
        assert _safe_float("abc") is None

    def test_empty_string(self):
        assert _safe_float("") is None


# ── _ensure_list ─────────────────────────────────────────────────────

class TestEnsureList:
    def test_list_passthrough(self):
        assert _ensure_list([1, 2]) == [1, 2]

    def test_single_dict_wrapped(self):
        assert _ensure_list({"id": "0001"}) == [{"id": "0001"}]

    def test_none_returns_empty(self):
        assert _ensure_list(None) == []


# ── derive_matchup_result_envelopes ──────────────────────────────────

def _make_weekly_results(matchups):
    """Helper to build a weeklyResults JSON structure."""
    return {
        "weeklyResults": {
            "week": "6",
            "matchup": matchups,
        }
    }


def _make_matchup(f1_id, f1_score, f1_result, f2_id, f2_score, f2_result):
    """Helper to build a single matchup."""
    return {
        "franchise": [
            {"id": f1_id, "score": str(f1_score), "result": f1_result},
            {"id": f2_id, "score": str(f2_score), "result": f2_result},
        ]
    }


class TestDeriveMatchupResultEnvelopes:
    def test_basic_win_loss(self):
        data = _make_weekly_results([
            _make_matchup("0001", 142.60, "W", "0002", 98.30, "L"),
        ])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert len(events) == 1
        e = events[0]
        assert e["event_type"] == "WEEKLY_MATCHUP_RESULT"
        assert e["league_id"] == "70985"
        assert e["season"] == 2024
        assert e["external_source"] == "MFL"
        p = e["payload"]
        assert p["winner_franchise_id"] == "0001"
        assert p["loser_franchise_id"] == "0002"
        assert p["winner_score"] == "142.60"
        assert p["loser_score"] == "98.30"
        assert p["is_tie"] is False
        assert p["week"] == 6

    def test_reversed_win_loss(self):
        """Second franchise is the winner."""
        data = _make_weekly_results([
            _make_matchup("0001", 98.30, "L", "0002", 142.60, "W"),
        ])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert len(events) == 1
        p = events[0]["payload"]
        assert p["winner_franchise_id"] == "0002"
        assert p["loser_franchise_id"] == "0001"

    def test_tie(self):
        data = _make_weekly_results([
            _make_matchup("0003", 100.00, "T", "0001", 100.00, "T"),
        ])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert len(events) == 1
        p = events[0]["payload"]
        assert p["is_tie"] is True
        # Lower franchise ID first (deterministic)
        assert p["winner_franchise_id"] == "0001"
        assert p["loser_franchise_id"] == "0003"

    def test_multiple_matchups(self):
        data = _make_weekly_results([
            _make_matchup("0001", 142.60, "W", "0002", 98.30, "L"),
            _make_matchup("0003", 110.00, "W", "0004", 105.50, "L"),
            _make_matchup("0005", 88.20, "L", "0006", 130.10, "W"),
        ])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert len(events) == 3
        # Verify all are distinct
        ext_ids = {e["external_id"] for e in events}
        assert len(ext_ids) == 3

    def test_external_id_deterministic(self):
        """Same input produces same external_id."""
        data = _make_weekly_results([
            _make_matchup("0001", 142.60, "W", "0002", 98.30, "L"),
        ])
        e1 = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        e2 = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert e1[0]["external_id"] == e2[0]["external_id"]

    def test_external_id_order_independent(self):
        """Franchise order in the matchup doesn't affect external_id."""
        data1 = _make_weekly_results([
            _make_matchup("0001", 142.60, "W", "0002", 98.30, "L"),
        ])
        data2 = _make_weekly_results([
            _make_matchup("0002", 98.30, "L", "0001", 142.60, "W"),
        ])
        e1 = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data1, source_url="https://test.com",
        )
        e2 = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data2, source_url="https://test.com",
        )
        assert e1[0]["external_id"] == e2[0]["external_id"]

    def test_empty_matchups(self):
        data = _make_weekly_results([])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert events == []

    def test_missing_weekly_results_key(self):
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json={}, source_url="https://test.com",
        )
        assert events == []

    def test_single_matchup_not_wrapped_in_list(self):
        """MFL may return a single matchup as a dict instead of a list."""
        data = {
            "weeklyResults": {
                "week": "6",
                "matchup": _make_matchup("0001", 142.60, "W", "0002", 98.30, "L"),
            }
        }
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert len(events) == 1

    def test_missing_score_skipped(self):
        data = _make_weekly_results([{
            "franchise": [
                {"id": "0001", "result": "W"},
                {"id": "0002", "result": "L"},
            ]
        }])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert events == []

    def test_missing_franchise_id_skipped(self):
        data = _make_weekly_results([{
            "franchise": [
                {"score": "100.00", "result": "W"},
                {"id": "0002", "score": "90.00", "result": "L"},
            ]
        }])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert events == []

    def test_three_franchise_matchup_skipped(self):
        """Matchups with != 2 franchises are skipped."""
        data = _make_weekly_results([{
            "franchise": [
                {"id": "0001", "score": "100.00", "result": "W"},
                {"id": "0002", "score": "90.00", "result": "L"},
                {"id": "0003", "score": "80.00", "result": "L"},
            ]
        }])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert events == []

    def test_fallback_score_based_winner(self):
        """When result field is missing, determine winner by score."""
        data = _make_weekly_results([{
            "franchise": [
                {"id": "0001", "score": "142.60", "result": ""},
                {"id": "0002", "score": "98.30", "result": ""},
            ]
        }])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert len(events) == 1
        p = events[0]["payload"]
        assert p["winner_franchise_id"] == "0001"
        assert p["loser_franchise_id"] == "0002"
        assert p["is_tie"] is False

    def test_payload_preserves_home_away(self):
        """Home/away franchise IDs are preserved regardless of winner."""
        data = _make_weekly_results([
            _make_matchup("0005", 98.30, "L", "0003", 142.60, "W"),
        ])
        events = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        p = events[0]["payload"]
        assert p["home_franchise_id"] == "0005"
        assert p["away_franchise_id"] == "0003"
        assert p["home_score"] == "98.30"
        assert p["away_score"] == "142.60"

    def test_different_weeks_different_external_ids(self):
        data = _make_weekly_results([
            _make_matchup("0001", 100.00, "W", "0002", 90.00, "L"),
        ])
        e1 = derive_matchup_result_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        e2 = derive_matchup_result_envelopes(
            year=2024, week=7, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert e1[0]["external_id"] != e2[0]["external_id"]


# ── Canonicalization fingerprint integration ────────────────────────

class TestMatchupCanonicalFingerprint:
    """Verify WEEKLY_MATCHUP_RESULT events get proper fingerprints."""

    def test_fingerprint_format(self):
        from squadvault.core.canonicalize.run_canonicalize import (
            MemoryEventRow,
            action_fingerprint,
        )
        payload_dict = {
            "week": 6,
            "winner_franchise_id": "0001",
            "loser_franchise_id": "0002",
            "winner_score": "142.60",
            "loser_score": "98.30",
            "is_tie": False,
        }
        import json
        row = MemoryEventRow(
            id=1,
            league_id="70985",
            season=2024,
            event_type="WEEKLY_MATCHUP_RESULT",
            occurred_at=None,
            ingested_at="2024-01-01T00:00:00Z",
            payload_json=json.dumps(payload_dict),
        )
        fp = action_fingerprint(row, payload_dict)
        assert fp == "WEEKLY_MATCHUP_RESULT:70985:2024:W6:0001:0002"

    def test_fingerprint_order_independent(self):
        """Franchise order in payload doesn't affect fingerprint."""
        import json

        from squadvault.core.canonicalize.run_canonicalize import (
            MemoryEventRow,
            action_fingerprint,
        )

        payload1 = {
            "week": 6,
            "winner_franchise_id": "0002",
            "loser_franchise_id": "0001",
        }
        payload2 = {
            "week": 6,
            "winner_franchise_id": "0001",
            "loser_franchise_id": "0002",
        }
        row1 = MemoryEventRow(
            id=1, league_id="70985", season=2024,
            event_type="WEEKLY_MATCHUP_RESULT",
            occurred_at=None, ingested_at="2024-01-01T00:00:00Z",
            payload_json=json.dumps(payload1),
        )
        row2 = MemoryEventRow(
            id=2, league_id="70985", season=2024,
            event_type="WEEKLY_MATCHUP_RESULT",
            occurred_at=None, ingested_at="2024-01-01T00:00:00Z",
            payload_json=json.dumps(payload2),
        )
        assert action_fingerprint(row1, payload1) == action_fingerprint(row2, payload2)


# ── Renderer integration ────────────────────────────────────────────

class TestMatchupBulletRendering:
    """Verify the deterministic bullets renderer handles matchup events."""

    def test_win_bullet(self):
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1",
                occurred_at="2024-10-01T00:00:00Z",
                event_type="WEEKLY_MATCHUP_RESULT",
                payload={
                    "winner_franchise_id": "0001",
                    "loser_franchise_id": "0002",
                    "winner_score": "142.60",
                    "loser_score": "98.30",
                    "is_tie": False,
                },
            ),
        ]
        bullets = render_deterministic_bullets_v1(events)
        assert len(bullets) == 1
        assert "beat" in bullets[0]
        assert "142.60-98.30" in bullets[0]

    def test_tie_bullet(self):
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1",
                occurred_at="2024-10-01T00:00:00Z",
                event_type="WEEKLY_MATCHUP_RESULT",
                payload={
                    "winner_franchise_id": "0001",
                    "loser_franchise_id": "0002",
                    "winner_score": "100.00",
                    "loser_score": "100.00",
                    "is_tie": True,
                },
            ),
        ]
        bullets = render_deterministic_bullets_v1(events)
        assert len(bullets) == 1
        assert "tied" in bullets[0]
        assert "100.00-100.00" in bullets[0]

    def test_win_with_team_resolver(self):
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        resolver = lambda fid: {"0001": "The Destroyers", "0002": "Lucky Strikes"}.get(fid, fid)
        events = [
            CanonicalEventRow(
                canonical_id="c1",
                occurred_at="2024-10-01T00:00:00Z",
                event_type="WEEKLY_MATCHUP_RESULT",
                payload={
                    "winner_franchise_id": "0001",
                    "loser_franchise_id": "0002",
                    "winner_score": "142.60",
                    "loser_score": "98.30",
                    "is_tie": False,
                },
            ),
        ]
        bullets = render_deterministic_bullets_v1(events, team_resolver=resolver)
        assert "The Destroyers beat Lucky Strikes 142.60-98.30." in bullets[0]
