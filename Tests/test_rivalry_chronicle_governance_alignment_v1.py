"""Phase 8B — Rivalry Chronicle Governance Alignment.

Verifies that the Rivalry Chronicle v1 operates under the same governance
model as the Weekly Recap:

- Generate produces DRAFT (not APPROVED)
- Human approval is required to transition to APPROVED
- Artifacts are versioned and traceable
- Fingerprint idempotency prevents duplicate drafts
- Both artifact classes share the recap_artifacts table

Contract card: Rivalry_Chronicle_v1_Contract_Card.md
  "Explicit human approval required"
  "Approved artifacts are immutable"
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy
from squadvault.chronicle.persist_rivalry_chronicle_v1 import (
    persist_rivalry_chronicle_v1,
)
from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.recaps.recap_artifacts import (
    ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
    ARTIFACT_TYPE_WEEKLY_RECAP,
    approve_recap_artifact,
)
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.storage.migrate import init_and_migrate
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)

LEAGUE = "99999"
LEAGUE_INT = 99999
SEASON = 2024


def _lock_event(week, ts):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "gov_test", "external_id": f"gov_lock_w{week}",
        "event_type": "TRANSACTION_LOCK_ALL_PLAYERS",
        "occurred_at": ts,
        "payload": {"type": "LOCK_ALL_PLAYERS", "week": week},
    }


def _waiver_event(franchise, player, bid, ts, uid):
    return {
        "league_id": LEAGUE, "season": SEASON,
        "external_source": "gov_test", "external_id": f"gov_{uid}",
        "event_type": "WAIVER_BID_AWARDED",
        "occurred_at": ts,
        "payload": {"franchise_id": franchise, "player_id": player, "bid_amount": bid},
    }


@pytest.fixture
def gov_db(tmp_path):
    """Fresh DB with weekly recap approved for week 1 (prerequisite for chronicle)."""
    db_path = str(tmp_path / "governance.sqlite")
    init_and_migrate(db_path)
    store = SQLiteStore(db_path=Path(db_path))

    events = [
        _lock_event(1, "2024-09-05T12:00:00Z"),
        _lock_event(2, "2024-09-12T12:00:00Z"),
        _waiver_event("F01", "P100", "25", "2024-09-06T10:00:00Z", "w1_waiver1"),
        _waiver_event("F02", "P200", "15", "2024-09-07T10:00:00Z", "w1_waiver2"),
        _waiver_event("F03", "P300", "30", "2024-09-08T10:00:00Z", "w1_waiver3"),
    ]
    store.append_events(events)

    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)

    sel = select_weekly_recap_events_v1(
        db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=1,
    )
    upsert_recap_run(db_path, RecapRunRecord(
        league_id=LEAGUE, season=SEASON, week_index=1, state="ELIGIBLE",
        window_mode=sel.window.mode,
        window_start=sel.window.window_start,
        window_end=sel.window.window_end,
        selection_fingerprint=sel.fingerprint,
        canonical_ids=[str(c) for c in sel.canonical_ids],
        counts_by_type=sel.counts_by_type,
    ))

    generate_weekly_recap_draft(
        db_path=db_path, league_id=LEAGUE, season=SEASON,
        week_index=1, reason="gov_alignment_prereq",
    )
    approve_latest_weekly_recap(
        db_path=db_path, league_id=LEAGUE, season=SEASON,
        week_index=1, approved_by="test_founder",
    )

    return db_path


class TestRivalryChronicleGovernanceAlignment:
    """Both artifact classes must follow the same governance model."""

    def test_persist_produces_draft_not_approved(self, gov_db):
        """persist_rivalry_chronicle_v1 creates DRAFT, not APPROVED."""
        result = persist_rivalry_chronicle_v1(
            db_path=gov_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1,),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert result.created_new is True

        con = sqlite3.connect(gov_db)
        row = con.execute(
            "SELECT state FROM recap_artifacts WHERE artifact_type=? AND version=?",
            (ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1, result.version),
        ).fetchone()
        con.close()

        assert row is not None
        assert row[0] == "DRAFT", (
            f"persist must produce DRAFT, got {row[0]}. Human approval required."
        )

    def test_full_chronicle_lifecycle_draft_approve(self, gov_db):
        """Chronicle follows same DRAFT -> approve -> APPROVED lifecycle."""
        result = persist_rivalry_chronicle_v1(
            db_path=gov_db,
            league_id=LEAGUE_INT,
            season=SEASON,
            week_indices=(1,),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert result.created_new is True

        con = sqlite3.connect(gov_db)
        state = con.execute(
            "SELECT state FROM recap_artifacts WHERE artifact_type=? AND version=?",
            (ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1, result.version),
        ).fetchone()[0]
        con.close()
        assert state == "DRAFT"

        approve_recap_artifact(
            gov_db,
            league_id=str(LEAGUE_INT),
            season=SEASON,
            week_index=result.anchor_week_index,
            version=result.version,
            approved_by="test_founder",
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
        )

        con = sqlite3.connect(gov_db)
        state = con.execute(
            "SELECT state FROM recap_artifacts WHERE artifact_type=? AND version=?",
            (ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1, result.version),
        ).fetchone()[0]
        con.close()
        assert state == "APPROVED"

    def test_fingerprint_idempotency(self, gov_db):
        """Same inputs produce same fingerprint, preventing duplicate DRAFTs."""
        r1 = persist_rivalry_chronicle_v1(
            db_path=gov_db, league_id=LEAGUE_INT, season=SEASON,
            week_indices=(1,), week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        r2 = persist_rivalry_chronicle_v1(
            db_path=gov_db, league_id=LEAGUE_INT, season=SEASON,
            week_indices=(1,), week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert r1.created_new is True
        assert r2.created_new is False
        assert r1.version == r2.version

    def test_both_artifact_classes_use_same_table(self, gov_db):
        """Weekly Recap and Rivalry Chronicle both store in recap_artifacts."""
        persist_rivalry_chronicle_v1(
            db_path=gov_db, league_id=LEAGUE_INT, season=SEASON,
            week_indices=(1,), week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        con = sqlite3.connect(gov_db)
        types = sorted({
            r[0] for r in con.execute(
                "SELECT DISTINCT artifact_type FROM recap_artifacts WHERE league_id=?",
                (LEAGUE_INT,),
            ).fetchall()
        })
        con.close()
        assert ARTIFACT_TYPE_WEEKLY_RECAP in types
        assert ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1 in types

    def test_chronicle_rendered_text_is_deterministic(self, gov_db):
        """Rendered text contains traceable, deterministic content."""
        result = persist_rivalry_chronicle_v1(
            db_path=gov_db, league_id=LEAGUE_INT, season=SEASON,
            week_indices=(1,), week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )
        con = sqlite3.connect(gov_db)
        row = con.execute(
            "SELECT rendered_text, selection_fingerprint FROM recap_artifacts "
            "WHERE artifact_type=? AND version=?",
            (ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1, result.version),
        ).fetchone()
        con.close()
        assert row[0] is not None and len(row[0]) > 0
        assert row[1] is not None and len(row[1]) == 64

    def test_chronicle_does_not_modify_weekly_recap(self, gov_db):
        """Generating a chronicle must not alter existing weekly recap artifacts."""
        con = sqlite3.connect(gov_db)
        before = con.execute(
            "SELECT id, state, rendered_text, selection_fingerprint "
            "FROM recap_artifacts WHERE artifact_type=? ORDER BY id",
            (ARTIFACT_TYPE_WEEKLY_RECAP,),
        ).fetchall()
        con.close()

        persist_rivalry_chronicle_v1(
            db_path=gov_db, league_id=LEAGUE_INT, season=SEASON,
            week_indices=(1,), week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            created_at_utc="2024-12-01T00:00:00Z",
        )

        con = sqlite3.connect(gov_db)
        after = con.execute(
            "SELECT id, state, rendered_text, selection_fingerprint "
            "FROM recap_artifacts WHERE artifact_type=? ORDER BY id",
            (ARTIFACT_TYPE_WEEKLY_RECAP,),
        ).fetchall()
        con.close()
        assert before == after, "Chronicle generation must not modify weekly recap artifacts"
