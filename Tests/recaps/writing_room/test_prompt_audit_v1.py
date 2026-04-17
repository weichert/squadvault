"""Tests for the Prompt Audit sidecar (v2 contract, rev4).

With rev4's expanded scan scope, all live-emitting category source files
are tracked by the drift detector (Test 5) and audited for completeness.
Migration 0009 adds prompt_text capture; tests 6 and 7 cover that
column. Test 8 (added in rev4) is the SCAN SCOPE GATE — it asserts that
ANGLE_SOURCE_FILES itself stays complete by enumerating context files
and requiring each be either scanned or explicitly listed as
non-emitting. Origin: Audit Surprise S2.
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
# Counts by prefix make additions explicit and surface drift early.
# Adding a detector requires updating these counts, which forces a
# deliberate decision rather than silently bumping a magic number.
# Prefix scheme (rev4): D = dimensional Narrative Angles v2 detectors
# (D1–D50, with D41 included though disabled); P = primordial matchup
# detectors from narrative_angles_v1; B = bye-week context detectors
# from bye_week_context_v1; R = league-rules context detectors.
# ---------------------------------------------------------------------------
def test_category_to_detector_includes_audit_anchors() -> None:
    assert CATEGORY_TO_DETECTOR["PLAYER_BOOM_BUST"] == "D4"
    assert CATEGORY_TO_DETECTOR["SCORING_MOMENTUM_IN_STREAK"] == "D49"
    by_prefix: dict[str, int] = {}
    for v in CATEGORY_TO_DETECTOR.values():
        by_prefix[v[0]] = by_prefix.get(v[0], 0) + 1
    assert by_prefix == {"D": 50, "P": 7, "B": 3, "R": 1}


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
    "src/squadvault/core/recaps/context/narrative_angles_v1.py",
    "src/squadvault/core/recaps/context/bye_week_context_v1.py",
    "src/squadvault/core/recaps/context/league_rules_context_v1.py",
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


# ---------------------------------------------------------------------------
# Test 6 — prompt_text populates when supplied (Migration 0009 / Finding 2)
#
# Confirms the new prompt_text column round-trips a non-trivial assembled
# prompt — including all eight user-prompt block headers — through the
# audit write path. The prompt body here mirrors the structure
# _build_user_prompt produces in creative_layer_v1; the test does not
# call the LLM but does exercise the full INSERT path against the
# real schema.
# ---------------------------------------------------------------------------
_ASSEMBLED_PROMPT_FIXTURE = (
    "League: 70985 | Season: 2025 | Week 7\n"
    "EAL directive: HIGH_CONFIDENCE_ALLOWED — Use confident, declarative tone.\n"
    "\n"
    "=== SEASON CONTEXT (standings, streaks, scoring) ===\n"
    "Standings: ...\n"
    "\n"
    "=== LEAGUE HISTORY (all-time records, cross-season — REFERENCE THIS) ===\n"
    "All-time high: ...\n"
    "\n"
    "=== NARRATIVE ANGLES (detected story hooks — USE THESE) ===\n"
    "PLAYER_BOOM_BUST: ...\n"
    "\n"
    "=== WRITER ROOM (scoring deltas, FAAB spending) ===\n"
    "FAAB: $20 on Watson\n"
    "\n"
    "=== PLAYER HIGHLIGHTS (individual player performances — USE THESE) ===\n"
    "QB1: 28.4 pts\n"
    "\n"
    "=== VERIFIED FACTS (canonical, authoritative — these are your source of truth) ===\n"
    "- Franchise A defeated Franchise B 142.3 to 118.7\n"
    "\n"
    "=== VERIFICATION CORRECTIONS (your previous draft was rejected) ===\n"
    "- ERROR: ... CORRECTION: ...\n"
    "\n"
    "Write the recap now."
)


def test_maybe_capture_attempt_writes_prompt_text(
    db_path: str, audit_env: None
) -> None:
    maybe_capture_attempt(
        db_path,
        league_id="70985",
        season=2025,
        week_index=7,
        attempt=2,
        all_angles=[_make_angle("PLAYER_BOOM_BUST")],
        budgeted=[_make_angle("PLAYER_BOOM_BUST")],
        narrative_angles_text="PLAYER_BOOM_BUST: ...",
        narrative_draft="Draft prose here.",
        verification_result=_make_verification_result(passed=True),
        prompt_text=_ASSEMBLED_PROMPT_FIXTURE,
    )

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT prompt_text, length(prompt_text) FROM prompt_audit"
        ).fetchall()
    finally:
        con.close()

    assert len(rows) == 1
    captured_prompt, captured_len = rows[0]
    assert captured_prompt == _ASSEMBLED_PROMPT_FIXTURE
    assert captured_len == len(_ASSEMBLED_PROMPT_FIXTURE)
    # All eight assembled block headers must round-trip — this is the
    # observability guarantee the column exists to provide.
    for header in (
        "League: 70985 | Season: 2025 | Week 7",
        "=== SEASON CONTEXT",
        "=== LEAGUE HISTORY",
        "=== NARRATIVE ANGLES",
        "=== WRITER ROOM",
        "=== PLAYER HIGHLIGHTS",
        "=== VERIFIED FACTS",
        "=== VERIFICATION CORRECTIONS",
    ):
        assert header in captured_prompt


# ---------------------------------------------------------------------------
# Test 7 — prompt_text default-empty backward-compat
#
# Confirms callers that omit prompt_text (the kw-only param defaults to
# "") still write a valid row. Two assertions: (a) the omitted-call
# write succeeds, and (b) readers see an empty string, not a NULL —
# the schema is NOT NULL DEFAULT '' to mirror the existing TEXT column
# convention.
# ---------------------------------------------------------------------------
def test_maybe_capture_attempt_default_prompt_text_empty(
    db_path: str, audit_env: None
) -> None:
    # Legacy-style call: prompt_text omitted entirely.
    maybe_capture_attempt(
        db_path,
        league_id="70985",
        season=2025,
        week_index=8,
        attempt=1,
        all_angles=[_make_angle("PLAYER_BOOM_BUST")],
        budgeted=[],
        narrative_angles_text="",
        narrative_draft="",
        verification_result=_make_verification_result(passed=True),
    )

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT prompt_text, prompt_text IS NULL FROM prompt_audit"
        ).fetchall()
    finally:
        con.close()

    assert rows == [("", 0)]


# ---------------------------------------------------------------------------
# Test 8 — SCAN SCOPE GATE.
#
# The drift detector test (Test 5) only catches missing CATEGORY_TO_DETECTOR
# entries among files in ANGLE_SOURCE_FILES. If a new detector file is added
# to core/recaps/context/ but not added to ANGLE_SOURCE_FILES, the drift
# test scans nothing and silently misses the new categories.
#
# This test enumerates context files and asserts each is either scanned by
# the drift detector or explicitly listed as a non-emitting context module.
# Adding a new detector file requires updating one of the two lists, which
# forces a deliberate decision.
#
# Origin: Audit Surprise S2 (drift-detector scope gap).
# ---------------------------------------------------------------------------
_NON_EMITTING_CONTEXT_MODULES: set[str] = {
    "__init__.py",
    "season_context_v1.py",
    "league_history_v1.py",
    "player_week_context_v1.py",
    "writer_room_context_v1.py",
}


def test_drift_scan_covers_all_context_files() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    context_dir = repo_root / "src/squadvault/core/recaps/context"
    actual_files = {p.name for p in context_dir.glob("*.py")}

    scanned = {Path(p).name for p in ANGLE_SOURCE_FILES}
    accounted_for = scanned | _NON_EMITTING_CONTEXT_MODULES

    unaccounted = sorted(actual_files - accounted_for)
    assert not unaccounted, (
        f"Context files exist that are neither in ANGLE_SOURCE_FILES nor in "
        f"_NON_EMITTING_CONTEXT_MODULES: {unaccounted}. "
        f"Add to one or the other."
    )

    stale_scanned = sorted(scanned - actual_files)
    stale_non_emitting = sorted(
        _NON_EMITTING_CONTEXT_MODULES - actual_files - {"__init__.py"}
    )
    assert not stale_scanned, (
        f"ANGLE_SOURCE_FILES references missing files: {stale_scanned}"
    )
    assert not stale_non_emitting, (
        f"_NON_EMITTING_CONTEXT_MODULES references missing files: "
        f"{stale_non_emitting}"
    )
