"""Tests for Defect 5: migration CLI and pending-migration helper.

Verifies that:
- apply_migrations is idempotent
- pending_migrations correctly identifies unapplied migrations
- The migrate subcommand is registered in recap.py
"""
from __future__ import annotations

import os
import sqlite3

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "squadvault", "core", "storage", "schema.sql"
)


def _fresh_db(tmp_path, name="test.sqlite"):
    """Create a fresh DB from schema.sql (simulates init_and_migrate)."""
    db_path = str(tmp_path / name)
    schema_sql = open(SCHEMA_PATH, encoding="utf-8").read()
    con = sqlite3.connect(db_path)
    con.executescript(schema_sql)
    con.close()
    return db_path


class TestApplyMigrationsIdempotent:
    """apply_migrations must be safe to call multiple times."""

    def test_double_apply_returns_empty(self, tmp_path):
        from squadvault.core.storage.migrate import apply_migrations
        db_path = _fresh_db(tmp_path)

        first = apply_migrations(db_path)
        second = apply_migrations(db_path)
        # Second call should apply nothing (all already tracked)
        assert second == [], f"Expected empty on re-apply, got {second}"

    def test_pending_empty_after_apply(self, tmp_path):
        from squadvault.core.storage.migrate import apply_migrations, pending_migrations
        db_path = _fresh_db(tmp_path)

        apply_migrations(db_path)
        pend = pending_migrations(db_path)
        assert pend == [], f"Expected no pending after apply, got {pend}"


class TestPendingMigrations:
    """pending_migrations should detect unapplied migrations."""

    def test_fresh_db_without_tracking_table(self, tmp_path):
        """A DB with no _schema_migrations table should report all migrations pending."""
        from squadvault.core.storage.migrate import _discover_migrations, pending_migrations
        db_path = str(tmp_path / "bare.sqlite")
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE dummy (id INTEGER)")
        con.close()

        pend = pending_migrations(db_path)
        all_versions = [v for v, _ in _discover_migrations()]
        assert pend == all_versions

    def test_partially_applied(self, tmp_path):
        """If only some migrations are applied, the rest should be pending."""
        from squadvault.core.storage.migrate import _discover_migrations, pending_migrations
        db_path = str(tmp_path / "partial.sqlite")
        con = sqlite3.connect(db_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)
        # Mark only the first migration as applied
        all_migrations = _discover_migrations()
        if all_migrations:
            con.execute(
                "INSERT INTO _schema_migrations (version) VALUES (?)",
                (all_migrations[0][0],),
            )
        con.commit()
        con.close()

        pend = pending_migrations(db_path)
        expected = [v for v, _ in all_migrations[1:]]
        assert pend == expected


class TestMigrateSubcommand:
    """The migrate subcommand should be registered in recap.py."""

    def test_subcommand_exists(self):
        """recap.py build_parser should accept 'migrate' command."""
        import importlib
        # Import recap.py as a module
        recap_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "recap.py"
        )
        spec = importlib.util.spec_from_file_location("recap_cli", recap_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        parser = mod.build_parser()
        # Should not raise on 'migrate --db foo'
        args = parser.parse_args(["migrate", "--db", "/tmp/test.db"])
        assert args.cmd == "migrate"
        assert args.db == "/tmp/test.db"
        assert hasattr(args, "fn"), "migrate subparser missing fn default"
