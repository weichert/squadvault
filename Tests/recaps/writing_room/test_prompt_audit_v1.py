"""Tests for the Prompt Audit sidecar (v2 contract, rev3).

With rev3's completed CATEGORY_TO_DETECTOR map, all 5 tests should pass.
The drift detector test remains in place as a standing guardrail: any future
narrative-angle category added to the source without a corresponding map
entry will fail this test with an explicit missing-keys list.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from squadvault.recaps.writing_room.prompt_audit_v1 import (
    AUDIT_ENV_VAR,
    CATEGORY_TO_DETECTOR,
    maybe_capture_attempt,
)


SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "squadvault"
    / "core"
    / "storage"
    / "schema_prompt_audit.sql"
)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Materialize the prompt_audit schema into a throwaway sqlite file."""
    path = tmp_path / "audit.db"
    schema_sql = SCHEMA_PATH.read_text()
    con = sqlite3.connect(str(path))
    try:
        con.executescript(schema_sql)
        con.commit()
    finally:
        con.close()
    return str(path)


@pytest.fixture
def audit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(AUDIT_ENV_VAR, "1")


def _make_verification_result(passed: bool = True) -> MagicMock:
    r = MagicMock()
    r.passed = passed
    r.checks = []
    return r


def _make_angle(category: str) -> MagicMock:
    a = MagicMock()
    a.category = category
    return a


# ---------------------------------------------------------------------------
# Test 1 — happy path: env gate on → one row written
# ---------------------------------------------------------------------------
def test_maybe_capture_attempt_writes_row_when_enabled(
    db_path: str, audit_env: None
) -> None:
    maybe_capture_attempt(
        db_path,
        league_id="70985",
        season=2025,
        week_index=7,
        attempt=1,
        all_angles=[_make_angle("PLAYER_BOOM_BUST"), _make_angle("SCORING_MOMENTUM_IN_STREAK")],
        budgeted=[_make_angle("PLAYER_BOOM_BUST")],
        narrative_angles_text="Bullet 1\nBullet 2",
        narrative_draft="Draft prose here.",
        verification_result=_make_verification_result(passed=True),
    )

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT league_id, season, week_index, attempt, verification_passed "
            "FROM prompt_audit"
        ).fetchall()
    finally:
        con.close()

    assert rows == [("70985", 2025, 7, 1, 1)]


# ---------------------------------------------------------------------------
# Test 2 — gate off: no row written
# ---------------------------------------------------------------------------
def test_maybe_capture_attempt_is_noop_when_disabled(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(AUDIT_ENV_VAR, raising=False)

    maybe_capture_attempt(
        db_path,
        league_id="70985",
        season=2025,
        week_index=7,
        attempt=1,
        all_angles=[_make_angle("PLAYER_BOOM_BUST")],
        budgeted=[],
        narrative_angles_text="",
        narrative_draft="",
        verification_result=_make_verification_result(passed=True),
    )

    con = sqlite3.connect(db_path)
    try:
        (count,) = con.execute("SELECT COUNT(*) FROM prompt_audit").fetchone()
    finally:
        con.close()

    assert count == 0


# ---------------------------------------------------------------------------
# Test 3 — append-only: multiple attempts at the same key all persist
#
# Replaces v1's test_unique_constraint. v2 deliberately removes the UNIQUE
# constraint; retries for the same (league, season, week, attempt) tuple are
# valid audit history, not integrity violations.
# ---------------------------------------------------------------------------
def test_append_only_behavior(db_path: str, audit_env: None) -> None:
    for i in range(3):
        maybe_capture_attempt(
            db_path,
            league_id="70985",
            season=2025,
            week_index=7,
            attempt=1,  # identical tuple across all three writes
            all_angles=[_make_angle("PLAYER_BOOM_BUST")],
            budgeted=[],
            narrative_angles_text=f"angles v{i}",
            narrative_draft=f"draft v{i}",
            verification_result=_make_verification_result(passed=(i == 2)),
        )

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT narrative_draft, verification_passed "
            "FROM prompt_audit ORDER BY id"
        ).fetchall()
    finally:
        con.close()

    assert rows == [
        ("draft v0", 0),
        ("draft v1", 0),
        ("draft v2", 1),
    ]


# ---------------------------------------------------------------------------
# Test 4 — CATEGORY_TO_DETECTOR contains the current-phase audit anchors
#
# Sanity count set to 50: the complete set of D-attributable categories
# across the three canonical angle source files (D1–D50, with D41 included
# for coverage even though its detector is currently disabled).
# ---------------------------------------------------------------------------
def test_category_to_detector_includes_audit_anchors() -> None:
    assert CATEGORY_TO_DETECTOR["PLAYER_BOOM_BUST"] == "D4"
    assert CATEGORY_TO_DETECTOR["SCORING_MOMENTUM_IN_STREAK"] == "D49"
    assert len(CATEGORY_TO_DETECTOR) == 50


# ---------------------------------------------------------------------------
# Test 5 — DRIFT DETECTOR (standing guardrail).
#
# Scans the canonical narrative-angle detector source files for all
# `category="..."` literals, and asserts that every one of them has a mapping
# in CATEGORY_TO_DETECTOR. When the test fails, pytest prints the missing
# keys — that list is the authoritative set of additions to make to the map.
# ---------------------------------------------------------------------------
ANGLE_SOURCE_FILES = [
    "src/squadvault/core/recaps/context/player_narrative_angles_v1.py",
    "src/squadvault/core/recaps/context/franchise_deep_angles_v1.py",
    "src/squadvault/core/recaps/context/auction_draft_angles_v1.py",
]

_CATEGORY_RE = re.compile(r'category\s*=\s*"([A-Z_][A-Z0-9_]*)"')


def _scan_live_categories() -> set[str]:
    repo_root = Path(__file__).resolve().parents[3]
    found: set[str] = set()
    for rel in ANGLE_SOURCE_FILES:
        path = repo_root / rel
        if not path.exists():
            continue
        found.update(_CATEGORY_RE.findall(path.read_text()))
    return found


def test_category_to_detector_drift_detector() -> None:
    live = _scan_live_categories()
    missing = sorted(live - set(CATEGORY_TO_DETECTOR))
    assert not missing, (
        "CATEGORY_TO_DETECTOR is out of sync with live detector output. "
        f"Missing keys ({len(missing)}): {missing}"
    )
