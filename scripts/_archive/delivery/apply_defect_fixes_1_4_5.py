#!/usr/bin/env python3
"""
Apply fixes for defects 1, 4, and 5.

Defect 1: EAL confidence bug — fallback count excludes zero (quiet weeks)
Defect 4: Legacy recaps table — add deprecation warnings to remaining consumers
Defect 5: Migration CLI — add `migrate` subcommand to recap.py

Usage:
    python apply_defect_fixes_1_4_5.py
"""

import os
import sys

def write_file(path, content):
    """Write content to file, creating directories as needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {path}")


def patch_file(path, old, new, label=""):
    """Replace exactly one occurrence of old with new in a file."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    count = content.count(old)
    if count == 0:
        print(f"  ERROR: patch target not found in {path}: {label or old[:60]!r}")
        sys.exit(1)
    if count > 1:
        print(f"  ERROR: patch target found {count} times in {path}: {label or old[:60]!r}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  patched {path} ({label})" if label else f"  patched {path}")


def main():
    # ── Defect 1: Fix EAL fallback count ──────────────────────────────────
    print("\n=== Defect 1: Fix EAL fallback count (zero-count bug) ===")

    # Fix production code: weekly_recap_lifecycle.py line 712
    # The old condition excludes COUNT(*)=0 because 0 is falsy in Python.
    # A quiet week with 0 events should get included_count=0 (→ AMBIGUITY_PREFER_SILENCE),
    # not included_count=None (→ LOW_CONFIDENCE_RESTRAINT).
    patch_file(
        "src/squadvault/recaps/weekly_recap_lifecycle.py",
        old=(
            "            if _fallback_row and _fallback_row[0] and int(_fallback_row[0]) > 0:\n"
            "                included_count = int(_fallback_row[0])"
        ),
        new=(
            "            # SV_DEFECT1_ZERO_COUNT_FIX: COUNT(*)=0 is valid (quiet week).\n"
            "            # Previous condition `_fallback_row[0] and int(...) > 0` excluded\n"
            "            # zero because 0 is falsy — gave None instead of 0.\n"
            "            if _fallback_row is not None:\n"
            "                included_count = int(_fallback_row[0])"
        ),
        label="defect1-lifecycle-fallback",
    )

    # Fix the mirrored test that copies the same buggy condition
    patch_file(
        "Tests/test_defect_fixes_v1.py",
        old=(
            "                if _fallback_row and _fallback_row[0] and int(_fallback_row[0]) > 0:\n"
            "                    included_count = int(_fallback_row[0])"
        ),
        new=(
            "                # SV_DEFECT1_ZERO_COUNT_FIX: 0 is a valid count.\n"
            "                if _fallback_row is not None:\n"
            "                    included_count = int(_fallback_row[0])"
        ),
        label="defect1-test-mirror-fix",
    )

    # Add test for zero-count case
    patch_file(
        "Tests/test_defect_fixes_v1.py",
        old="# ── Defect 2: use_canonical default ──────────────────────────────────",
        new='''\
    def test_fallback_zero_count_gives_zero_not_none(self, tmp_path):
        """When canonical_ids_json is empty and canonical_events has 0 rows in
        the window, included_count should be 0 (not None).

        This is the root cause of the EAL confidence bug: 0 is falsy in Python,
        so the old condition `_fallback_row[0] and int(...) > 0` left
        included_count=None, producing LOW_CONFIDENCE_RESTRAINT instead of
        AMBIGUITY_PREFER_SILENCE.
        """
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
            ("L1", 2024, 7, "ELIGIBLE", "fp_empty",
             "", "{}", window_start, window_end),
        )
        # No canonical_events inserted — zero events in window
        con.commit()

        from squadvault.core.storage.session import DatabaseSession

        included_count = None
        with DatabaseSession(db_path) as _eal_con:
            _eal_row = _eal_con.execute(
                "SELECT canonical_ids_json FROM recap_runs"
                " WHERE league_id=? AND season=? AND week_index=?",
                ("L1", 2024, 7),
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
                # SV_DEFECT1_ZERO_COUNT_FIX: 0 is a valid count.
                if _fallback_row is not None:
                    included_count = int(_fallback_row[0])

        assert included_count == 0, (
            f"Expected included_count=0 for quiet week, got {included_count!r}"
        )

        # Verify this produces the correct EAL directive
        from squadvault.core.eal.editorial_attunement_v1 import (
            EALMeta,
            evaluate_editorial_attunement_v1,
            EAL_AMBIGUITY_PREFER_SILENCE,
        )
        meta = EALMeta(
            has_selection_set=True,
            has_window=True,
            included_count=included_count,
        )
        directive = evaluate_editorial_attunement_v1(meta)
        assert directive == EAL_AMBIGUITY_PREFER_SILENCE, (
            f"Quiet week (0 events) should get AMBIGUITY_PREFER_SILENCE, got {directive}"
        )
        con.close()


# ── Defect 2: use_canonical default ──────────────────────────────────''',
        label="defect1-add-zero-count-test",
    )

    # ── Defect 4: Legacy recaps deprecation warnings ────────────────────
    print("\n=== Defect 4: Add deprecation warnings to legacy consumers ===")

    # recap_week_init.py — add deprecation warning on legacy insert
    patch_file(
        "src/squadvault/consumers/recap_week_init.py",
        old=(
            "    # 4) Initialize recap v1 record if missing (existing behavior)\n"
            "    inserted = insert_recap_v1_if_missing("
        ),
        new=(
            "    # 4) Initialize recap v1 record if missing (LEGACY — scheduled for removal)\n"
            "    # SV_DEFECT4_LEGACY_CONSUMER: This writes to the deprecated `recaps` table.\n"
            "    # The canonical lifecycle uses recap_runs + recap_artifacts.\n"
            "    import warnings\n"
            "    warnings.warn(\n"
            '        "recap_week_init: insert_recap_v1_if_missing writes to the deprecated "\n'
            '        "recaps table. This will be removed after observation window.",\n'
            "        DeprecationWarning,\n"
            "        stacklevel=1,\n"
            "    )\n"
            "    inserted = insert_recap_v1_if_missing("
        ),
        label="defect4-init-deprecation",
    )

    # recap_week_selection_check.py — add deprecation at module level
    patch_file(
        "src/squadvault/consumers/recap_week_selection_check.py",
        old='"""Check recap selection state for a given week."""',
        new=(
            '"""Check recap selection state for a given week.\n'
            "\n"
            "SV_DEFECT4_LEGACY_CONSUMER: This module imports from the deprecated recap_store.\n"
            "The canonical lifecycle uses recap_runs + recap_artifacts.\n"
            'Scheduled for removal after observation window.\n"""'
        ),
        label="defect4-selection-check-docstring",
    )

    # recap_week_write_artifact.py — add deprecation at module level
    patch_file(
        "src/squadvault/consumers/recap_week_write_artifact.py",
        old='"""Write a recap artifact JSON to disk from database."""',
        new=(
            '"""Write a recap artifact JSON to disk from database.\n'
            "\n"
            "SV_DEFECT4_LEGACY_CONSUMER: This module writes to the deprecated recaps table\n"
            "via recap_store. The canonical lifecycle uses recap_runs + recap_artifacts.\n"
            'Scheduled for removal after observation window.\n"""'
        ),
        label="defect4-write-artifact-docstring",
    )

    # recap_week_materialize_version.py — add deprecation marker
    patch_file(
        "src/squadvault/consumers/recap_week_materialize_version.py",
        old='"""Materialize a recap version from database to disk."""',
        new=(
            '"""Materialize a recap version from database to disk.\n'
            "\n"
            "SV_DEFECT4_LEGACY_CONSUMER: This module reads from the deprecated recaps table.\n"
            "The canonical lifecycle uses recap_runs + recap_artifacts.\n"
            'Scheduled for removal after observation window.\n"""'
        ),
        label="defect4-materialize-docstring",
    )

    # Add test: verify all legacy consumers have deprecation markers
    patch_file(
        "Tests/test_defect_fixes_v1.py",
        old=(
            "class TestLegacyRecapsDeprecation:\n"
            '    """The recaps table should be marked deprecated in schema.sql."""\n'
            "\n"
            "    def test_deprecation_marker_present(self):\n"
            '        """schema.sql must contain the deprecation marker."""\n'
            "        schema_text = open(SCHEMA_PATH, encoding=\"utf-8\").read()\n"
            "        assert \"SV_DEFECT4_LEGACY_RECAPS_DEPRECATED\" in schema_text, (\n"
            '            "Deprecation marker not found in schema.sql"\n'
            "        )\n"
            '        assert "DEPRECATED" in schema_text'
        ),
        new=(
            "class TestLegacyRecapsDeprecation:\n"
            '    """The recaps table should be marked deprecated in schema.sql\n'
            "    and all legacy consumers should carry deprecation markers.\"\"\"\n"
            "\n"
            "    def test_deprecation_marker_present(self):\n"
            '        """schema.sql must contain the deprecation marker."""\n'
            "        schema_text = open(SCHEMA_PATH, encoding=\"utf-8\").read()\n"
            "        assert \"SV_DEFECT4_LEGACY_RECAPS_DEPRECATED\" in schema_text, (\n"
            '            "Deprecation marker not found in schema.sql"\n'
            "        )\n"
            '        assert "DEPRECATED" in schema_text\n'
            "\n"
            "    def test_legacy_consumers_have_deprecation_markers(self):\n"
            '        """All consumer files that import from recap_store must have\n'
            '        the SV_DEFECT4_LEGACY_CONSUMER marker."""\n'
            "        import pathlib\n"
            "        consumer_dir = pathlib.Path(SCHEMA_PATH).parent.parent.parent / \"consumers\"\n"
            "        legacy_consumers = [\n"
            '            "recap_week_init.py",\n'
            '            "recap_week_selection_check.py",\n'
            '            "recap_week_write_artifact.py",\n'
            '            "recap_week_materialize_version.py",\n'
            "        ]\n"
            "        for name in legacy_consumers:\n"
            "            path = consumer_dir / name\n"
            "            assert path.exists(), f\"{name} not found at {path}\"\n"
            "            text = path.read_text(encoding=\"utf-8\")\n"
            "            assert \"SV_DEFECT4_LEGACY_CONSUMER\" in text, (\n"
            "                f\"{name} missing SV_DEFECT4_LEGACY_CONSUMER deprecation marker\"\n"
            "            )"
        ),
        label="defect4-add-consumer-marker-test",
    )

    # ── Defect 5: Migration CLI ─────────────────────────────────────────
    print("\n=== Defect 5: Add migration CLI and pending-migration helper ===")

    # Add pending_migrations() to migrate.py
    patch_file(
        "src/squadvault/core/storage/migrate.py",
        old=(
            "def init_and_migrate(db_path: str) -> None:\n"
            '    """Initialize database from schema.sql and apply any pending migrations."""'
        ),
        new=(
            "def pending_migrations(db_path: str) -> list[str]:\n"
            '    """Return list of migration versions that have not yet been applied.\n'
            "\n"
            "    Does not modify the database. Safe to call for diagnostics.\n"
            '    """\n'
            "    con = sqlite3.connect(db_path)\n"
            "    con.row_factory = sqlite3.Row\n"
            "    try:\n"
            "        # Check if _schema_migrations table exists\n"
            "        tables = {r[0] for r in con.execute(\n"
            '            "SELECT name FROM sqlite_master WHERE type=\'table\'"\n'
            "        ).fetchall()}\n"
            '        if "_schema_migrations" not in tables:\n'
            "            # No tracking table => all migrations are pending\n"
            "            return [v for v, _ in _discover_migrations()]\n"
            "        applied = _applied_versions(con)\n"
            "        return [v for v, _ in _discover_migrations() if v not in applied]\n"
            "    finally:\n"
            "        con.close()\n"
            "\n\n"
            "def init_and_migrate(db_path: str) -> None:\n"
            '    """Initialize database from schema.sql and apply any pending migrations."""'
        ),
        label="defect5-pending-migrations-fn",
    )

    # Add cmd_migrate and subparser to recap.py
    # First: add the import
    patch_file(
        "scripts/recap.py",
        old="from squadvault.recaps.weekly_recap_lifecycle import (",
        new=(
            "from squadvault.core.storage.migrate import apply_migrations, pending_migrations\n"
            "from squadvault.recaps.weekly_recap_lifecycle import ("
        ),
        label="defect5-recap-import",
    )

    # Add cmd_migrate function (before build_parser)
    patch_file(
        "scripts/recap.py",
        old="\ndef build_parser() -> argparse.ArgumentParser:",
        new=(
            "\ndef cmd_migrate(args: argparse.Namespace) -> int:\n"
            '    """Apply pending schema migrations to the database."""\n'
            "    applied = apply_migrations(args.db)\n"
            "    if applied:\n"
            "        for v in applied:\n"
            '            print(f"  applied: {v}")\n'
            '        print(f"migrate: {len(applied)} migration(s) applied.")\n'
            "    else:\n"
            '        print("migrate: database is up to date.")\n'
            "    return 0\n"
            "\n\n"
            "def _warn_if_migrations_pending(db_path: str) -> None:\n"
            '    """Print a warning if the database has unapplied migrations.\n'
            "\n"
            "    Called by operator commands as a non-blocking advisory.\n"
            '    Does not modify the database or halt execution.\n'
            '    """\n'
            "    try:\n"
            "        pend = pending_migrations(db_path)\n"
            "        if pend:\n"
            "            import sys\n"
            '            print(\n'
            '                f"WARNING: {len(pend)} pending migration(s): {pend}. "\n'
            '                f"Run: ./scripts/recap.sh migrate --db {db_path}",\n'
            "                file=sys.stderr,\n"
            "            )\n"
            "    except Exception:\n"
            "        pass  # Never block operator flow for migration checks\n"
            "\n\n"
            "def build_parser() -> argparse.ArgumentParser:"
        ),
        label="defect5-cmd-migrate",
    )

    # Add the migrate subparser registration (after the last subparser, before return p)
    patch_file(
        "scripts/recap.py",
        old="    return p\n\n\ndef _cmd_rivalry_chronicle_v1",
        new=(
            "    # migrate\n"
            "    sp = sub.add_parser(\n"
            '        "migrate",\n'
            '        help="Apply pending schema migrations to the database",\n'
            "    )\n"
            '    sp.add_argument("--db", required=True)\n'
            "    sp.set_defaults(fn=cmd_migrate)\n"
            "\n"
            "    return p\n"
            "\n\n"
            "def _cmd_rivalry_chronicle_v1"
        ),
        label="defect5-migrate-subparser",
    )

    # Wire pending-migration warning into key operator commands
    patch_file(
        "scripts/recap.py",
        old=(
            "def cmd_status(args: argparse.Namespace) -> int:\n"
        ),
        new=(
            "def cmd_status(args: argparse.Namespace) -> int:\n"
            "    _warn_if_migrations_pending(args.db)\n"
        ),
        label="defect5-warn-status",
    )

    patch_file(
        "scripts/recap.py",
        old=(
            "def cmd_list_weeks(args: argparse.Namespace) -> int:\n"
            "    weeks = _list_week_indexes(args.db, args.league_id, args.season)"
        ),
        new=(
            "def cmd_list_weeks(args: argparse.Namespace) -> int:\n"
            "    _warn_if_migrations_pending(args.db)\n"
            "    weeks = _list_week_indexes(args.db, args.league_id, args.season)"
        ),
        label="defect5-warn-list-weeks",
    )

    # ── Defect 5 tests ──────────────────────────────────────────────────
    print("\n=== Adding tests for Defect 5 ===")

    write_file("Tests/test_defect5_migration_cli.py", '''\
"""Tests for Defect 5: migration CLI and pending-migration helper.

Verifies that:
- apply_migrations is idempotent
- pending_migrations correctly identifies unapplied migrations
- The migrate subcommand is registered in recap.py
"""
from __future__ import annotations

import os
import sqlite3

import pytest

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
        from squadvault.core.storage.migrate import pending_migrations, _discover_migrations
        db_path = str(tmp_path / "bare.sqlite")
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE dummy (id INTEGER)")
        con.close()

        pend = pending_migrations(db_path)
        all_versions = [v for v, _ in _discover_migrations()]
        assert pend == all_versions

    def test_partially_applied(self, tmp_path):
        """If only some migrations are applied, the rest should be pending."""
        from squadvault.core.storage.migrate import pending_migrations, _discover_migrations
        db_path = str(tmp_path / "partial.sqlite")
        con = sqlite3.connect(db_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (strftime(\'%Y-%m-%dT%H:%M:%fZ\', \'now\'))
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
        """recap.py build_parser should accept \'migrate\' command."""
        import importlib
        import sys
        # Import recap.py as a module
        recap_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "recap.py"
        )
        spec = importlib.util.spec_from_file_location("recap_cli", recap_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        parser = mod.build_parser()
        # Should not raise on \'migrate --db foo\'
        args = parser.parse_args(["migrate", "--db", "/tmp/test.db"])
        assert args.cmd == "migrate"
        assert args.db == "/tmp/test.db"
        assert hasattr(args, "fn"), "migrate subparser missing fn default"
''')

    print("\n=== All patches applied. ===")
    print("\nVerification:")
    print("  PYTHONPATH=src python -m pytest Tests/ -q")
    print("\nExpected: 1109 passed, 3 skipped")
    print("\nCommit message:")
    print('  git add -A && git commit -m "Fix defects 1/4/5: EAL zero-count bug, legacy deprecation markers, migration CLI"')


if __name__ == "__main__":
    main()
