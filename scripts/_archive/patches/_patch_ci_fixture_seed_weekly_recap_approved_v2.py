#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("fixtures/ci_squadvault.sqlite")

LEAGUE_ID = "70985"
SEASON = 2024
WEEK_INDEX = 6

ARTIFACT_TYPE = "WEEKLY_RECAP"
STATE_APPROVED = "APPROVED"

TS_UTC = "2026-01-01T00:00:00Z"
CREATED_BY = "ci"
APPROVED_BY = "ci"

RENDERED_TEXT = (
    "WEEKLY RECAP (CI FIXTURE)\n"
    "\n"
    "Deterministic seeded recap used to satisfy golden path export validation.\n"
    "League: 70985\n"
    "Season: 2024\n"
    "Week: 06\n"
    "Timestamp: 2026-01-01T00:00:00Z\n"
)

def _require_columns(conn: sqlite3.Connection, table: str, required: set[str]) -> None:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    missing = sorted(required - set(cols))
    if missing:
        raise SystemExit(f"ERROR: {table} missing columns: {missing}\nFound: {cols}")

def _get_selection_context(conn: sqlite3.Connection) -> tuple[str, str, str]:
    """
    Prefer sourcing fingerprint + window from recaps table if present for this key.
    Otherwise fall back to deterministic placeholders.
    """
    # recaps schema exists in your fixture (per your earlier PRAGMA output)
    _require_columns(conn, "recaps", {"selection_fingerprint", "window_start", "window_end", "league_id", "season", "week_index"})
    row = conn.execute(
        """
        SELECT selection_fingerprint, window_start, window_end
        FROM recaps
        WHERE league_id=? AND season=? AND week_index=?
        ORDER BY recap_version DESC, id DESC
        LIMIT 1
        """,
        (LEAGUE_ID, SEASON, WEEK_INDEX),
    ).fetchone()
    if row and row[0]:
        fp = str(row[0])
        ws = str(row[1] or TS_UTC)
        we = str(row[2] or TS_UTC)
        return fp, ws, we

    # Deterministic placeholders if recaps has no row
    fp = f"ci_seed_fp__{LEAGUE_ID}__{SEASON}__{WEEK_INDEX:02d}__v1"
    return fp, TS_UTC, TS_UTC

def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"ERROR: missing fixture DB: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        _require_columns(
            conn,
            "recap_artifacts",
            {
                "id","league_id","season","week_index","artifact_type","version","state",
                "selection_fingerprint","window_start","window_end",
                "rendered_text","created_at","created_by","approved_at","approved_by",
            },
        )

        fp, ws, we = _get_selection_context(conn)

        rows = conn.execute(
            """
            SELECT id, version, state, rendered_text
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
            ORDER BY version ASC, id ASC
            """,
            (LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE),
        ).fetchall()

        before_count = len(rows)
        before_states = [r["state"] for r in rows]
        before_max_version = max([r["version"] for r in rows], default=0)

        changed = False
        approved_rows = [r for r in rows if r["state"] == STATE_APPROVED]

        if approved_rows:
            r = approved_rows[-1]
            if (r["rendered_text"] is None) or (str(r["rendered_text"]).strip() == ""):
                conn.execute(
                    "UPDATE recap_artifacts SET rendered_text=? WHERE id=?",
                    (RENDERED_TEXT, int(r["id"])),
                )
                changed = True
        elif rows:
            r = rows[-1]
            conn.execute(
                """
                UPDATE recap_artifacts
                SET state=?,
                    approved_at=?,
                    approved_by=?,
                    created_at=COALESCE(created_at, ?),
                    created_by=COALESCE(created_by, ?),
                    selection_fingerprint=COALESCE(selection_fingerprint, ?),
                    window_start=COALESCE(window_start, ?),
                    window_end=COALESCE(window_end, ?),
                    rendered_text=CASE
                        WHEN rendered_text IS NULL OR TRIM(rendered_text) = '' THEN ?
                        ELSE rendered_text
                    END
                WHERE id=?
                """,
                (STATE_APPROVED, TS_UTC, APPROVED_BY, TS_UTC, CREATED_BY, fp, ws, we, RENDERED_TEXT, int(r["id"])),
            )
            changed = True
        else:
            # Insert deterministic new row; satisfy NOT NULL selection_fingerprint (+ window fields).
            conn.execute(
                """
                INSERT INTO recap_artifacts (
                    league_id, season, week_index, artifact_type,
                    version, state,
                    selection_fingerprint, window_start, window_end,
                    rendered_text,
                    created_at, created_by,
                    approved_at, approved_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE,
                    1, STATE_APPROVED,
                    fp, ws, we,
                    RENDERED_TEXT,
                    TS_UTC, CREATED_BY,
                    TS_UTC, APPROVED_BY,
                ),
            )
            changed = True

        conn.commit()

        post = conn.execute(
            """
            SELECT id, version, state,
                   LENGTH(COALESCE(rendered_text,'')) AS text_len,
                   selection_fingerprint
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND state=?
            ORDER BY version DESC, id DESC
            LIMIT 1
            """,
            (LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE, STATE_APPROVED),
        ).fetchone()
        if not post:
            raise SystemExit("ERROR: postcondition failed: no APPROVED WEEKLY_RECAP row found.")
        if not post["selection_fingerprint"]:
            raise SystemExit("ERROR: postcondition failed: selection_fingerprint is empty.")

        print("=== Patch: seed APPROVED weekly recap in CI fixture (v2) ===")
        print(f"db={DB_PATH}")
        print(f"key=league_id={LEAGUE_ID} season={SEASON} week_index={WEEK_INDEX} artifact_type={ARTIFACT_TYPE}")
        print(f"selection_fingerprint={post['selection_fingerprint']}")
        print(f"before: rows={before_count} states={before_states} max_version={before_max_version}")
        print(f"after : id={post['id']} version={post['version']} state={post['state']} text_len={post['text_len']}")
        print(f"changed={'yes' if changed else 'no'}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
