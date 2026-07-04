"""Scratch-DB integration tests for the Manual Source Adapter (Unit A8).

Frozen Gate-2 obligations at the storage/orchestration layer (never prod; a temp SQLite per test):
  T7.1  approval-or-refuse      - no C3 approval -> ApprovalRequiredError (no silent ingestion)
  T1.1  idempotent re-import    - second import a no-op; rows byte-unchanged
  T2.1  distinct identity space - MANUAL and MFL rows for the same key coexist; MFL untouched
  T5.1  canonical byte-unchanged- existing MFL payload identical before/after a manual import
  T3.1  conflict surfaced       - a differing canonical bid is REPORTED, never resolved/mutated
  T7.2  retention persisted     - stored manual payload carries the C2/D3 content-address fields
"""
from __future__ import annotations

from pathlib import Path

import pytest

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.manual_auction import AttestedAuctionRow, derive_manual_auction_envelopes
from squadvault.ingest.manual_import import (
    ApprovalRequiredError,
    find_canonical_conflicts,
    import_manual_events,
    record_approval,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"

_LEAGUE = "70985"
_SEASON = 2021
_TAG = "KP-AUCTION-2021"
_SRC = f"MANUAL:{_TAG}"
_SHA = "a" * 64
_SEED = {("0002", "12171")}


def _store(tmp_path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "scratch.sqlite")
    store.init_db(SCHEMA_PATH.read_text(encoding="utf-8"))
    return store


def _mfl_row(bid: float) -> dict:
    """A synthetic MFL DRAFT_PICK envelope for 0002/12171 (ledger row)."""
    return {
        "event_type": "DRAFT_PICK", "occurred_at": "2021-09-01T00:00:00Z",
        "external_source": "MFL", "external_id": "mfl-0002-12171",
        "league_id": _LEAGUE, "season": _SEASON,
        "payload": {"mfl_type": "AUCTION_WON", "franchise_id": "0002", "player_id": "12171", "bid_amount": bid},
    }


def _seed_canonical_mfl(store, bid: float) -> None:
    """Seed the MFL pick as a CANONICAL fact (memory + canonical_events) so it appears in
    v_canonical_best_events - the gold fact the conflict check compares against."""
    store.append_events([_mfl_row(bid)])
    with store.connect() as c:
        me_id = c.execute(
            "SELECT id FROM memory_events WHERE external_source='MFL' AND external_id='mfl-0002-12171'"
        ).fetchone()[0]
        c.execute(
            "INSERT INTO canonical_events (league_id, season, event_type, action_fingerprint, "
            "best_memory_event_id, best_score, updated_at, occurred_at) "
            "VALUES (?,?,'DRAFT_PICK','fp_mfl_0002_12171',?,100,?,?)",
            (_LEAGUE, _SEASON, me_id, "2021-09-01T00:00:00Z", "2021-09-01T00:00:00Z"),
        )
        c.commit()


def _manual_envelopes(bid: float = 67):
    envs, held = derive_manual_auction_envelopes(
        league_id=_LEAGUE, season=_SEASON, tag=_TAG,
        rows=[AttestedAuctionRow("0002", "12171", bid)],
        source_artifact_sha256=_SHA, source_artifact_ref=f"cas/{_SHA}", roster_seed=_SEED,
    )
    assert held == []
    return envs


def _approve(store):
    record_approval(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                    source_artifact_sha256=_SHA, actor="founder", notes="KP 2021 attest")


def _count(store) -> int:
    with store.connect() as c:
        return c.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]


def _payload_of(store, external_source: str) -> str:
    with store.connect() as c:
        r = c.execute("SELECT payload_json FROM memory_events WHERE external_source = ?",
                      (external_source,)).fetchone()
    return r[0] if r else ""


# ── T7.1: approval-or-refuse ─────────────────────────────────────────
def test_import_without_approval_refused(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ApprovalRequiredError):
        import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                             source_artifact_sha256=_SHA, envelopes=_manual_envelopes())
    assert _count(store) == 0  # nothing written


def test_import_with_approval_proceeds(tmp_path):
    store = _store(tmp_path)
    _approve(store)
    res = import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                               source_artifact_sha256=_SHA, envelopes=_manual_envelopes())
    assert res.inserted == 1 and res.skipped == 0
    assert _count(store) == 1


# ── T1.1: idempotent re-import ───────────────────────────────────────
def test_reimport_is_noop(tmp_path):
    store = _store(tmp_path)
    _approve(store)
    envs = _manual_envelopes()
    import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                         source_artifact_sha256=_SHA, envelopes=envs)
    before = _payload_of(store, _SRC)
    res2 = import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                                source_artifact_sha256=_SHA, envelopes=envs)
    assert res2.inserted == 0 and res2.skipped == 1
    assert _count(store) == 1
    assert _payload_of(store, _SRC) == before  # byte-unchanged


# ── T2.1 / T5.1: distinct identity space; canonical untouched ────────
def test_manual_and_mfl_coexist_mfl_unchanged(tmp_path):
    store = _store(tmp_path)
    _seed_canonical_mfl(store, 99)                 # seed canonical (memory + canonical_events)
    mfl_before = _payload_of(store, "MFL")
    _approve(store)
    import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                         source_artifact_sha256=_SHA, envelopes=_manual_envelopes(67))
    assert _count(store) == 2                      # both rows present (distinct identity space)
    assert _payload_of(store, "MFL") == mfl_before  # T5.1: canonical byte-unchanged
    assert _payload_of(store, _SRC) != ""           # manual row present


# ── T3.1: conflict surfaced, never resolved ──────────────────────────
def test_conflict_surfaced_not_resolved(tmp_path):
    store = _store(tmp_path)
    _seed_canonical_mfl(store, 99)                 # canonical says $99
    mfl_before = _payload_of(store, "MFL")
    _approve(store)
    res = import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                               source_artifact_sha256=_SHA, envelopes=_manual_envelopes(67))  # manual says $67
    assert len(res.conflicts) == 1
    c = res.conflicts[0]
    assert c.manual_bid == 67.0 and c.canonical_bid == 99.0
    assert c.canonical_external_source == "MFL"
    assert _payload_of(store, "MFL") == mfl_before  # canonical WINS: unmutated
    assert _count(store) == 2                        # manual still lands, surfaced not dropped


def test_no_conflict_when_absent(tmp_path):
    store = _store(tmp_path)  # no MFL row for 0002/12171
    conflicts = find_canonical_conflicts(store, _manual_envelopes(67))
    assert conflicts == []


# ── T7.2: retention fields persisted ─────────────────────────────────
def test_retention_fields_persisted(tmp_path):
    import json
    store = _store(tmp_path)
    _approve(store)
    import_manual_events(store, league_id=_LEAGUE, season=_SEASON, external_source=_SRC,
                         source_artifact_sha256=_SHA, envelopes=_manual_envelopes())
    payload = json.loads(_payload_of(store, _SRC))
    assert payload["source_artifact_sha256"] == _SHA
    assert payload["source_artifact_ref"] == f"cas/{_SHA}"
