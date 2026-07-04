"""Verifier third path + provenance threading for the Manual Source Adapter (Unit A8).

  T6.1  load_all_auction_picks threads external_source (MFL vs MANUAL distinguishable).
  T6.2  verify_draft_auction_dollars disposition:
          - MFL coverage, correct figure  -> NO human-attested note (byte-identical MFL path).
          - MANUAL coverage, correct figure -> SOFT "human-attested" surface (D5, contract section 4).
          - MANUAL coverage, wrong figure   -> HARD (fabrication vs the imported rows still caught).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from squadvault.core.recaps.context.auction_draft_angles_v1 import load_all_auction_picks
from squadvault.core.recaps.verification.recap_verifier_v1 import (
    _build_reverse_name_map,
    _load_franchise_names,
    verify_draft_auction_dollars,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "70985"
SEASON = 2021


def _fresh(tmp_path, name="scratch.sqlite"):
    db = str(tmp_path / name)
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    con.commit()
    con.close()
    return db


def _seed_pick(con, *, fid, pid, pos, bid, name, external_source):
    con.execute(
        "INSERT OR REPLACE INTO franchise_directory (league_id, season, franchise_id, name, updated_at) "
        "VALUES (?,?,?,?,?)",
        (LEAGUE, SEASON, fid, name, "2021-01-01T00:00:00Z"),
    )
    con.execute(
        "INSERT OR REPLACE INTO player_directory (league_id, season, player_id, position, updated_at) "
        "VALUES (?,?,?,?,?)",
        (LEAGUE, SEASON, pid, pos, "2021-01-01T00:00:00Z"),
    )
    occurred = f"{SEASON}-09-01T12:00:00Z"
    import json
    payload = json.dumps({"franchise_id": fid, "player_id": pid, "bid_amount": bid}, sort_keys=True)
    ext_id = f"dp_{fid}_{pid}"
    con.execute(
        "INSERT INTO memory_events (league_id, season, external_source, external_id, event_type, "
        "occurred_at, ingested_at, payload_json) VALUES (?,?,?,?,'DRAFT_PICK',?,?,?)",
        (LEAGUE, SEASON, external_source, ext_id, occurred, occurred, payload),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute(
        "INSERT INTO canonical_events (league_id, season, event_type, action_fingerprint, "
        "best_memory_event_id, best_score, updated_at, occurred_at) VALUES (?,?,'DRAFT_PICK',?,?,100,?,?)",
        (LEAGUE, SEASON, f"fp_{ext_id}", me_id, occurred, occurred),
    )


def _build(tmp_path, external_source, name="scratch.sqlite"):
    db = _fresh(tmp_path, name)
    con = sqlite3.connect(db)
    # One franchise, top $67 / cheapest $12, provenance parameterized.
    _seed_pick(con, fid="0002", pid="12171", pos="QB", bid=67, name="KP Dynasty", external_source=external_source)
    _seed_pick(con, fid="0002", pid="9001", pos="WR", bid=12, name="KP Dynasty", external_source=external_source)
    con.commit()
    con.close()
    return db


def _rmap(db):
    return _build_reverse_name_map(_load_franchise_names(db, LEAGUE, SEASON))


# ── T6.1: external_source threaded onto picks ────────────────────────
def test_external_source_threaded(tmp_path):
    db = _build(tmp_path, "MANUAL:KP-AUCTION-2021", name="a.sqlite")
    picks = [p for p in load_all_auction_picks(db, LEAGUE) if p.season == SEASON]
    assert picks and all(p.external_source == "MANUAL:KP-AUCTION-2021" for p in picks)

    db2 = _build(tmp_path, "MFL", name="b.sqlite")
    picks2 = [p for p in load_all_auction_picks(db2, LEAGUE) if p.season == SEASON]
    assert picks2 and all(p.external_source == "MFL" for p in picks2)


# ── T6.2: disposition ────────────────────────────────────────────────
_CORRECT = "KP Dynasty spent $67 on his top pick at the auction this year."
_WRONG = "KP Dynasty splurged $75 on his top pick at the auction this year."


def test_mfl_correct_figure_no_attested_note(tmp_path):
    """MFL coverage, correct figure -> zero failures (byte-identical existing behavior)."""
    db = _build(tmp_path, "MFL")
    out = verify_draft_auction_dollars(_CORRECT, db_path=db, league_id=LEAGUE, season=SEASON,
                                       reverse_name_map=_rmap(db))
    assert out == []


def test_manual_correct_figure_surfaced_human_attested(tmp_path):
    """MANUAL coverage, correct figure -> SOFT human-attested surface (not silent adapter-grade)."""
    db = _build(tmp_path, "MANUAL:KP-AUCTION-2021")
    out = verify_draft_auction_dollars(_CORRECT, db_path=db, league_id=LEAGUE, season=SEASON,
                                       reverse_name_map=_rmap(db))
    dad = [f for f in out if f.category == "DRAFT_AUCTION_DOLLAR"]
    assert len(dad) == 1
    assert dad[0].severity == "SOFT"
    assert "human-attested" in dad[0].evidence.lower()


def test_manual_wrong_figure_still_hard(tmp_path):
    """MANUAL coverage, wrong figure -> HARD (fabrication vs imported rows still caught)."""
    db = _build(tmp_path, "MANUAL:KP-AUCTION-2021")
    out = verify_draft_auction_dollars(_WRONG, db_path=db, league_id=LEAGUE, season=SEASON,
                                       reverse_name_map=_rmap(db))
    dad = [f for f in out if f.category == "DRAFT_AUCTION_DOLLAR"]
    assert len(dad) == 1
    assert dad[0].severity == "HARD"
    assert "75" in dad[0].claim
