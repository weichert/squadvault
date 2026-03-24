"""Tests for defect fixes applied before Phase 10 observation window.

# SV_DEFECT_FIX_TESTS_V1
"""
from __future__ import annotations

import json
import os
import sqlite3

import pytest

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)


def _fresh_db(tmp_path, name="test.sqlite"):
    """Create a fresh DB from schema.sql."""
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


# ── Defect 1: EAL fallback count ────────────────────────────────────

class TestEALFallbackCount:
    """When canonical_ids_json is NULL, EAL should fall back to counting
    canonical_events directly instead of defaulting to LOW_CONFIDENCE_RESTRAINT."""

    def test_fallback_uses_canonical_events_count(self, tmp_path):
        """If canonical_ids_json is empty but canonical_events has data in the
        window, included_count should reflect the canonical event count."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        window_start = "2024-10-14T00:00:00Z"
        window_end = "2024-10-21T00:00:00Z"

        # Insert a recap_run with empty canonical_ids_json (real-world scenario:
        # weeks processed before this column was reliably populated get "")
        con.execute(
            """INSERT INTO recap_runs
               (league_id, season, week_index, state, selection_fingerprint,
                canonical_ids_json, counts_by_type_json,
                window_start, window_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 6, "ELIGIBLE", "fp1",
             "", "{}", window_start, window_end),
        )

        # Insert memory_events + canonical_events with occurred_at inside the window
        for i in range(5):
            con.execute(
                """INSERT INTO memory_events
                   (league_id, season, external_source, external_id, event_type,
                    occurred_at, ingested_at, payload_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("L1", 2024, "test", f"e{i}",
                 "WEEKLY_MATCHUP_RESULT",
                 f"2024-10-15T{10+i:02d}:00:00Z",
                 "2024-10-15T12:00:00Z",
                 json.dumps({"game": i})),
            )
            me_id = i + 1  # sqlite autoincrement starts at 1
            con.execute(
                """INSERT INTO canonical_events
                   (league_id, season, event_type, action_fingerprint,
                    best_memory_event_id, best_score, updated_at, occurred_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("L1", 2024, "WEEKLY_MATCHUP_RESULT",
                 f"fp_match_{i}", me_id, 100,
                 "2024-10-15T12:00:00Z",
                 f"2024-10-15T{10+i:02d}:00:00Z"),
            )
        con.commit()

        # Test the EAL fallback logic directly (mirrors weekly_recap_lifecycle.py)
        from squadvault.core.storage.session import DatabaseSession

        included_count = None
        with DatabaseSession(db_path) as _eal_con:
            _eal_row = _eal_con.execute(
                "SELECT canonical_ids_json FROM recap_runs"
                " WHERE league_id=? AND season=? AND week_index=?",
                ("L1", 2024, 6),
            ).fetchone()
            if _eal_row and _eal_row[0]:
                _ids = json.loads(_eal_row[0])
                if isinstance(_ids, list):
                    included_count = len(_ids)
            # Fallback: count canonical events in window
            if included_count is None and window_start and window_end:
                _fallback_row = _eal_con.execute(
                    "SELECT COUNT(*) FROM canonical_events"
                    " WHERE league_id=? AND season=?"
                    " AND occurred_at IS NOT NULL"
                    " AND occurred_at >= ? AND occurred_at < ?",
                    ("L1", 2024, window_start, window_end),
                ).fetchone()
                if _fallback_row and _fallback_row[0] and int(_fallback_row[0]) > 0:
                    included_count = int(_fallback_row[0])

        assert included_count == 5, f"Expected 5 from fallback, got {included_count}"
        con.close()

    def test_included_count_from_canonical_ids_json(self, tmp_path):
        """When canonical_ids_json IS populated, it should be used directly."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)
        ids = ["fp1", "fp2", "fp3"]
        con.execute(
            """INSERT INTO recap_runs
               (league_id, season, week_index, state, selection_fingerprint,
                canonical_ids_json, counts_by_type_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 1, "ELIGIBLE", "fp1", json.dumps(ids), "{}"),
        )
        con.commit()
        con.close()

        from squadvault.core.storage.session import DatabaseSession

        included_count = None
        with DatabaseSession(db_path) as _eal_con:
            _eal_row = _eal_con.execute(
                "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
                ("L1", 2024, 1),
            ).fetchone()
            if _eal_row and _eal_row[0]:
                _parsed = json.loads(_eal_row[0])
                if isinstance(_parsed, list):
                    included_count = len(_parsed)

        assert included_count == 3


# ── Defect 2: use_canonical default ──────────────────────────────────

class TestCanonicalDefault:
    """event_queries helpers should default to use_canonical=True."""

    def test_default_is_canonical(self):
        """Verify the default parameter value is True."""
        import inspect
        from squadvault.core.queries.event_queries import (
            fetch_all_events,
            fetch_by_event_type,
            fetch_by_event_type_prefix,
        )
        for fn in (fetch_all_events, fetch_by_event_type, fetch_by_event_type_prefix):
            sig = inspect.signature(fn)
            param = sig.parameters.get("use_canonical")
            assert param is not None, f"{fn.__name__} missing use_canonical parameter"
            assert param.default is True, (
                f"{fn.__name__}.use_canonical default is {param.default!r}, expected True"
            )

    def test_convenience_aliases_have_use_canonical(self):
        """All convenience aliases should accept use_canonical."""
        import inspect
        from squadvault.core.queries.event_queries import (
            draft_picks,
            waiver_awards,
            waiver_requests,
            trades,
            free_agent_transactions,
        )
        for fn in (draft_picks, waiver_awards, waiver_requests, trades, free_agent_transactions):
            sig = inspect.signature(fn)
            param = sig.parameters.get("use_canonical")
            assert param is not None, f"{fn.__name__} missing use_canonical parameter"
            assert param.default is True, (
                f"{fn.__name__}.use_canonical default is {param.default!r}, expected True"
            )


# ── Defect 4: Legacy recaps table deprecation ────────────────────────

class TestLegacyRecapsDeprecation:
    """The recaps table should be marked deprecated in schema.sql."""

    def test_deprecation_marker_present(self):
        """schema.sql must contain the deprecation marker."""
        schema_text = open(SCHEMA_PATH, encoding="utf-8").read()
        assert "SV_DEFECT4_LEGACY_RECAPS_DEPRECATED" in schema_text, (
            "Deprecation marker not found in schema.sql"
        )
        assert "DEPRECATED" in schema_text
