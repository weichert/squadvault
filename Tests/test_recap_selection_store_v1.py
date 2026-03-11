"""Tests for squadvault.core.recaps.selection.recap_selection_store.

Covers: insert_selection_if_missing, get_stored_selection, is_stale,
idempotency, StoredSelection fields.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.selection.recap_selection_store import (
    StoredSelection,
    get_stored_selection,
    insert_selection_if_missing,
    is_stale,
)
from squadvault.core.recaps.selection.weekly_selection_v1 import SelectionResult
from squadvault.core.recaps.selection.weekly_windows_v1 import WeeklyWindow

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024
WEEK = 1


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


def _sel(week: int = WEEK, canonical_ids: list = None, fingerprint: str = "a" * 64) -> SelectionResult:
    """Build a SelectionResult for testing."""
    return SelectionResult(
        week_index=week,
        window=WeeklyWindow(
            mode="LOCK_TO_LOCK",
            week_index=week,
            window_start="2024-09-05T12:00:00Z",
            window_end="2024-09-12T12:00:00Z",
            start_lock="2024-09-05T12:00:00Z",
            next_lock="2024-09-12T12:00:00Z",
        ),
        canonical_ids=canonical_ids or ["fp_1", "fp_2"],
        counts_by_type={"TRANSACTION_TRADE": 2},
        fingerprint=fingerprint,
    )


class TestInsertAndGet:
    def test_insert_new(self, db):
        """Inserting a new selection returns True."""
        result = insert_selection_if_missing(db, LEAGUE, SEASON, _sel())
        assert result is True

    def test_get_after_insert(self, db):
        """Stored selection is retrievable after insert."""
        insert_selection_if_missing(db, LEAGUE, SEASON, _sel())
        stored = get_stored_selection(db, LEAGUE, SEASON, WEEK)
        assert stored is not None
        assert isinstance(stored, StoredSelection)
        assert stored.league_id == LEAGUE
        assert stored.season == SEASON
        assert stored.week_index == WEEK
        assert stored.fingerprint == "a" * 64
        assert stored.event_count == 2
        assert stored.window_mode == "LOCK_TO_LOCK"

    def test_get_nonexistent_returns_none(self, db):
        assert get_stored_selection(db, LEAGUE, SEASON, 99) is None

    def test_idempotent_insert(self, db):
        """Second insert for same week is ignored (returns False)."""
        insert_selection_if_missing(db, LEAGUE, SEASON, _sel())
        result = insert_selection_if_missing(db, LEAGUE, SEASON, _sel(fingerprint="b" * 64))
        assert result is False
        # Original fingerprint preserved
        stored = get_stored_selection(db, LEAGUE, SEASON, WEEK)
        assert stored.fingerprint == "a" * 64

    def test_different_weeks_independent(self, db):
        """Different weeks have independent selections."""
        insert_selection_if_missing(db, LEAGUE, SEASON, _sel(week=1, fingerprint="a" * 64))
        insert_selection_if_missing(db, LEAGUE, SEASON, _sel(week=2, fingerprint="b" * 64))
        s1 = get_stored_selection(db, LEAGUE, SEASON, 1)
        s2 = get_stored_selection(db, LEAGUE, SEASON, 2)
        assert s1.fingerprint == "a" * 64
        assert s2.fingerprint == "b" * 64


class TestIsStale:
    def test_none_stored_is_not_stale(self):
        """No stored selection is not considered stale."""
        assert is_stale(None, _sel()) is False

    def test_same_fingerprint_not_stale(self):
        stored = StoredSelection(
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            selection_version=1, window_mode="LOCK_TO_LOCK",
            window_start="2024-09-05T12:00:00Z", window_end="2024-09-12T12:00:00Z",
            event_count=2, fingerprint="a" * 64, computed_at="2024-10-01T00:00:00Z",
        )
        assert is_stale(stored, _sel(fingerprint="a" * 64)) is False

    def test_different_fingerprint_is_stale(self):
        stored = StoredSelection(
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            selection_version=1, window_mode="LOCK_TO_LOCK",
            window_start="2024-09-05T12:00:00Z", window_end="2024-09-12T12:00:00Z",
            event_count=2, fingerprint="a" * 64, computed_at="2024-10-01T00:00:00Z",
        )
        assert is_stale(stored, _sel(fingerprint="b" * 64)) is True


class TestStoredSelectionFrozen:
    def test_immutable(self):
        stored = StoredSelection(
            league_id=LEAGUE, season=SEASON, week_index=WEEK,
            selection_version=1, window_mode="LOCK_TO_LOCK",
            window_start=None, window_end=None,
            event_count=0, fingerprint="x" * 64, computed_at="2024-10-01T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            stored.fingerprint = "changed"
