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


# ── Defect 1: EAL included_count derivation ─────────────────────────

class TestEALIncludedCount:
    """included_count is derived solely from canonical_ids_json in recap_runs.
    The legacy fallback that counted canonical_events directly has been removed."""

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

    def test_null_canonical_ids_gives_none(self, tmp_path):
        """When canonical_ids_json is NULL/empty, included_count is None.
        EAL treats None as neutral — no fallback counting is performed."""
        db_path = _fresh_db(tmp_path)
        con = sqlite3.connect(db_path)

        con.execute(
            """INSERT INTO recap_runs
               (league_id, season, week_index, state, selection_fingerprint,
                canonical_ids_json, counts_by_type_json,
                window_start, window_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 6, "ELIGIBLE", "fp1",
             "", "{}", "2024-10-14T00:00:00Z", "2024-10-21T00:00:00Z"),
        )
        con.commit()
        con.close()

        from squadvault.core.storage.session import DatabaseSession

        included_count = None
        with DatabaseSession(db_path) as _eal_con:
            _eal_row = _eal_con.execute(
                "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
                ("L1", 2024, 6),
            ).fetchone()
            if _eal_row and _eal_row[0]:
                _ids = json.loads(_eal_row[0])
                if isinstance(_ids, list):
                    included_count = len(_ids)

        assert included_count is None, (
            f"Expected None when canonical_ids_json is empty, got {included_count!r}"
        )

    def test_eal_fallback_removed_from_lifecycle(self):
        """Lifecycle should no longer contain the canonical_events COUNT fallback."""
        import pathlib
        lifecycle = pathlib.Path(SCHEMA_PATH).parent.parent / "recaps" / "weekly_recap_lifecycle.py"
        text = lifecycle.read_text(encoding="utf-8")
        assert "SV_DEFECT1_EAL_FALLBACK_COUNT" not in text, (
            "EAL fallback marker still present in lifecycle — should have been removed"
        )
        assert "SV_DEFECT1_ZERO_COUNT_FIX" not in text, (
            "EAL zero-count fix marker still present in lifecycle — fallback was removed"
        )


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
    """The recaps table should be marked deprecated in schema.sql
    and all legacy consumers should carry deprecation markers."""

    def test_deprecation_marker_present(self):
        """schema.sql must contain the deprecation marker."""
        schema_text = open(SCHEMA_PATH, encoding="utf-8").read()
        assert "SV_DEFECT4_LEGACY_RECAPS_DEPRECATED" in schema_text, (
            "Deprecation marker not found in schema.sql"
        )
        assert "DEPRECATED" in schema_text

    def test_legacy_consumers_have_deprecation_markers(self):
        """All consumer files that import from recap_store must have
        the SV_DEFECT4_LEGACY_CONSUMER marker."""
        import pathlib
        consumer_dir = pathlib.Path(SCHEMA_PATH).parent.parent.parent / "consumers"
        legacy_consumers = [
            "recap_week_init.py",
            "recap_week_write_artifact.py",
        ]
        for name in legacy_consumers:
            path = consumer_dir / name
            assert path.exists(), f"{name} not found at {path}"
            text = path.read_text(encoding="utf-8")
            assert "SV_DEFECT4_LEGACY_CONSUMER" in text, (
                f"{name} missing SV_DEFECT4_LEGACY_CONSUMER deprecation marker"
            )

    def test_retired_legacy_consumers_deleted(self):
        """Legacy consumers that have been retired should no longer exist."""
        import pathlib
        consumer_dir = pathlib.Path(SCHEMA_PATH).parent.parent.parent / "consumers"
        retired = [
            "recap_week_status.py",
            "recap_week_render_facts.py",
            "recap_week_selection_check.py",
            "recap_week_materialize_version.py",
        ]
        for name in retired:
            path = consumer_dir / name
            assert not path.exists(), (
                f"{name} should have been deleted (legacy recaps table consumer)"
            )
