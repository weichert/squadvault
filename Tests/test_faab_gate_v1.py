"""Tests for the deterministic post-generation FAAB gate (faab_gate_v1).

The gate enforces the canonical per-player FAAB allowlist on a model-authored
narrative as a hard final pass (FAAB fabrication is instruction-resistant ->
enforce, don't ask). Founder picks under test:
  - hybrid behavior: strip the offending sentence(s) when clean, else block;
  - standalone backstop (no verifier import); detection mirrors verifier Cat 8.

Most coverage is on the pure core (apply_faab_gate) with hand-built allowlists,
no DB. One DB-backed test exercises load_faab_allowlist against schema.sql.
"""
from __future__ import annotations

import os
import sqlite3

from squadvault.core.recaps.render.faab_gate_v1 import (
    FaabAllowlist,
    apply_faab_gate,
    load_faab_allowlist,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "test_league"
SEASON = 2024

# Watson canonically picked up for $20.45; Allen for $21.00. Hurts/Jefferson
# are real players in the directory but were never FAAB pickups (phantoms).
_ALLOWLIST = FaabAllowlist(
    name_to_pid={
        "christian watson": "P_WATSON",
        "keenan allen": "P_ALLEN",
        "jalen hurts": "P_HURTS",
        "justin jefferson": "P_JEFFERSON",
    },
    pid_to_amounts={
        "P_WATSON": (20.45,),
        "P_ALLEN": (21.00,),
    },
)


class TestCleanNarrative:
    def test_no_faab_figures_is_clean(self) -> None:
        text = "The Playmakers demolished Steve by forty. It was a rout."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "clean"
        assert out.text == text
        assert out.violations == ()

    def test_correct_amount_within_tolerance_is_clean(self) -> None:
        # $20 matches canonical $20.45 within +/-1.0.
        text = "Christian Watson, a $20 FAAB pickup, then erupted for thirty."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "clean"
        assert out.text == text

    def test_exact_amount_is_clean(self) -> None:
        text = "Keenan Allen ($21 FAAB) was the steal of the week."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "clean"

    def test_draft_context_dollar_is_ignored(self) -> None:
        # "draft" near the dollar suppresses the FAAB check (auction context).
        text = "He spent $45 at the draft auction to land the back. A bargain."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "clean"

    def test_non_faab_dollar_is_ignored(self) -> None:
        # No FAAB keyword near the figure -> not a FAAB claim.
        text = "The trophy cost $45 to engrave. Worth every cent."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "clean"


class TestStrip:
    def test_mispair_sentence_stripped_clean(self) -> None:
        # Wrong amount for a real acquisition: $45 vs canonical $20.45.
        text = (
            "The Playmakers rolled to a forty-point win behind a balanced attack. "
            "Christian Watson, a $45 FAAB pickup, was the headliner. "
            "Their defense did the rest in the second half."
        )
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "stripped"
        assert "$45" not in out.text
        assert "Watson" not in out.text
        assert "The Playmakers rolled" in out.text
        assert "Their defense did the rest" in out.text
        assert len(out.removed_sentences) == 1

    def test_phantom_sentence_stripped_clean(self) -> None:
        # Jalen Hurts has no WAIVER_BID_AWARDED record -> phantom claim.
        text = (
            "Steve's offense exploded for the league high this week. "
            "He grabbed Jalen Hurts as a $1 FAAB flier that paid off. "
            "The win pulled him back to .500 on the season."
        )
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "stripped"
        assert "Hurts" not in out.text
        assert "$1" not in out.text
        assert "Steve's offense exploded" in out.text
        assert "back to .500" in out.text

    def test_multiple_violations_all_stripped(self) -> None:
        text = (
            "It was a wild transaction week across the league. "
            "Christian Watson came over as a $45 FAAB pickup. "
            "Justin Jefferson was a $60 waiver claim that never panned out. "
            "The standings barely budged regardless."
        )
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "stripped"
        assert "$45" not in out.text
        assert "$60" not in out.text
        assert "It was a wild transaction week" in out.text
        assert "The standings barely budged" in out.text
        assert len(out.removed_sentences) == 2


class TestBlock:
    def test_violation_is_whole_narrative_blocks(self) -> None:
        # The only substantive content is the bad FAAB claim -> block.
        text = "Christian Watson was a $45 FAAB pickup."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "blocked"
        assert out.text == ""
        assert out.violations

    def test_stripping_leaves_only_stub_blocks(self) -> None:
        # Removing the violation sentence leaves prose below the survival floor.
        text = "Wild week. Christian Watson, a $45 FAAB pickup, led all scorers."
        out = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert out.action == "blocked"
        assert out.text == ""


class TestDeterminism:
    def test_idempotent_on_clean_output(self) -> None:
        text = (
            "A balanced effort carried the day for the Playmakers. "
            "Christian Watson, a $45 FAAB pickup, was the headliner. "
            "Their defense did the rest in the second half."
        )
        first = apply_faab_gate(text, allowlist=_ALLOWLIST)
        assert first.action == "stripped"
        # Re-gating the survivor must find nothing (no residual violation).
        second = apply_faab_gate(first.text, allowlist=_ALLOWLIST)
        assert second.action == "clean"
        assert second.text == first.text


class TestLoadAllowlist:
    def _build_db(self, tmp_path) -> str:
        db_path = str(tmp_path / "gate.sqlite")
        con = sqlite3.connect(db_path)
        con.executescript(open(SCHEMA_PATH, encoding="utf-8").read())

        def _faab_bid(franchise_id, player_id, bid_amount):
            import json
            ts = "2024-10-15T12:00:00Z"
            payload = json.dumps({
                "franchise_id": franchise_id, "player_id": player_id,
                "bid_amount": bid_amount, "mfl_type": "BBID_WAIVER",
            }, sort_keys=True)
            ext = f"faab_{player_id}_{bid_amount}"
            con.execute(
                "INSERT INTO memory_events (league_id, season, external_source, "
                "external_id, event_type, occurred_at, ingested_at, payload_json) "
                "VALUES (?, ?, 'test', ?, 'WAIVER_BID_AWARDED', ?, ?, ?)",
                (LEAGUE, SEASON, ext, ts, ts, payload))
            me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            con.execute(
                "INSERT INTO canonical_events (league_id, season, event_type, "
                "action_fingerprint, best_memory_event_id, best_score, updated_at, "
                "occurred_at) VALUES (?, ?, 'WAIVER_BID_AWARDED', ?, ?, 100, ?, ?)",
                (LEAGUE, SEASON, f"fp_{ext}", me_id, ts, ts))

        _faab_bid("F1", "P_WATSON", 20.45)
        for pid, name in (("P_WATSON", "Watson, Christian"),
                          ("P_HURTS", "Hurts, Jalen")):
            con.execute(
                "INSERT OR REPLACE INTO player_directory "
                "(league_id, season, player_id, name, position) VALUES (?, ?, ?, ?, ?)",
                (LEAGUE, SEASON, pid, name, "WR"))
        con.commit()
        con.close()
        return db_path

    def test_loads_names_and_bids(self, tmp_path) -> None:
        allow = load_faab_allowlist(self._build_db(tmp_path), LEAGUE, SEASON)
        # "Last, First" resolved to "first last" lowercase.
        assert allow.name_to_pid.get("christian watson") == "P_WATSON"
        assert allow.name_to_pid.get("jalen hurts") == "P_HURTS"
        assert allow.pid_to_amounts.get("P_WATSON") == (20.45,)
        # Hurts is a real player with no bid -> not in the amounts map.
        assert "P_HURTS" not in allow.pid_to_amounts

    def test_loaded_allowlist_drives_gate(self, tmp_path) -> None:
        allow = load_faab_allowlist(self._build_db(tmp_path), LEAGUE, SEASON)
        text = (
            "A quiet week saw few moves of consequence anywhere. "
            "Jalen Hurts arrived as a $1 FAAB flier, the lone exception. "
            "The contenders mostly stood pat ahead of the playoff push."
        )
        out = apply_faab_gate(text, allowlist=allow)
        assert out.action == "stripped"
        assert "Hurts" not in out.text
