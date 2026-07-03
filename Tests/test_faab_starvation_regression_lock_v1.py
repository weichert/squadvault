"""Unit F2 — FAAB starvation regression lock (tests-only).

Adjudication (founder, 2026-07-02; D-X disposition 4, premise-corrected):
Option 1 — tests-only regression lock. The brief's premise (that zero-WBA
seasons still receive FAAB angles / writer-room FAAB context) is FALSIFIED at
HEAD and was already contradicted by the Stage A memo
(OBSERVATIONS_2026_07_02_FAAB_CLAIM_ATTRIBUTION_STAGE_A.md line 116 — the
"FAAB reaches prompt? NO" row — and line 134 — the H1 classification
"no FAAB writer-room/angle possible ... Data absent -> invention"). H1 is
UNPROMPTED invention, mitigated in practice by the Unit F1 verifier fix.

This unit makes ZERO source changes. It locks the already-correct behavior so
a future detector/derivation change cannot silently reintroduce a FAAB-context
leak into a zero-WBA prompt. All tests are green at HEAD (the lock); if any is
not green, the adjudication itself is falsified and the session halts.

Test map (adapted from brief section 3; Test 2 byte-identical DROPPED as moot
with no source change):
  Test 1 — zero-WBA assembly output carries no FAAB angle and no writer-room
           FAAB content line (the known template header token is exempted).
  Test 3 — free-agent bullets are preserved (amount-less transaction facts are
           never gated by FAAB context handling).
  Test 4 — data-keyed, not season-keyed: adding a single WBA row to an
           otherwise identical fixture makes FAAB context appear.
  Test 5 — boundary: exactly one WBA event is treated as non-zero.

The residual template-header token
"=== WRITER ROOM (scoring deltas, FAAB spending) ===" (creative_layer_v1.py:322)
is a prompt-template element, explicitly OUT OF SCOPE for this unit (brief
section 7) and left for a separate DECIDE ruling. Test 1 exempts exactly that
line, per this adjudication.
"""
from __future__ import annotations

import json
import os
import sqlite3

from squadvault.ai.creative_layer_v1 import _build_user_prompt
from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    CanonicalEventRow,
    render_deterministic_bullets_v1,
)
from squadvault.recaps.weekly_recap_lifecycle import _derive_prompt_context

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
LEAGUE = "70985"
# A season number is used only for row scoping; suppression is keyed to the
# WBA COUNT, never to this number (Test 4 proves it by toggling a WBA row on
# for this same season).
SEASON = 2019
WEEK = 5

# EXEMPTED residual: the prompt-template section header label added by
# creative_layer_v1._build_user_prompt (:322). It names "FAAB spending" whenever
# the WRITER ROOM block is present (i.e. whenever scoring deltas exist), even
# with no FAAB data. Per the F2 adjudication (2026-07-02) this template token is
# out of scope for this tests-only unit and is left for a separate DECIDE ruling.
_TEMPLATE_HEADER_RESIDUAL = "=== WRITER ROOM (scoring deltas, FAAB spending) ==="


def _fresh_db(tmp_path, name="f2.sqlite"):
    db_path = str(tmp_path / name)
    con = sqlite3.connect(db_path)
    con.executescript(open(SCHEMA_PATH, encoding="utf-8").read())
    con.close()
    return db_path


def _canon(con, event_type, payload, occurred_at, cid):
    con.execute(
        """INSERT INTO memory_events (league_id, season, external_source, external_id,
           event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, 'test', ?, ?, ?, ?, ?)""",
        (LEAGUE, SEASON, cid, event_type, occurred_at, occurred_at,
         json.dumps(payload, sort_keys=True)),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events (league_id, season, event_type,
           action_fingerprint, best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, 100, ?, ?)""",
        (LEAGUE, SEASON, event_type, f"fp_{cid}", me_id, occurred_at, occurred_at),
    )


def _build_fixture(tmp_path, *, wba_count):
    """A minimal but assembly-complete fixture for (SEASON, WEEK).

    Two franchises, week-4 and week-5 matchups (so scoring deltas compute and
    the WRITER ROOM block — hence the exempted header — is present), a scored
    player, and `wba_count` WAIVER_BID_AWARDED events. `wba_count` is the only
    variable across tests: FAAB context must be a pure function of it.
    """
    db_path = _fresh_db(tmp_path, name=f"f2_wba{wba_count}.sqlite")
    con = sqlite3.connect(db_path)
    for fid, name in (("0001", "Alpha Squad"), ("0002", "Beta Team")):
        con.execute(
            "INSERT OR REPLACE INTO franchise_directory "
            "(league_id, season, franchise_id, name, updated_at) "
            "VALUES (?, ?, ?, ?, '2019-01-01T00:00:00Z')",
            (LEAGUE, SEASON, fid, name),
        )
    con.execute(
        "INSERT OR REPLACE INTO player_directory "
        "(league_id, season, player_id, name, position) VALUES (?, ?, ?, ?, ?)",
        (LEAGUE, SEASON, "P1", "Smith, Joe", "RB"),
    )
    for w, (sa, sb) in ((4, (100.0, 80.0)), (5, (120.0, 90.0))):
        _canon(con, "WEEKLY_MATCHUP_RESULT", {
            "week": w, "winner_franchise_id": "0001", "loser_franchise_id": "0002",
            "winner_score": f"{sa:.2f}", "loser_score": f"{sb:.2f}", "is_tie": False,
        }, f"2019-10-{w:02d}T12:00:00Z", f"m{w}")
        _canon(con, "WEEKLY_PLAYER_SCORE", {
            "week": w, "franchise_id": "0001", "player_id": "P1",
            "score": 20.0, "is_starter": True, "should_start": True,
        }, f"2019-10-{w:02d}T12:00:00Z", f"ps{w}")
    for i in range(wba_count):
        _canon(con, "WAIVER_BID_AWARDED", {
            "franchise_id": "0001", "player_id": "P1", "bid_amount": 15.0 + i,
        }, f"2019-09-2{5 + i}T01:00:00Z", f"wba{i}")
    con.commit()
    con.close()
    return db_path


def _assemble_prompt(db_path):
    """Assemble the full user-turn prompt (context derivation + template)."""
    ctx = _derive_prompt_context(
        db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=WEEK,
        window_end=None,
    )
    return _build_user_prompt(
        facts_bullets=["Alpha Squad beat Beta Team 120.00 to 90.00."],
        eal_directive="STANDARD", league_id=LEAGUE, season=SEASON, week_index=WEEK,
        season_context=ctx.season_context_text, league_history=ctx.league_history_text,
        narrative_angles=ctx.narrative_angles_text, writer_room_context=ctx.writer_room_text,
        player_highlights=ctx.player_highlights_text, manager_identity=ctx.manager_identity_text,
    )


def _faab_lines(prompt):
    return [ln.strip() for ln in prompt.splitlines() if "faab" in ln.lower()]


class TestFaabStarvationRegressionLock:
    """Unit F2 — locks the already-correct zero-WBA suppression behavior."""

    def test_1_zero_wba_suppresses_faab_context(self, tmp_path):
        """Test 1 (invariant lock): a zero-WBA season's assembled prompt carries
        no FAAB angle and no writer-room FAAB content line. The only line
        containing 'faab' is the exempted out-of-scope template header."""
        prompt = _assemble_prompt(_build_fixture(tmp_path, wba_count=0))
        faab = _faab_lines(prompt)
        # The template header (creative_layer_v1.py:322) is the sole permitted
        # residual per the F2 adjudication; any other FAAB line is a leak.
        assert faab == [_TEMPLATE_HEADER_RESIDUAL], (
            f"zero-WBA prompt must contain no FAAB content beyond the exempted "
            f"template header; got: {faab}"
        )

    def test_3_free_agent_bullets_preserved(self, tmp_path):
        """Test 3 (free-agent preservation): TRANSACTION_FREE_AGENT adds are real,
        amount-less canonical facts and must still surface. FAAB-context handling
        must never gate transaction facts."""
        rows = [CanonicalEventRow(
            canonical_id="fa1", event_type="TRANSACTION_FREE_AGENT",
            occurred_at="2019-10-05T12:00:00Z",
            payload={"franchise_id": "0001", "player_id": "P9"},
        )]
        bullets = render_deterministic_bullets_v1(
            rows,
            team_resolver=lambda x: "Alpha Squad",
            player_resolver=lambda x: "Free Agent Guy",
        )
        assert bullets == ["Alpha Squad added Free Agent Guy (free agent)."], bullets
        assert not any("$" in b for b in bullets), (
            f"free-agent bullets carry no dollar amount by design; got: {bullets}"
        )

    def test_4_data_keyed_not_season_keyed(self, tmp_path):
        """Test 4 (data-keyed proof): the same season/fixture yields no FAAB
        context with zero WBA rows and FAAB context with one. Emptiness is a
        function of the canonical WBA count, not the season number — a hardcoded
        season list could not produce this toggle."""
        zero = _faab_lines(_assemble_prompt(_build_fixture(tmp_path, wba_count=0)))
        one = _faab_lines(_assemble_prompt(_build_fixture(tmp_path, wba_count=1)))
        assert zero == [_TEMPLATE_HEADER_RESIDUAL], zero
        assert any("faab spending through this week" in ln.lower() for ln in one), (
            f"a single WBA row must surface writer-room FAAB context; got: {one}"
        )
        assert len(one) > len(zero)

    def test_5_boundary_one_wba_is_non_zero(self, tmp_path):
        """Test 5 (boundary): exactly one WBA event is treated as non-zero — full
        FAAB context (the writer-room FAAB spending line) is present."""
        one = _faab_lines(_assemble_prompt(_build_fixture(tmp_path, wba_count=1)))
        assert any("faab spending through this week" in ln.lower() for ln in one), (
            f"exactly one WBA is non-zero and must surface FAAB context; got: {one}"
        )
