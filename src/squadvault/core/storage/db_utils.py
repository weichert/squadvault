"""Shared database utility functions.

Canonical location for helpers that were previously duplicated across modules.
"""
from __future__ import annotations

import sqlite3
from typing import Any


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return set of column names for a given table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(r[1]) for r in rows}


def norm_id(raw: Any) -> str:
    """Normalize an ID: strip whitespace, strip leading zeros from numeric strings.

    Returns empty string for None or whitespace-only input.
    """
    s = "" if raw is None else str(raw).strip()
    if not s:
        return ""
    if s.isdigit():
        return s.lstrip("0") or "0"
    return s
