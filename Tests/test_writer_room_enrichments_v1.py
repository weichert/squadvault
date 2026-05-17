"""Tests for Writer Room Enrichments v1.

Covers:
- Scoring deltas (week-over-week momentum/collapse)
- FAAB spending context (cumulative per franchise)
- Player position in bullets (position resolver)
- bid_amount field fix in bullet renderer
"""
from __future__ import annotations

import json
import os
import sqlite3

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)

LEAGUE = "test_league"
SEASON = 2024


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score, is_tie=False):
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": is_tie,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"m_{league_id}_{season}_{week}_{winner_id}_{loser_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_MATCHUP_RESULT",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_MATCHUP_RESULT",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


def _insert_waiver_bid(con, *, league_id, season, franchise_id, player_id,
                        bid_amount, occurred_at="2024-10-10T12:00:00Z"):
    payload = {
        "franchise_id": franchise_id,
        "player_id": player_id,
        "bid_amount": bid_amount,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"wb_{league_id}_{season}_{franchise_id}_{player_id}_{bid_amount}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WAIVER_BID_AWARDED",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WAIVER_BID_AWARDED",
         f"fp_{ext_id}", me_id, 100, occurred_at, occurred_at),
    )


# ── Scoring Deltas ───────────────────────────────────────────────────


class TestScoringDeltas:
    def test_computes_delta(self, tmp_path):
        """Delta should be this_week - last_week."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_scoring_deltas

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Week 5: A scores 82
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=5,
                        winner_id="B", loser_id="A",
                        winner_score=110, loser_score=82)
        # Week 6: A scores 145
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=6,
                        winner_id="A", loser_id="B",
                        winner_score=145, loser_score=95)
        con.commit()
        con.close()

        deltas = derive_scoring_deltas(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6
        )

        a_delta = [d for d in deltas if d.franchise_id == "A"][0]
        assert a_delta.this_week_score == 145.0
        assert a_delta.last_week_score == 82.0
        assert a_delta.delta == 63.0
        assert a_delta.has_delta

    def test_no_prior_week_delta_is_none(self, tmp_path):
        """Week 1 has no prior week — delta should be None."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_scoring_deltas

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=1,
                        winner_id="A", loser_id="B",
                        winner_score=120, loser_score=100)
        con.commit()
        con.close()

        deltas = derive_scoring_deltas(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )

        a_delta = [d for d in deltas if d.franchise_id == "A"][0]
        assert a_delta.delta is None
        assert not a_delta.has_delta

    def test_negative_delta(self, tmp_path):
        """Scoring drop should produce negative delta."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_scoring_deltas

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=3,
                        winner_id="A", loser_id="B",
                        winner_score=150, loser_score=100)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=4,
                        winner_id="B", loser_id="A",
                        winner_score=110, loser_score=85)
        con.commit()
        con.close()

        deltas = derive_scoring_deltas(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=4
        )

        a_delta = [d for d in deltas if d.franchise_id == "A"][0]
        assert a_delta.delta == -65.0  # 85 - 150

    def test_empty_returns_empty(self, tmp_path):
        """No matchup data returns empty tuple."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_scoring_deltas

        db_path = _fresh_db(tmp_path)
        deltas = derive_scoring_deltas(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1
        )
        assert deltas == ()


# ── FAAB Spending ────────────────────────────────────────────────────


class TestFaabSpending:
    def test_sums_spending(self, tmp_path):
        """Multiple bids from same franchise should sum."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_faab_spending

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="A", player_id="P1", bid_amount=25)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="A", player_id="P2", bid_amount=15)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="B", player_id="P3", bid_amount=10)
        con.commit()
        con.close()

        faab = derive_faab_spending(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            week_index=18, faab_budget=200,
        )

        a_faab = [f for f in faab if f.franchise_id == "A"][0]
        assert a_faab.total_spent == 40.0
        assert a_faab.num_acquisitions == 2
        assert a_faab.remaining == 160.0
        assert a_faab.pct_spent == 0.2

        b_faab = [f for f in faab if f.franchise_id == "B"][0]
        assert b_faab.total_spent == 10.0
        assert b_faab.num_acquisitions == 1

    def test_no_budget_means_no_remaining(self, tmp_path):
        """Without a budget, remaining and pct_spent should be None."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_faab_spending

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="A", player_id="P1", bid_amount=25)
        con.commit()
        con.close()

        faab = derive_faab_spending(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            week_index=18,
        )

        a_faab = [f for f in faab if f.franchise_id == "A"][0]
        assert a_faab.total_spent == 25.0
        assert a_faab.remaining is None
        assert a_faab.pct_spent is None

    def test_skips_zero_bids(self, tmp_path):
        """Bids with 0 amount should be skipped."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_faab_spending

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="A", player_id="P1", bid_amount=0)
        con.commit()
        con.close()

        faab = derive_faab_spending(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            week_index=18,
        )
        assert len(faab) == 0

    def test_empty_returns_empty(self, tmp_path):
        """No waiver bids returns empty tuple."""
        from squadvault.core.recaps.context.writer_room_context_v1 import derive_faab_spending

        db_path = _fresh_db(tmp_path)
        faab = derive_faab_spending(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        assert faab == ()


# ── Player Position in Bullets ───────────────────────────────────────


class TestPlayerPositionInBullets:
    def test_position_included(self):
        """When position resolver is provided, bullets include position."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="WAIVER_BID_AWARDED",
                payload={"franchise_id": "F01", "player_id": "P100", "bid_amount": 12},
            ),
        ]
        bullets = render_deterministic_bullets_v1(
            events,
            team_resolver=lambda x: "Gopher Boys" if x == "F01" else x,
            player_resolver=lambda x: "Tyler Bass" if x == "P100" else x,
            player_position_resolver=lambda x: "PK" if x == "P100" else None,
        )
        assert len(bullets) == 1
        assert "Tyler Bass (PK)" in bullets[0]
        assert "Gopher Boys" in bullets[0]

    def test_no_position_resolver_is_fine(self):
        """Without position resolver, bullets render normally."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="TRANSACTION_FREE_AGENT",
                payload={"franchise_id": "F01", "player_id": "P200"},
            ),
        ]
        bullets = render_deterministic_bullets_v1(
            events,
            player_resolver=lambda x: "Jaylen Waddle" if x == "P200" else x,
        )
        assert len(bullets) == 1
        assert "Jaylen Waddle" in bullets[0]
        assert "()" not in bullets[0]  # no empty parens

    def test_position_in_trade_bullets(self):
        """Trade bullets should also include position."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="TRANSACTION_TRADE",
                payload={
                    "from_franchise_id": "F01",
                    "to_franchise_id": "F02",
                    "player_id": "P300",
                },
            ),
        ]
        bullets = render_deterministic_bullets_v1(
            events,
            team_resolver=lambda x: {"F01": "Team A", "F02": "Team B"}.get(x, x),
            player_resolver=lambda x: "Patrick Mahomes" if x == "P300" else x,
            player_position_resolver=lambda x: "QB" if x == "P300" else None,
        )
        assert len(bullets) == 1
        assert "Patrick Mahomes (QB)" in bullets[0]

    def test_position_in_draft_bullets(self):
        """Draft bullets should also include position."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="DRAFT_PICK",
                payload={"franchise_id": "F01", "player_id": "P400", "round": 1, "pick": 3},
            ),
        ]
        bullets = render_deterministic_bullets_v1(
            events,
            player_resolver=lambda x: "Bijan Robinson" if x == "P400" else x,
            player_position_resolver=lambda x: "RB" if x == "P400" else None,
        )
        assert len(bullets) == 1
        assert "Bijan Robinson (RB)" in bullets[0]


# ── bid_amount Field Fix ─────────────────────────────────────────────


class TestBidAmountFix:
    def test_bid_amount_key_renders(self):
        """bid_amount (the MFL ingest key) should produce a dollar amount in bullet."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="WAIVER_BID_AWARDED",
                payload={"franchise_id": "F01", "player_id": "P100", "bid_amount": 42},
            ),
        ]
        bullets = render_deterministic_bullets_v1(events)
        assert len(bullets) == 1
        assert "$42" in bullets[0]

    def test_bid_key_still_works(self):
        """The original 'bid' key should still work."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="WAIVER_BID_AWARDED",
                payload={"franchise_id": "F01", "player_id": "P100", "bid": 15},
            ),
        ]
        bullets = render_deterministic_bullets_v1(events)
        assert "$15" in bullets[0]

    def test_no_bid_amount_no_dollar(self):
        """If neither bid nor bid_amount is present, no dollar amount shown."""
        from squadvault.core.recaps.render.deterministic_bullets_v1 import (
            CanonicalEventRow,
            render_deterministic_bullets_v1,
        )
        events = [
            CanonicalEventRow(
                canonical_id="c1", occurred_at="2024-10-01",
                event_type="WAIVER_BID_AWARDED",
                payload={"franchise_id": "F01", "player_id": "P100"},
            ),
        ]
        bullets = render_deterministic_bullets_v1(events)
        assert "$" not in bullets[0]
        assert "on waivers" in bullets[0]


# ── Prompt Rendering ─────────────────────────────────────────────────


class TestWriterRoomPromptRendering:
    def test_renders_deltas_and_faab(self, tmp_path):
        """Full render with both deltas and FAAB."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            derive_faab_spending,
            derive_scoring_deltas,
            render_writer_room_context_for_prompt,
        )

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=5,
                        winner_id="A", loser_id="B",
                        winner_score=82, loser_score=70)
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=6,
                        winner_id="A", loser_id="B",
                        winner_score=145, loser_score=95)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="A", player_id="P1", bid_amount=25)
        con.commit()
        con.close()

        deltas = derive_scoring_deltas(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6
        )
        faab = derive_faab_spending(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
            week_index=18, faab_budget=200,
        )
        names = {"A": "Gopher Boys", "B": "Hoosier Daddy"}
        text = render_writer_room_context_for_prompt(
            deltas=deltas, faab=faab, name_map=names,
        )

        assert "Week-over-week" in text
        assert "Gopher Boys" in text
        assert "+63.00" in text
        assert "FAAB spending" in text
        assert "$25" in text
        assert "remaining" in text

    def test_empty_renders_empty(self):
        """No data produces empty string."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            render_writer_room_context_for_prompt,
        )
        text = render_writer_room_context_for_prompt(deltas=(), faab=())
        assert text == ""


# ── Individual FAAB Acquisitions (A3) ────────────────────────────────


class TestFaabAcquisitions:
    """Arc 1 A3: derive_faab_acquisitions and render integration.

    Individual player+bid pairs now flow into the Writer Room context
    so the creative layer has explicit dollar amounts to cite rather
    than synthesizing from cumulative totals.
    """

    def test_derives_acquisitions(self, tmp_path):
        """derive_faab_acquisitions returns one entry per WAIVER_BID_AWARDED."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            derive_faab_acquisitions,
        )

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="F1", player_id="P_BTJ",
                           bid_amount=51.0,
                           occurred_at="2024-09-15T12:00:00Z")
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="F2", player_id="P_MCQ",
                           bid_amount=32.0,
                           occurred_at="2024-09-16T12:00:00Z")
        con.commit()
        con.close()

        acqs = derive_faab_acquisitions(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=5,
        )
        assert len(acqs) == 2
        pids = {a.player_id for a in acqs}
        assert "P_BTJ" in pids
        assert "P_MCQ" in pids
        bid_map = {a.player_id: a.bid_amount for a in acqs}
        assert bid_map["P_BTJ"] == 51.0
        assert bid_map["P_MCQ"] == 32.0

    def test_through_occurred_at_filters(self, tmp_path):
        """through_occurred_at excludes bids after the cutoff."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            derive_faab_acquisitions,
        )

        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="F1", player_id="P_EARLY",
                           bid_amount=20.0,
                           occurred_at="2024-09-10T00:00:00Z")
        _insert_waiver_bid(con, league_id=LEAGUE, season=SEASON,
                           franchise_id="F1", player_id="P_LATE",
                           bid_amount=40.0,
                           occurred_at="2024-10-20T00:00:00Z")
        con.commit()
        con.close()

        acqs = derive_faab_acquisitions(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=5,
            through_occurred_at="2024-10-01T00:00:00Z",
        )
        assert len(acqs) == 1
        assert acqs[0].player_id == "P_EARLY"

    def test_render_includes_individual_bids(self, tmp_path):
        """render_writer_room_context_for_prompt includes individual acquisitions block."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            FaabAcquisition,
            render_writer_room_context_for_prompt,
        )

        acqs = (
            FaabAcquisition(franchise_id="F1", player_id="P_BTJ",
                            bid_amount=51.0, occurred_at=None),
            FaabAcquisition(franchise_id="F2", player_id="P_MCQ",
                            bid_amount=32.0, occurred_at=None),
        )
        player_names = {"P_BTJ": "Thomas, Brian", "P_MCQ": "McConkey, Ladd"}
        names = {"F1": "Brandon", "F2": "Eddie"}

        text = render_writer_room_context_for_prompt(
            deltas=(), faab=(),
            acquisitions=acqs,
            name_map=names,
            player_name_map=player_names,
        )

        assert "Individual FAAB acquisitions" in text
        assert "ONLY these amounts may be cited" in text
        assert "Brandon: $51 for Brian Thomas" in text
        assert "Eddie: $32 for Ladd McConkey" in text

    def test_render_name_format_last_first_converted(self, tmp_path):
        """Storage format 'Last, First' is converted to 'First Last' in render."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            FaabAcquisition,
            render_writer_room_context_for_prompt,
        )

        acqs = (
            FaabAcquisition(franchise_id="F1", player_id="P1",
                            bid_amount=25.0, occurred_at=None),
        )
        text = render_writer_room_context_for_prompt(
            deltas=(), faab=(),
            acquisitions=acqs,
            name_map={"F1": "Steve"},
            player_name_map={"P1": "Jefferson, Justin"},
        )
        assert "Justin Jefferson" in text
        assert "Jefferson, Justin" not in text

    def test_no_acquisitions_omits_block(self):
        """Empty acquisitions list omits the individual bids block entirely."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            render_writer_room_context_for_prompt,
        )

        text = render_writer_room_context_for_prompt(
            deltas=(), faab=(), acquisitions=(),
        )
        assert text == ""
        assert "Individual FAAB" not in text


# ── Phase C: FAAB ROI (Arc 2) ─────────────────────────────────────────


class TestFaabRoi:
    """Arc 2 Phase C: FAAB return-on-investment derivation.

    Post-acquisition points scored per player give the creative layer
    a factual basis for "paid off" or "hasn't delivered" claims.
    """

    def test_basic_roi(self, tmp_path):
        """ROI computed from season history for a FAAB acquisition."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            FaabAcquisition,
            derive_faab_roi,
        )

        acquisitions = (
            FaabAcquisition(
                franchise_id="F1", player_id="P1",
                bid_amount=30.0, occurred_at="2024-09-15T12:00:00Z",
            ),
        )
        # Player scored 15.0, 0.0 (bye), 22.5 across 3 weeks
        history: dict = {
            ("F1", "P1"): [(1, 15.0, True), (2, 0.0, True), (3, 22.5, True)],
        }
        roi = derive_faab_roi(acquisitions, player_season_history=history, current_week=3)
        assert len(roi) == 1
        assert roi[0].franchise_id == "F1"
        assert roi[0].player_id == "P1"
        assert roi[0].bid_amount == 30.0
        assert roi[0].total_points_since_acquisition == 37.5   # 15 + 0 ignored? No — 0 weeks included
        assert roi[0].weeks_scored == 2   # only scored (>0) weeks

    def test_zero_bid_excluded(self):
        """Acquisitions with bid_amount=0 are excluded."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            FaabAcquisition,
            derive_faab_roi,
        )

        acquisitions = (
            FaabAcquisition(
                franchise_id="F1", player_id="P1",
                bid_amount=0.0, occurred_at=None,
            ),
        )
        history: dict = {("F1", "P1"): [(1, 20.0, True)]}
        roi = derive_faab_roi(acquisitions, player_season_history=history, current_week=3)
        assert roi == ()

    def test_no_history_excluded(self):
        """Acquisition with no season history is excluded."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            FaabAcquisition,
            derive_faab_roi,
        )

        acquisitions = (
            FaabAcquisition(
                franchise_id="F1", player_id="P_UNKNOWN",
                bid_amount=25.0, occurred_at=None,
            ),
        )
        roi = derive_faab_roi(acquisitions, player_season_history={}, current_week=3)
        assert roi == ()

    def test_roi_appears_in_render(self):
        """ROI block appears in render_writer_room_context_for_prompt output."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            FaabRoiEntry,
            render_writer_room_context_for_prompt,
        )

        roi = (
            FaabRoiEntry(
                franchise_id="F1", player_id="P1",
                bid_amount=30.0,
                total_points_since_acquisition=87.5,
                weeks_scored=4,
                acquisition_week=2,
            ),
        )
        text = render_writer_room_context_for_prompt(
            deltas=(), faab=(), roi=roi,
            name_map={"F1": "Brandon"},
            player_name_map={"P1": "Thomas, Brian"},
        )
        assert "FAAB post-acquisition" in text
        assert "Brandon" in text
        assert "Brian Thomas" in text
        assert "$30" in text
        assert "87.50 pts" in text
        assert "4 week(s)" in text


# ── Phase D: Manager Identity (Arc 2) ─────────────────────────────────


class TestManagerIdentity:
    """Arc 2 Phase D: derive_manager_identities and render."""

    def _build_db(self, tmp_path, *, owner_name: str | None = "Brandon Weichert",
                   nickname: str | None = "Brandon"):
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        # Insert franchise_directory row with owner_name
        con.execute(
            "INSERT OR REPLACE INTO franchise_directory "
            "(league_id, season, franchise_id, name, owner_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (LEAGUE, SEASON, "F1", "Brandon Knows Ball", owner_name),
        )

        # Insert nickname if provided
        if nickname:
            con.execute(
                "INSERT OR REPLACE INTO franchise_nicknames "
                "(league_id, franchise_id, nickname) "
                "VALUES (?, ?, ?)",
                (LEAGUE, "F1", nickname),
            )
        con.commit()
        con.close()
        return db_path

    def test_derives_owner_first_name(self, tmp_path):
        """owner_first extracted from owner_name."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            derive_manager_identities,
        )
        db_path = self._build_db(tmp_path, nickname=None)
        identities = derive_manager_identities(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        assert len(identities) == 1
        assert identities[0].owner_first == "Brandon"
        assert identities[0].nickname is None
        assert identities[0].preferred_short_form == "Brandon"

    def test_nickname_takes_priority(self, tmp_path):
        """Nickname preferred over owner_first as short-form."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            derive_manager_identities,
        )
        db_path = self._build_db(tmp_path, owner_name="Brandon Weichert", nickname="BK")
        identities = derive_manager_identities(
            db_path=db_path, league_id=LEAGUE, season=SEASON,
        )
        assert identities[0].nickname == "BK"
        assert identities[0].preferred_short_form == "BK"

    def test_render_includes_short_forms(self, tmp_path):
        """Rendered block contains the preferred short-form."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            ManagerIdentity,
            render_manager_identities_for_prompt,
        )
        identities = (
            ManagerIdentity(
                franchise_id="F1", team_name="Brandon Knows Ball",
                owner_name="Brandon Weichert", owner_first="Brandon",
                nickname=None,
            ),
        )
        text = render_manager_identities_for_prompt(identities)
        assert "Manager identity" in text
        assert "Brandon Knows Ball" in text
        assert '"Brandon"' in text

    def test_render_empty_when_no_short_forms(self):
        """Render returns empty string when no identity has a short-form."""
        from squadvault.core.recaps.context.writer_room_context_v1 import (
            ManagerIdentity,
            render_manager_identities_for_prompt,
        )
        identities = (
            ManagerIdentity(
                franchise_id="F1", team_name="Anonymous Team",
                owner_name=None, owner_first=None, nickname=None,
            ),
        )
        text = render_manager_identities_for_prompt(identities)
        assert text == ""
