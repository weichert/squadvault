#!/usr/bin/env python3
"""Regenerate fixtures/ci_squadvault.sqlite from schema.sql + existing data.

Usage:
    python scripts/regenerate_fixture_db.py

Creates a fresh DB from schema.sql, copies all data from the existing
fixture DB, and replaces the fixture. Run after schema.sql changes.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "src" / "squadvault" / "core" / "storage" / "schema.sql"
FIXTURE_PATH = REPO_ROOT / "fixtures" / "ci_squadvault.sqlite"
BACKUP_PATH = REPO_ROOT / "fixtures" / "ci_squadvault.sqlite.bak"


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema.sql not found at {SCHEMA_PATH}")
        return 1

    if not FIXTURE_PATH.exists():
        print(f"ERROR: fixture DB not found at {FIXTURE_PATH}")
        return 1

    schema_sql = SCHEMA_PATH.read_text()

    shutil.copy2(FIXTURE_PATH, BACKUP_PATH)
    print(f"Backed up to {BACKUP_PATH}")

    old_con = sqlite3.connect(str(FIXTURE_PATH))
    old_tables = [
        r[0] for r in old_con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]

    new_path = str(FIXTURE_PATH) + ".new"
    if os.path.exists(new_path):
        os.remove(new_path)

    new_con = sqlite3.connect(new_path)
    new_con.executescript(schema_sql)

    new_tables = [
        r[0] for r in new_con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]
    print(f"Created fresh DB with {len(new_tables)} tables from schema.sql")

    copied = 0
    for table in old_tables:
        if table not in new_tables:
            print(f"  SKIP {table} (not in new schema)")
            continue

        new_cols = {
            r[1] for r in new_con.execute(f"PRAGMA table_info({table})").fetchall()
        }
        old_cols = [
            r[1] for r in old_con.execute(f"PRAGMA table_info({table})").fetchall()
        ]

        common = [c for c in old_cols if c in new_cols]
        if not common:
            continue

        cols_str = ", ".join(common)
        rows = old_con.execute(f"SELECT {cols_str} FROM {table}").fetchall()
        if rows:
            placeholders = ", ".join(["?"] * len(common))
            new_con.executemany(
                f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})",
                rows,
            )
            copied += len(rows)
            print(f"  {table}: {len(rows)} rows")

    new_con.commit()

    for table in new_tables:
        count = new_con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0 and table not in ("recap_verdicts",):
            print(f"  WARNING: {table} is empty")

    new_con.close()
    old_con.close()

    os.replace(new_path, str(FIXTURE_PATH))
    print(f"\nRegenerated {FIXTURE_PATH} ({copied} total rows)")
    print(f"Backup at {BACKUP_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
