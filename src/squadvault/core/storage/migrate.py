"""Schema migration framework for SquadVault.

Applies versioned SQL migrations in order. Each migration runs once
and is tracked in a _schema_migrations table.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

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

    ADD COLUMN idempotency: SQLite has no `ALTER TABLE ADD COLUMN IF NOT
    EXISTS`. Migrations that add a column will fail with `duplicate
    column name` on a fresh install via `init_and_migrate`, because
    schema.sql (the canonical post-migration state) already created the
    column. The runner treats this specific error as "schema.sql has
    already satisfied this migration" — mark it applied and continue.
    This mirrors the spirit of `CREATE TABLE IF NOT EXISTS` used by
    earlier migrations to remain safe against schema.sql co-execution.
    Convention for future ADD COLUMN migrations: one ADD COLUMN per
    migration file (a multi-statement script that fails on its first
    ADD COLUMN will silently skip subsequent statements).
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
            try:
                con.executescript(sql)
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
                # ADD COLUMN already satisfied by schema.sql co-execution.
                # Mark applied so subsequent runs see it as done.
            con.execute(
                "INSERT INTO _schema_migrations (version) VALUES (?)",
                (version,),
            )
            con.commit()
            newly_applied.append(version)

        return newly_applied
    finally:
        con.close()


def pending_migrations(db_path: str) -> list[str]:
    """Return list of migration versions that have not yet been applied.

    Does not modify the database. Safe to call for diagnostics.
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        # Check if _schema_migrations table exists
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        if "_schema_migrations" not in tables:
            # No tracking table => all migrations are pending
            return [v for v, _ in _discover_migrations()]
        applied = _applied_versions(con)
        return [v for v, _ in _discover_migrations() if v not in applied]
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
