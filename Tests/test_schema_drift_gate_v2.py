"""Schema drift gate: schema.sql must structurally match the fixture DB.

This test prevents the schema.sql and the fixture DB from silently diverging.
Any column, table, or index mismatch is a hard failure.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)
FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "ci_squadvault.sqlite"
)


def _tables(con: sqlite3.Connection) -> list[str]:
    """Return sorted list of user tables."""
    return sorted([
        r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ])


def _columns(con: sqlite3.Connection, table: str) -> list[tuple[str, str]]:
    """Return sorted list of (name, type) for a table."""
    return sorted([
        (r[1], r[2]) for r in con.execute(f"PRAGMA table_info({table})").fetchall()
    ])


def _column_names(con: sqlite3.Connection, table: str) -> set[str]:
    """Return set of column names for a table."""
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}


@pytest.fixture
def schema_db(tmp_path):
    """Create a fresh DB from schema.sql."""
    db_path = str(tmp_path / "fresh.sqlite")
    schema_sql = open(SCHEMA_PATH).read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


class TestSchemaFixtureDrift:
    """schema.sql must produce the same structure as the fixture DB."""

    def test_schema_file_exists(self):
        """schema.sql must exist."""
        assert os.path.exists(SCHEMA_PATH), f"schema.sql not found at {SCHEMA_PATH}"

    def test_fixture_file_exists(self):
        """Fixture DB must exist."""
        assert os.path.exists(FIXTURE_PATH), f"Fixture DB not found at {FIXTURE_PATH}"

    def test_same_tables(self, schema_db):
        """Both must define exactly the same set of tables."""
        s_con = sqlite3.connect(schema_db)
        f_con = sqlite3.connect(FIXTURE_PATH)

        s_tables = set(_tables(s_con))
        f_tables = set(_tables(f_con))

        only_schema = sorted(s_tables - f_tables)
        only_fixture = sorted(f_tables - s_tables)

        s_con.close()
        f_con.close()

        failures = []
        if only_schema:
            failures.append(f"Tables in schema.sql only: {only_schema}")
        if only_fixture:
            failures.append(f"Tables in fixture only: {only_fixture}")
        assert not failures, "\n".join(failures)

    def test_same_columns_per_table(self, schema_db):
        """Every shared table must have the same columns."""
        s_con = sqlite3.connect(schema_db)
        f_con = sqlite3.connect(FIXTURE_PATH)

        shared = sorted(set(_tables(s_con)) & set(_tables(f_con)))
        failures = []

        for t in shared:
            s_cols = _column_names(s_con, t)
            f_cols = _column_names(f_con, t)
            only_s = sorted(s_cols - f_cols)
            only_f = sorted(f_cols - s_cols)
            if only_s:
                failures.append(f"{t}: columns in schema.sql only: {only_s}")
            if only_f:
                failures.append(f"{t}: columns in fixture only: {only_f}")

        s_con.close()
        f_con.close()

        assert not failures, "Column drift detected:\n" + "\n".join(failures)


class TestFreshDbUsable:
    """A fresh DB created from schema.sql must support core operations."""

    def test_can_insert_memory_event(self, schema_db):
        """Memory event append must work on a fresh DB."""
        con = sqlite3.connect(schema_db)
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, "test", "e1", "MATCHUP_RESULT",
             "2024-10-01T00:00:00Z", "2024-10-01T00:00:00Z", '{}'),
        )
        con.commit()
        count = con.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
        con.close()
        assert count == 1

    def test_can_insert_recap_run(self, schema_db):
        """Recap run upsert must work on a fresh DB."""
        con = sqlite3.connect(schema_db)
        con.execute(
            """INSERT INTO recap_runs
               (league_id, season, week_index, state, selection_fingerprint,
                canonical_ids_json, counts_by_type_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 1, "ELIGIBLE", "fp1", "[]", "{}"),
        )
        con.commit()
        row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs WHERE league_id='L1'"
        ).fetchone()
        con.close()
        assert row is not None
        assert row[0] == "[]"

    def test_can_insert_recap_artifact(self, schema_db):
        """Recap artifact creation must work on a fresh DB."""
        con = sqlite3.connect(schema_db)
        con.execute(
            """INSERT INTO recap_artifacts
               (league_id, season, week_index, artifact_type, version, state,
                selection_fingerprint, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 1, "WEEKLY_RECAP", 1, "DRAFT", "fp1", "system"),
        )
        con.commit()
        count = con.execute("SELECT COUNT(*) FROM recap_artifacts").fetchone()[0]
        con.close()
        assert count == 1

    def test_can_insert_franchise_and_player(self, schema_db):
        """Directory inserts must work on a fresh DB."""
        con = sqlite3.connect(schema_db)
        con.execute(
            "INSERT INTO franchise_directory (league_id, season, franchise_id, name) VALUES (?,?,?,?)",
            ("L1", 2024, "F01", "Eagles"),
        )
        con.execute(
            "INSERT INTO player_directory (league_id, season, player_id, name) VALUES (?,?,?,?)",
            ("L1", 2024, "P01", "Joe Burrow"),
        )
        con.commit()
        f_count = con.execute("SELECT COUNT(*) FROM franchise_directory").fetchone()[0]
        p_count = con.execute("SELECT COUNT(*) FROM player_directory").fetchone()[0]
        con.close()
        assert f_count == 1
        assert p_count == 1

    def test_can_insert_recap_selection(self, schema_db):
        """Selection persistence must work on a fresh DB."""
        con = sqlite3.connect(schema_db)
        con.execute(
            """INSERT INTO recap_selections
               (league_id, season, week_index, window_mode, event_count, fingerprint, computed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 1, "LOCK_TO_LOCK", 5, "fp1", "2024-10-01T00:00:00Z"),
        )
        con.commit()
        count = con.execute("SELECT COUNT(*) FROM recap_selections").fetchone()[0]
        con.close()
        assert count == 1

    def test_canonical_ids_json_readable_for_eal(self, schema_db):
        """The EAL included_count fix reads canonical_ids_json — this must work on fresh DB."""
        import json
        con = sqlite3.connect(schema_db)
        ids = [1, 2, 3, 4, 5]
        con.execute(
            """INSERT INTO recap_runs
               (league_id, season, week_index, state, selection_fingerprint,
                canonical_ids_json, counts_by_type_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("L1", 2024, 1, "ELIGIBLE", "fp1", json.dumps(ids), "{}"),
        )
        con.commit()
        row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs WHERE league_id='L1' AND season=2024 AND week_index=1"
        ).fetchone()
        con.close()
        assert row is not None
        parsed = json.loads(row[0])
        assert parsed == ids
        assert len(parsed) == 5
