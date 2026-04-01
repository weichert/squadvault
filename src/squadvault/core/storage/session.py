"""Consistent database connection lifecycle management.

Provides a thin context manager for sqlite3 connections.
Not an ORM. Not an abstraction layer. Just consistent open/commit/close.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseSession:
    """Thin wrapper: consistent connection lifecycle, nothing more.

    Usage:
        with DatabaseSession(db_path) as con:
            row = con.execute("SELECT ...").fetchone()
    """

    def __init__(self, db_path: str | Path):
        """Initialize with path to SQLite database."""
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        """Open connection with Row factory enabled."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit on success, close always."""
        if self._conn:
            if exc_type is None:
                self._conn.commit()
            self._conn.close()
            self._conn = None
        return False
