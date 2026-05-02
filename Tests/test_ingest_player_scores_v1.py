"""Tests for squadvault.ingest.player_scores.

Covers: _stable_external_id, _safe_float, _ensure_list,
derive_player_score_envelopes (consuming weeklyResults JSON).
"""
from __future__ import annotations

from squadvault.ingest.player_scores import (
    _ensure_list,
    _safe_float,
    _stable_external_id,
    derive_player_score_envelopes,
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
        assert _safe_float("40.20") == 40.20

    def test_valid_int(self):
        assert _safe_float("100") == 100.0

    def test_none(self):
        assert _safe_float(None) is None

    def test_invalid(self):
        assert _safe_float("abc") is None

    def test_empty_string(self):
        assert _safe_float("") is None

    def test_zero(self):
        assert _safe_float("0") == 0.0

    def test_negative(self):
        assert _safe_float("-2.50") == -2.50


# ── _ensure_list ─────────────────────────────────────────────────────

class TestEnsureList:
    def test_list_passthrough(self):
        assert _ensure_list([1, 2]) == [1, 2]

    def test_single_dict_wrapped(self):
        assert _ensure_list({"id": "0001"}) == [{"id": "0001"}]

    def test_none_returns_empty(self):
        assert _ensure_list(None) == []


# ── Test helpers ─────────────────────────────────────────────────────

def _make_player(player_id, score, status="starter", should_start="0"):
    """Helper to build a single player entry."""
    return {
        "id": player_id,
        "score": str(score),
        "status": status,
        "shouldStart": should_start,
    }


def _make_franchise(franchise_id, players, score="100.00"):
    """Helper to build a franchise within a matchup."""
    return {
        "id": franchise_id,
        "score": score,
        "result": "W",
        "player": players,
        "starters": ",".join(
            p["id"] for p in (players if isinstance(players, list) else [players])
            if p.get("status") == "starter"
        ),
    }


def _make_weekly_results(matchups):
    """Helper to build a weeklyResults JSON structure."""
    return {
        "weeklyResults": {
            "week": "6",
            "matchup": matchups,
        }
    }


def _make_matchup(franchises):
    """Helper to build a matchup with multiple franchises."""
    return {"franchise": franchises}


COMMON_KWARGS = dict(
    year=2024,
    week=6,
    league_id="70985",
    source_url="https://test.com",
)


# ── derive_player_score_envelopes ────────────────────────────────────

class TestDerivePlayerScoreEnvelopes:
    def test_basic_starter(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [
                    _make_player("15648", "40.20", "starter"),
                ]),
                _make_franchise("0002", [
                    _make_player("99999", "22.50", "starter"),
                ]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert len(events) == 2
        e = [e for e in events if e["payload"]["player_id"] == "15648"][0]
        assert e["event_type"] == "WEEKLY_PLAYER_SCORE"
        assert e["league_id"] == "70985"
        assert e["season"] == 2024
        assert e["external_source"] == "MFL"
        p = e["payload"]
        assert p["week"] == 6
        assert p["franchise_id"] == "0001"
        assert p["player_id"] == "15648"
        assert p["score"] == 40.20
        assert p["is_starter"] is True

    def test_nonstarter_included(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [
                    _make_player("15648", "40.20", "starter"),
                    _make_player("12345", "15.00", "nonstarter"),
                ]),
                _make_franchise("0002", [
                    _make_player("99999", "22.50", "starter"),
                ]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert len(events) == 3
        bench = [e for e in events if e["payload"]["player_id"] == "12345"][0]
        assert bench["payload"]["is_starter"] is False

    def test_should_start_parsed(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [
                    _make_player("15648", "10.00", "starter", "0"),
                    _make_player("12345", "25.00", "nonstarter", "1"),
                ]),
                _make_franchise("0002", [
                    _make_player("99999", "22.50", "starter"),
                ]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        starter = [e for e in events if e["payload"]["player_id"] == "15648"][0]
        bench = [e for e in events if e["payload"]["player_id"] == "12345"][0]
        assert starter["payload"]["should_start"] is False
        assert bench["payload"]["should_start"] is True

    def test_multiple_matchups(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "40.20")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
            _make_matchup([
                _make_franchise("0003", [_make_player("11111", "30.00")]),
                _make_franchise("0004", [_make_player("22222", "18.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert len(events) == 4
        franchise_ids = {e["payload"]["franchise_id"] for e in events}
        assert franchise_ids == {"0001", "0002", "0003", "0004"}

    def test_player_without_score_skipped(self):
        """Players with no score attribute are silently skipped."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [
                    _make_player("15648", "40.20"),
                    {"id": "99999", "status": "starter"},  # no score
                ]),
                _make_franchise("0002", [_make_player("11111", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        player_ids = {e["payload"]["player_id"] for e in events}
        assert "15648" in player_ids
        assert "11111" in player_ids
        assert "99999" not in player_ids

    def test_external_id_deterministic(self):
        """Same input produces same external_id."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "40.20")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        e1 = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        e2 = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert e1[0]["external_id"] == e2[0]["external_id"]

    def test_different_weeks_different_external_ids(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "40.20")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        e1 = derive_player_score_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        e2 = derive_player_score_envelopes(
            year=2024, week=7, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
        )
        assert e1[0]["external_id"] != e2[0]["external_id"]

    def test_different_franchises_different_external_ids(self):
        """Same player on different franchises gets different external_ids."""
        data1 = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "40.20")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        data2 = _make_weekly_results([
            _make_matchup([
                _make_franchise("0003", [_make_player("15648", "40.20")]),
                _make_franchise("0004", [_make_player("99999", "22.50")]),
            ]),
        ])
        e1 = derive_player_score_envelopes(
            weekly_results_json=data1, **COMMON_KWARGS,
        )
        e2 = derive_player_score_envelopes(
            weekly_results_json=data2, **COMMON_KWARGS,
        )
        ids_1 = {e["external_id"] for e in e1}
        ids_2 = {e["external_id"] for e in e2}
        assert ids_1.isdisjoint(ids_2)

    def test_empty_matchups_returns_empty(self):
        data = _make_weekly_results([])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert events == []

    def test_missing_weekly_results_key(self):
        events = derive_player_score_envelopes(
            weekly_results_json={}, **COMMON_KWARGS,
        )
        assert events == []

    def test_occurred_at_propagated(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "40.20")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            year=2024, week=6, league_id="70985",
            weekly_results_json=data, source_url="https://test.com",
            occurred_at="2024-10-15T12:00:00Z",
        )
        assert events[0]["occurred_at"] == "2024-10-15T12:00:00Z"

    def test_occurred_at_none_by_default(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "40.20")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert events[0]["occurred_at"] is None

    def test_zero_score_player_included(self):
        """Players with 0.0 score should be included (bye week fill-in, etc.)."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "0.00")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        p = [e for e in events if e["payload"]["player_id"] == "15648"][0]
        assert p["payload"]["score"] == 0.0

    def test_negative_score_player_included(self):
        """Players with negative scores should be included."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [_make_player("15648", "-2.50")]),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        p = [e for e in events if e["payload"]["player_id"] == "15648"][0]
        assert p["payload"]["score"] == -2.50

    def test_output_sorted_deterministically(self):
        """Events should be sorted by franchise_id then player_id for determinism."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0002", [
                    _make_player("99999", "10.00"),
                ]),
                _make_franchise("0001", [
                    _make_player("55555", "15.00"),
                    _make_player("11111", "20.00"),
                ]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        # Should be sorted: franchise 0001 first (players 11111, 55555), then 0002 (99999)
        assert len(events) == 3
        assert events[0]["payload"]["franchise_id"] == "0001"
        assert events[0]["payload"]["player_id"] == "11111"
        assert events[1]["payload"]["franchise_id"] == "0001"
        assert events[1]["payload"]["player_id"] == "55555"
        assert events[2]["payload"]["franchise_id"] == "0002"
        assert events[2]["payload"]["player_id"] == "99999"

    def test_all_external_ids_unique(self):
        """Every event in a multi-player multi-franchise week gets a unique external_id."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", [
                    _make_player("15648", "40.20"),
                    _make_player("12345", "12.50", "nonstarter"),
                ]),
                _make_franchise("0002", [
                    _make_player("99999", "22.50"),
                ]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        ext_ids = {e["external_id"] for e in events}
        assert len(ext_ids) == 3

    def test_single_matchup_not_wrapped_in_list(self):
        """MFL may return a single matchup as a dict instead of a list."""
        data = {
            "weeklyResults": {
                "week": "6",
                "matchup": _make_matchup([
                    _make_franchise("0001", [_make_player("15648", "40.20")]),
                    _make_franchise("0002", [_make_player("99999", "22.50")]),
                ]),
            }
        }
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert len(events) == 2

    def test_single_franchise_player_not_in_list(self):
        """MFL may return a single player as a dict instead of a list."""
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", _make_player("15648", "40.20")),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        player_ids = {e["payload"]["player_id"] for e in events}
        assert "15648" in player_ids

    def test_missing_franchise_id_skipped(self):
        data = _make_weekly_results([
            _make_matchup([
                {"player": [_make_player("15648", "40.20")]},
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        franchise_ids = {e["payload"]["franchise_id"] for e in events}
        assert franchise_ids == {"0002"}

    def test_franchise_with_no_players_skipped(self):
        data = _make_weekly_results([
            _make_matchup([
                _make_franchise("0001", []),
                _make_franchise("0002", [_make_player("99999", "22.50")]),
            ]),
        ])
        events = derive_player_score_envelopes(
            weekly_results_json=data, **COMMON_KWARGS,
        )
        assert len(events) == 1
        assert events[0]["payload"]["franchise_id"] == "0002"


# ── Canonicalization fingerprint integration ────────────────────────

class TestPlayerScoreCanonicalFingerprint:
    """Verify WEEKLY_PLAYER_SCORE events get proper fingerprints."""

    def test_fingerprint_format(self):
        import json

        from squadvault.core.canonicalize.run_canonicalize import (
            MemoryEventRow,
            action_fingerprint,
        )

        payload_dict = {
            "week": 6,
            "franchise_id": "0001",
            "player_id": "15648",
            "score": 40.20,
            "is_starter": True,
            "should_start": False,
        }
        row = MemoryEventRow(
            id=1,
            league_id="70985",
            season=2024,
            event_type="WEEKLY_PLAYER_SCORE",
            occurred_at=None,
            ingested_at="2024-01-01T00:00:00Z",
            payload_json=json.dumps(payload_dict),
        )
        fp = action_fingerprint(row, payload_dict)
        assert fp == "WEEKLY_PLAYER_SCORE:70985:2024:W6:0001:15648"

    def test_fingerprint_deterministic(self):
        import json

        from squadvault.core.canonicalize.run_canonicalize import (
            MemoryEventRow,
            action_fingerprint,
        )

        payload_dict = {
            "week": 6,
            "franchise_id": "0001",
            "player_id": "15648",
            "score": 40.20,
        }
        row = MemoryEventRow(
            id=1,
            league_id="70985",
            season=2024,
            event_type="WEEKLY_PLAYER_SCORE",
            occurred_at=None,
            ingested_at="2024-01-01T00:00:00Z",
            payload_json=json.dumps(payload_dict),
        )
        fp1 = action_fingerprint(row, payload_dict)
        fp2 = action_fingerprint(row, payload_dict)
        assert fp1 == fp2

    def test_different_players_different_fingerprints(self):
        import json

        from squadvault.core.canonicalize.run_canonicalize import (
            MemoryEventRow,
            action_fingerprint,
        )

        def _make_row(player_id):
            payload = {"week": 6, "franchise_id": "0001", "player_id": player_id, "score": 40.20}
            return MemoryEventRow(
                id=1, league_id="70985", season=2024,
                event_type="WEEKLY_PLAYER_SCORE",
                occurred_at=None, ingested_at="2024-01-01T00:00:00Z",
                payload_json=json.dumps(payload),
            ), payload

        row1, p1 = _make_row("15648")
        row2, p2 = _make_row("99999")
        assert action_fingerprint(row1, p1) != action_fingerprint(row2, p2)

    def test_different_franchises_different_fingerprints(self):
        import json

        from squadvault.core.canonicalize.run_canonicalize import (
            MemoryEventRow,
            action_fingerprint,
        )

        def _make_row(franchise_id):
            payload = {"week": 6, "franchise_id": franchise_id, "player_id": "15648", "score": 40.20}
            return MemoryEventRow(
                id=1, league_id="70985", season=2024,
                event_type="WEEKLY_PLAYER_SCORE",
                occurred_at=None, ingested_at="2024-01-01T00:00:00Z",
                payload_json=json.dumps(payload),
            ), payload

        row1, p1 = _make_row("0001")
        row2, p2 = _make_row("0002")
        assert action_fingerprint(row1, p1) != action_fingerprint(row2, p2)
