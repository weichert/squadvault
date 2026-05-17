"""Phase D: Commissioner review surface — verification report tests.

Covers render_verification_report() and _load_latest_verification_result()
from squadvault.consumers.editorial_review_week.

D1: Inline claim annotation (hard + soft failures listed with evidence)
D2: Summary header (PASSED / FLAGGED status, checks run, counts)
D3: Suggested edits per hard failure category
D4: Edit burden counter with regeneration recommendation at threshold
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)

LEAGUE = "70985"
SEASON = 2025
WEEK = 4


def _fresh_db(tmp_path, name="test.sqlite"):
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


def _insert_prompt_audit_row(
    con: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
    attempt: int = 1,
    verification_passed: bool = True,
    hard_failures: list[dict] | None = None,
    soft_failures: list[dict] | None = None,
    checks_run: int = 11,
) -> int:
    """Insert a prompt_audit row with a synthetic verification_result_json."""
    result = {
        "passed": verification_passed,
        "hard_failures": hard_failures or [],
        "soft_failures": soft_failures or [],
        "checks_run": checks_run,
    }
    con.execute(
        """INSERT INTO prompt_audit
           (league_id, season, week_index, attempt,
            angles_summary_json, budgeted_summary_json,
            narrative_angles_text, narrative_draft,
            verification_passed, verification_result_json, prompt_text,
            captured_at)
           VALUES (?, ?, ?, ?, '[]', '[]', '', 'draft text', ?, ?, '',
                   strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
        (
            league_id, season, week_index, attempt,
            1 if verification_passed else 0,
            json.dumps(result),
        ),
    )
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


class TestLoadLatestVerificationResult:
    """_load_latest_verification_result() behaviour."""

    def test_returns_none_when_no_record(self, tmp_path):
        from squadvault.consumers.editorial_review_week import (
            _load_latest_verification_result,
        )
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        result = _load_latest_verification_result(con, LEAGUE, SEASON, WEEK)
        assert result is None

    def test_returns_passing_result(self, tmp_path):
        from squadvault.consumers.editorial_review_week import (
            _load_latest_verification_result,
        )
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=True, checks_run=11,
        )
        con.commit()
        result = _load_latest_verification_result(con, LEAGUE, SEASON, WEEK)
        assert result is not None
        assert result["passed"] is True
        assert result["checks_run"] == 11

    def test_prefers_passing_over_failing(self, tmp_path):
        from squadvault.consumers.editorial_review_week import (
            _load_latest_verification_result,
        )
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        # Insert passing attempt first (lower id)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            attempt=1, verification_passed=True, checks_run=9,
        )
        # Insert failing attempt after (higher id)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            attempt=2, verification_passed=False,
            hard_failures=[{"category": "SCORE", "claim": "bad", "evidence": "real"}],
            checks_run=11,
        )
        con.commit()
        result = _load_latest_verification_result(con, LEAGUE, SEASON, WEEK)
        # Should prefer the passing row
        assert result is not None
        assert result["passed"] is True


class TestRenderVerificationReport:
    """render_verification_report() output for Phase D surface."""

    def _con(self, db_path):
        return sqlite3.connect(db_path)

    def test_d2_passed_status_shown(self, tmp_path):
        """D2: PASSED status appears in header for clean drafts."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=True, checks_run=11,
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "PASSED" in report
        assert "Checks run: 11" in report

    def test_d2_flagged_status_for_hard_failures(self, tmp_path):
        """D2: FLAGGED status when hard failures are present."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=False,
            hard_failures=[
                {
                    "category": "FAAB_CLAIM",
                    "claim": "$51 FAAB attributed to Brian Thomas",
                    "evidence": "No WAIVER_BID_AWARDED record found.",
                }
            ],
            checks_run=11,
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "FLAGGED" in report
        assert "Hard failures: 1" in report

    def test_d1_hard_failure_claim_shown(self, tmp_path):
        """D1: Hard failure claim and evidence shown inline."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=False,
            hard_failures=[
                {
                    "category": "CHAMPIONSHIP_CLAIM",
                    "claim": "6 championship appearances attributed to KP",
                    "evidence": "Canonical: 7. Championship weeks: W16/W18.",
                }
            ],
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "CHAMPIONSHIP_CLAIM" in report
        assert "6 championship appearances" in report
        assert "Canonical: 7" in report

    def test_d3_faab_suggested_edit(self, tmp_path):
        """D3: FAAB_CLAIM hard failure produces a specific suggested edit."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=False,
            hard_failures=[
                {
                    "category": "FAAB_CLAIM",
                    "claim": "$51 FAAB attributed to Brian Thomas",
                    "evidence": "No WAIVER_BID_AWARDED record.",
                }
            ],
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "SUGGESTED EDITS" in report
        assert "Remove or correct the dollar amount" in report

    def test_d4_edit_burden_none_for_passing(self, tmp_path):
        """D4: No edit burden shown for passing drafts."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=True,
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "EDIT BURDEN: None" in report

    def test_d4_regeneration_recommended_at_three(self, tmp_path):
        """D4: Regeneration recommended when 3+ hard failures."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=False,
            hard_failures=[
                {"category": "FAAB_CLAIM", "claim": "A", "evidence": "B"},
                {"category": "FAAB_CLAIM", "claim": "C", "evidence": "D"},
                {"category": "SCORE", "claim": "E", "evidence": "F"},
            ],
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "REGENERATION RECOMMENDED" in report

    def test_no_record_reports_gracefully(self, tmp_path):
        """No prompt_audit record produces a graceful 'no record' message."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "No verification record" in report

    def test_soft_warnings_shown(self, tmp_path):
        """D1: Soft warnings listed separately from hard failures."""
        from squadvault.consumers.editorial_review_week import (
            render_verification_report,
        )
        db_path = _fresh_db(tmp_path)
        con = self._con(db_path)
        _insert_prompt_audit_row(
            con, league_id=LEAGUE, season=SEASON, week_index=WEEK,
            verification_passed=True,
            soft_failures=[
                {"category": "BANNED_PHRASE", "claim": "nightmare season", "evidence": ""},
            ],
        )
        con.commit()
        report = render_verification_report(
            con, db_path, LEAGUE, SEASON, WEEK,
        )
        assert "SOFT WARNINGS" in report
        assert "BANNED_PHRASE" in report
        assert "nightmare season" in report
