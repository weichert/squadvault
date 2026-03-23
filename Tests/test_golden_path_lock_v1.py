"""Phase 6 — Golden Path Lock Test.

Verifies the complete canonical operator flow end-to-end on a fresh DB:

 1. Ingest domain events (memory_events append-only)
 2. Canonicalize (deterministic projection)
 3. Compute weekly window (lock-to-lock)
 4. Select canonical events within window (allowlist-filtered)
 5. Persist recap_runs with selection trace
 6. Evaluate EAL restraint directive
 7. Generate DRAFT artifact (from recap_runs, no recaps table)
 8. Verify EAL directive persisted as audit metadata
 9. Approve artifact (human gate)
10. Version and persist approved artifact
11. Export approved artifact bundle
12. Retrieve archived recap across seasons

After this test passes, factual recap generation is LOCKED.
No redesign of fact selection, no new cleverness in recap structure,
no hidden inference. Only additive, contract-consistent changes.

Also operationalizes the Recap Review Heuristic (Phase 6C):
- Identity test: recap contains league-specific identifiers
- Memory test: rendered text traces to known canonical events
- Tone consistency: no fabricated content, no dramatization
- Edit burden: rendered text is complete without rewriting
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from squadvault.core.storage.migrate import init_and_migrate
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_runs import upsert_recap_run, RecapRunRecord
from squadvault.core.recaps.recap_artifacts import (
    latest_approved_version,
    approve_recap_artifact,
)
from squadvault.core.exports.approved_weekly_recap_export_v1 import (
    fetch_latest_approved_weekly_recap,
    write_approved_weekly_recap_export_bundle,
)
from squadvault.recaps.weekly_recap_lifecycle import (
    generate_weekly_recap_draft,
    approve_latest_weekly_recap,
)

LEAGUE = "golden_path_lock_league"
SEASON = 2024


def _lock_event(week: int, ts: str) -> dict:
    """Build a LOCK_ALL_PLAYERS event."""
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "gp_test", "external_id": f"gp_lock_w{week}_{ts}",
        "event_type": "TRANSACTION_LOCK_ALL_PLAYERS",
        "occurred_at": ts,
        "payload": {"type": "LOCK_ALL_PLAYERS", "week": week},
    }


def _waiver_event(franchise: str, player: str, bid: str, ts: str, uid: str) -> dict:
    """Build a WAIVER_BID_AWARDED event."""
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "gp_test", "external_id": f"gp_{uid}",
        "event_type": "WAIVER_BID_AWARDED",
        "occurred_at": ts,
        "payload": {"franchise_id": franchise, "player_id": player, "bid_amount": bid},
    }


def _fa_event(franchise: str, added: str, dropped: str, ts: str, uid: str) -> dict:
    """Build a TRANSACTION_FREE_AGENT event."""
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "gp_test", "external_id": f"gp_{uid}",
        "event_type": "TRANSACTION_FREE_AGENT",
        "occurred_at": ts,
        "payload": {
            "franchise_id": franchise,
            "players_added_ids": [added],
            "players_dropped_ids": [dropped],
        },
    }


@pytest.fixture
def golden_path_db(tmp_path):
    """Fresh DB with realistic multi-week activity."""
    db_path = str(tmp_path / "golden_path.sqlite")
    init_and_migrate(db_path)
    store = SQLiteStore(db_path=Path(db_path))

    # Three lock boundaries (two complete weeks)
    locks = [
        _lock_event(1, "2024-09-05T12:00:00Z"),
        _lock_event(2, "2024-09-12T12:00:00Z"),
        _lock_event(3, "2024-09-19T12:00:00Z"),
    ]

    # Week 1 activity (between lock 1 and lock 2)
    week1 = [
        _waiver_event("F01", "P100", "25", "2024-09-06T10:00:00Z", "w1_waiver1"),
        _waiver_event("F02", "P200", "15", "2024-09-07T10:00:00Z", "w1_waiver2"),
        _fa_event("F03", "P300", "P400", "2024-09-08T10:00:00Z", "w1_fa1"),
        _waiver_event("F04", "P500", "30", "2024-09-09T10:00:00Z", "w1_waiver3"),
    ]

    # Week 2 activity (between lock 2 and lock 3)
    week2 = [
        _waiver_event("F01", "P600", "50", "2024-09-13T10:00:00Z", "w2_waiver1"),
        _fa_event("F02", "P700", "P800", "2024-09-14T10:00:00Z", "w2_fa1"),
    ]

    inserted, _ = store.append_events(locks + week1 + week2)
    assert inserted == 9

    return db_path


class TestGoldenPathLock:
    """Full canonical operator flow: the weekly recap golden path."""

    def test_complete_golden_path(self, golden_path_db, tmp_path):
        """Steps 1-12 of the canonical operator flow, verified end-to-end."""
        db = golden_path_db

        # ── Step 1: Events already ingested by fixture ──────────────
        con = sqlite3.connect(db)
        mem_count = con.execute(
            "SELECT COUNT(*) FROM memory_events WHERE league_id=?", (LEAGUE,)
        ).fetchone()[0]
        con.close()
        assert mem_count == 9, "Step 1: all events ingested"

        # ── Step 2: Canonicalize ────────────────────────────────────
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)

        con = sqlite3.connect(db)
        canon_count = con.execute(
            "SELECT COUNT(*) FROM canonical_events WHERE league_id=? AND season=?",
            (LEAGUE, SEASON),
        ).fetchone()[0]
        con.close()
        assert canon_count >= 6, "Step 2: canonical events created"

        # ── Step 3-4: Compute window + select events ────────────────
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        assert sel.window.mode == "LOCK_TO_LOCK", "Step 3: deterministic window"
        assert sel.window.window_start == "2024-09-05T12:00:00Z"
        assert sel.window.window_end == "2024-09-12T12:00:00Z"
        assert len(sel.canonical_ids) >= 3, "Step 4: events selected within window"
        assert len(sel.fingerprint) == 64, "Step 4: selection fingerprint is SHA-256"

        # ── Step 5: Persist recap_runs ──────────────────────────────
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1,
            state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))

        # ── Step 6-7: EAL evaluation + generate DRAFT ──────────────
        draft = generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="golden_path_lock_test",
        )
        assert draft.version == 1, "Step 7: first draft version"
        assert draft.created_new is True
        assert draft.selection_fingerprint == sel.fingerprint

        # ── Step 8: Verify EAL persisted ────────────────────────────
        con = sqlite3.connect(db)
        eal_row = con.execute(
            "SELECT editorial_attunement_v1 FROM recap_runs "
            "WHERE league_id=? AND season=? AND week_index=?",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()
        assert eal_row is not None and eal_row[0] is not None, (
            "Step 8: EAL directive persisted as audit metadata"
        )

        # ── Step 9-10: Approve (human gate) ─────────────────────────
        approval = approve_latest_weekly_recap(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, approved_by="founder_steve",
        )
        assert approval.approved_version == 1, "Step 9: approval succeeds"
        assert latest_approved_version(db, LEAGUE, SEASON, 1) == 1, (
            "Step 10: version persisted"
        )

        # ── Step 11: Export approved bundle ─────────────────────────
        artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, 1)
        assert artifact.state == "APPROVED"
        assert artifact.approved_by == "founder_steve"

        export_dir = tmp_path / "export"
        manifest = write_approved_weekly_recap_export_bundle(artifact, export_dir)
        assert Path(manifest.recap_md).exists(), "Step 11: markdown export exists"
        assert Path(manifest.recap_json).exists(), "Step 11: JSON export exists"
        assert Path(manifest.metadata_json).exists(), "Step 11: metadata exists"

        # ── Step 12: Archive retrieval across weeks ─────────────────
        # Process week 2 and verify week 1 is still retrievable
        sel2 = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=2,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=2,
            state="ELIGIBLE",
            window_mode=sel2.window.mode,
            window_start=sel2.window.window_start,
            window_end=sel2.window.window_end,
            selection_fingerprint=sel2.fingerprint,
            canonical_ids=[str(c) for c in sel2.canonical_ids],
            counts_by_type=sel2.counts_by_type,
        ))
        draft2 = generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=2, reason="golden_path_week2",
        )
        approve_latest_weekly_recap(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=2, approved_by="founder_steve",
        )

        # Retrieve week 1 archive after week 2 is approved
        w1_artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, 1)
        assert w1_artifact.state == "APPROVED", "Step 12: week 1 still retrievable"
        assert w1_artifact.selection_fingerprint == sel.fingerprint

        w2_artifact = fetch_latest_approved_weekly_recap(db, LEAGUE, SEASON, 2)
        assert w2_artifact.state == "APPROVED", "Step 12: week 2 retrievable"


class TestRecapReviewHeuristic:
    """Operationalized recap review criteria (Phase 6C).

    These tests verify that generated recaps satisfy the Recap Review
    Heuristic criteria programmatically.
    """

    def test_identity_test_passes(self, golden_path_db):
        """Could this recap belong to a different league? No — it contains
        league-specific identifiers."""
        db = golden_path_db
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))
        generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="review_heuristic_test",
        )

        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT rendered_text FROM recap_artifacts "
            "WHERE league_id=? AND season=? AND week_index=? AND state='DRAFT'",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()

        text = row[0]
        # Identity: contains league ID and season
        assert LEAGUE in text, "Identity test: league_id present"
        assert str(SEASON) in text, "Identity test: season present"
        assert "Week 1" in text, "Identity test: week_index present"

    def test_memory_test_passes(self, golden_path_db):
        """Does the recap emerge from known facts? Yes — selection fingerprint
        and canonical IDs are traceable."""
        db = golden_path_db
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))
        generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="memory_test",
        )

        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT rendered_text, selection_fingerprint FROM recap_artifacts "
            "WHERE league_id=? AND season=? AND week_index=? AND state='DRAFT'",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()

        text, stored_fp = row[0], row[1]
        # Memory: fingerprint is traceable
        assert stored_fp == sel.fingerprint, "Memory test: fingerprint traces to selection"
        # Memory: window bounds present
        assert sel.window.window_start in text, "Memory test: window start in text"
        assert sel.window.window_end in text, "Memory test: window end in text"
        # Memory: selection fingerprint present in rendered text
        assert sel.fingerprint in text, "Memory test: fingerprint in rendered text"

    def test_no_fabrication(self, golden_path_db):
        """Recap does not contain fabricated content — no player names,
        no dramatization, no inference beyond what events provide."""
        db = golden_path_db
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))
        generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="no_fabrication_test",
        )

        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT rendered_text FROM recap_artifacts "
            "WHERE league_id=? AND season=? AND week_index=? AND state='DRAFT'",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()

        text = row[0]
        # No fabrication markers
        fabrication_signals = [
            "incredible", "amazing", "crushing", "dominant",
            "revenge", "rivalry", "heated", "shocking",
            "must-win", "blockbuster", "superstar",
        ]
        for signal in fabrication_signals:
            assert signal.lower() not in text.lower(), (
                f"No fabrication: '{signal}' should not appear in deterministic recap"
            )

    def test_edit_burden_acceptable(self, golden_path_db):
        """A commissioner should not need to rewrite this recap to trust it.
        The rendered text is structurally complete."""
        db = golden_path_db
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))
        generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="edit_burden_test",
        )

        con = sqlite3.connect(db)
        row = con.execute(
            "SELECT rendered_text FROM recap_artifacts "
            "WHERE league_id=? AND season=? AND week_index=? AND state='DRAFT'",
            (LEAGUE, SEASON, 1),
        ).fetchone()
        con.close()

        text = row[0]
        # Structural completeness checks
        assert "SquadVault Weekly Recap" in text, "Header present"
        assert "Window:" in text, "Window bounds present"
        assert "Selection fingerprint:" in text, "Fingerprint present"
        assert "Events selected:" in text, "Event count present"
        assert "Trace" in text, "Trace section present"
        assert len(text) > 200, "Recap has substantive content"


class TestExplicitRegeneration:
    """Regeneration is only allowed under approved conditions (Phase 6B lock)."""

    def test_regeneration_creates_new_version(self, golden_path_db):
        """Force regeneration creates a new version, not an overwrite."""
        db = golden_path_db
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))

        v1 = generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="initial_draft",
        )
        assert v1.version == 1

        v2 = generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="regeneration", force=True,
        )
        assert v2.version == 2, "Regeneration creates new version"
        assert v2.created_new is True

    def test_withhold_path_works(self, golden_path_db):
        """Withholding a recap is a valid outcome."""
        from squadvault.core.recaps.recap_artifacts import withhold_recap_artifact

        db = golden_path_db
        canonicalize(league_id=LEAGUE, season=SEASON, db_path=db)
        sel = select_weekly_recap_events_v1(
            db_path=db, league_id=LEAGUE, season=SEASON, week_index=1,
        )
        upsert_recap_run(db, RecapRunRecord(
            league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
            window_mode=sel.window.mode,
            window_start=sel.window.window_start,
            window_end=sel.window.window_end,
            selection_fingerprint=sel.fingerprint,
            canonical_ids=[str(c) for c in sel.canonical_ids],
            counts_by_type=sel.counts_by_type,
        ))

        draft = generate_weekly_recap_draft(
            db_path=db, league_id=LEAGUE, season=SEASON,
            week_index=1, reason="will_withhold",
        )

        withhold_recap_artifact(
            db, LEAGUE, SEASON, 1, draft.version,
            withheld_reason="silence_preferred",
        )

        # Verify no approved version exists
        assert latest_approved_version(db, LEAGUE, SEASON, 1) is None, (
            "Withheld recap should not be approved"
        )
