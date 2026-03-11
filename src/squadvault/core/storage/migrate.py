"""Schema migration framework for SquadVault.

Applies versioned SQL migrations in order. Each migration runs once
and is tracked in a _schema_migrations table.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional


MIGRATIONS_DIR = Path(__file__).parent / "migrations"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _ensure_migrations_table(con: sqlite3.Connection) -> None:
    """Create the migrations tracking table if it doesn't exist."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS _schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
    """)
    con.commit()


def _applied_versions(con: sqlite3.Connection) -> set[str]:
    """Return set of already-applied migration versions."""
    rows = con.execute("SELECT version FROM _schema_migrations").fetchall()
    return {str(r[0]) for r in rows}


def _discover_migrations() -> list[tuple[str, str]]:
    """Discover .sql migration files, sorted by filename.

    Returns list of (version, sql_text) tuples.
    """
    if not MIGRATIONS_DIR.is_dir():
        return []
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    result = []
    for f in files:
        version = f.stem  # e.g., "001_add_column"
        sql = f.read_text(encoding="utf-8")
        result.append((version, sql))
    return result


def apply_migrations(db_path: str) -> list[str]:
    """Apply all pending migrations to the database.

    Returns list of newly applied version strings.
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        _ensure_migrations_table(con)
        applied = _applied_versions(con)
        migrations = _discover_migrations()

        newly_applied = []
        for version, sql in migrations:
            if version in applied:
                continue
            con.executescript(sql)
            con.execute(
                "INSERT INTO _schema_migrations (version) VALUES (?)",
                (version,),
            )
            con.commit()
            newly_applied.append(version)

        return newly_applied
    finally:
        con.close()


def init_and_migrate(db_path: str) -> None:
    """Initialize database from schema.sql and apply any pending migrations."""
    con = sqlite3.connect(db_path)
    try:
        if SCHEMA_PATH.exists():
            con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            con.commit()
    finally:
        con.close()

    apply_migrations(db_path)
