#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("fixtures/ci_squadvault.sqlite")

LEAGUE_ID = "70985"
SEASON = 2024
WEEK_INDEX = 6

ARTIFACT_TYPE = "WEEKLY_RECAP"
STATE_APPROVED = "APPROVED"
STATE_DRAFT = "DRAFT"

TS_UTC = "2026-01-01T00:00:00Z"
CREATED_BY = "ci"
APPROVED_BY = "ci"

# Deterministic, short, ASCII-only. Critically includes required NAC header.
RENDERED_TEXT = (
    "# WEEKLY RECAP (CI FIXTURE)\n"
    "\n"
    "This is a deterministic seeded recap used to satisfy golden path export + NAC validation.\n"
    "\n"
    "## What happened (facts)\n"
    "- Fixture seed: league 70985, season 2024, week 06.\n"
    "- Timestamp is fixed: 2026-01-01T00:00:00Z.\n"
    "\n"
    "## Notes\n"
    "This content is intentionally minimal and stable.\n"
)

TABLE = "recap_artifacts"

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"ERROR: missing fixture DB: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE})").fetchall()]
        required = [
            "id",
            "league_id",
            "season",
            "week_index",
            "artifact_type",
            "version",
            "state",
            "selection_fingerprint",
            "rendered_text",
            "created_at",
            "created_by",
            "approved_at",
            "approved_by",
        ]
        missing = [c for c in required if c not in cols]
        if missing:
            raise SystemExit(
                "ERROR: recap_artifacts schema missing expected columns:\n"
                + "\n".join(f"- {m}" for m in missing)
                + f"\nFound cols: {cols}"
            )

        # Deterministic fingerprint derived from (type + key + rendered_text).
        fp_src = f"{ARTIFACT_TYPE}|{LEAGUE_ID}|{SEASON}|{WEEK_INDEX}|{RENDERED_TEXT}"
        selection_fingerprint = _sha256_hex(fp_src)

        rows = conn.execute(
            f"""
            SELECT id, version, state, selection_fingerprint, rendered_text
            FROM {TABLE}
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = ?
            ORDER BY version ASC, id ASC
            """,
            (LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE),
        ).fetchall()

        before_count = len(rows)
        before_states = [r["state"] for r in rows]
        before_max_version = max([int(r["version"]) for r in rows], default=0)

        changed = False
        chosen_id: Optional[int] = None
        chosen_version: Optional[int] = None

        approved_rows = [r for r in rows if r["state"] == STATE_APPROVED]

        if approved_rows:
            # Prefer highest approved version.
            r = approved_rows[-1]
            chosen_id = int(r["id"])
            chosen_version = int(r["version"])

            # Ensure required fields are correct + deterministic.
            cur_text = "" if r["rendered_text"] is None else str(r["rendered_text"])
            cur_fp = "" if r["selection_fingerprint"] is None else str(r["selection_fingerprint"])

            if cur_text != RENDERED_TEXT or cur_fp != selection_fingerprint:
                conn.execute(
                    f"""
                    UPDATE {TABLE}
                    SET rendered_text = ?,
                        selection_fingerprint = ?,
                        created_at = COALESCE(created_at, ?),
                        created_by = COALESCE(created_by, ?),
                        approved_at = COALESCE(approved_at, ?),
                        approved_by = COALESCE(approved_by, ?)
                    WHERE id = ?
                    """,
                    (
                        RENDERED_TEXT,
                        selection_fingerprint,
                        TS_UTC,
                        CREATED_BY,
                        TS_UTC,
                        APPROVED_BY,
                        chosen_id,
                    ),
                )
                changed = True

        elif rows:
            # Promote highest-version row to APPROVED and normalize content.
            r = rows[-1]
            chosen_id = int(r["id"])
            chosen_version = int(r["version"])

            conn.execute(
                f"""
                UPDATE {TABLE}
                SET state = ?,
                    rendered_text = ?,
                    selection_fingerprint = ?,
                    created_at = COALESCE(created_at, ?),
                    created_by = COALESCE(created_by, ?),
                    approved_at = ?,
                    approved_by = ?
                WHERE id = ?
                """,
                (
                    STATE_APPROVED,
                    RENDERED_TEXT,
                    selection_fingerprint,
                    TS_UTC,
                    CREATED_BY,
                    TS_UTC,
                    APPROVED_BY,
                    chosen_id,
                ),
            )
            changed = True

        else:
            # Insert deterministically at version=1.
            chosen_version = 1
            conn.execute(
                f"""
                INSERT INTO {TABLE} (
                    league_id, season, week_index, artifact_type,
                    version, state,
                    selection_fingerprint,
                    rendered_text,
                    created_at, created_by,
                    approved_at, approved_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    LEAGUE_ID,
                    SEASON,
                    WEEK_INDEX,
                    ARTIFACT_TYPE,
                    chosen_version,
                    STATE_APPROVED,
                    selection_fingerprint,
                    RENDERED_TEXT,
                    TS_UTC,
                    CREATED_BY,
                    TS_UTC,
                    APPROVED_BY,
                ),
            )
            chosen_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            changed = True

        conn.commit()

        post = conn.execute(
            f"""
            SELECT id, version, state,
                   LENGTH(COALESCE(rendered_text, '')) AS text_len,
                   selection_fingerprint
            FROM {TABLE}
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = ?
              AND state = ?
            ORDER BY version DESC, id DESC
            LIMIT 1
            """,
            (LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE, STATE_APPROVED),
        ).fetchone()

        if not post:
            raise SystemExit("ERROR: postcondition failed: no APPROVED WEEKLY_RECAP row found")

        if "## What happened (facts)\n" not in RENDERED_TEXT:
            raise SystemExit("ERROR: internal: seeded text missing required header")

        print("=== Patch: seed APPROVED weekly recap in CI fixture (v3) ===")
        print(f"db={DB_PATH}")
        print(f"key=league_id={LEAGUE_ID} season={SEASON} week_index={WEEK_INDEX} artifact_type={ARTIFACT_TYPE}")
        print(f"selection_fingerprint={selection_fingerprint}")
        print(f"before: rows={before_count} states={before_states} max_version={before_max_version}")
        print(f"after : id={post['id']} version={post['version']} state={post['state']} text_len={post['text_len']}")
        print(f"changed={'yes' if changed else 'no'}")
        print(f"OK: APPROVED WEEKLY_RECAP present (id={post['id']} version={post['version']} text_len={post['text_len']} fp={post['selection_fingerprint']})")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
