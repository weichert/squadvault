#!/usr/bin/env python3
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

TS_UTC = "2026-01-01T00:00:00Z"

DB_PATH = Path("fixtures/ci_squadvault.sqlite")

LEAGUE_ID = "70985"
SEASON = 2024
WEEK_INDEX = 6
ARTIFACT_TYPE = "WEEKLY_RECAP"
TARGET_STATE = "APPROVED"

# Deterministic, short, ASCII-only
RENDERED_TEXT = (
    "Weekly Recap (Fixture Seed)\n"
    "league_id=70985 season=2024 week_index=6\n"
    "state=APPROVED\n"
    "created_at_utc=2026-01-01T00:00:00Z\n"
    "approved_at_utc=2026-01-01T00:00:00Z\n"
)

# Golden path / NAC preflight normalization expects a 64-hex fingerprint; use deterministic zeros.
FP64 = "0" * 64


def _repo_root_from_this_file() -> Path:
    return Path(__file__).resolve().parent.parent


def _connect(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    return con


def _table_columns(con: sqlite3.Connection, table: str) -> List[str]:
    rows = con.execute(f"PRAGMA table_info({table});").fetchall()
    return [r["name"] for r in rows]


def _pick_first(cols: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    for c in candidates:
        if c in cols:
            return c
    return None


def _require(table: str, cols: Sequence[str], required: Sequence[str]) -> None:
    missing = [c for c in required if c not in cols]
    if missing:
        raise SystemExit(
            "ERROR: recap_artifacts schema missing expected columns:\n"
            f"  table={table}\n"
            f"  missing={missing}\n"
            f"  cols={list(cols)}\n"
        )


def _select_latest_for_week(con: sqlite3.Connection, cols: Sequence[str]) -> List[sqlite3.Row]:
    # version is expected by tests; order by version desc if present, else by id desc.
    order = None
    if "version" in cols:
        order = "version DESC"
    elif "id" in cols:
        order = "id DESC"

    q = (
        "SELECT * FROM recap_artifacts "
        "WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? "
    )
    if order:
        q += f"ORDER BY {order}"
    return con.execute(q, (LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE)).fetchall()


def main() -> int:
    os.chdir(_repo_root_from_this_file())

    if not DB_PATH.exists():
        print(f"ERROR: fixture DB not found: {DB_PATH}", file=sys.stderr)
        return 2

    con = _connect(DB_PATH)
    try:
        tables = {r["name"] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()}
        if "recap_artifacts" not in tables:
            raise SystemExit(f"ERROR: fixture DB missing recap_artifacts table. tables={sorted(tables)}")

        cols = _table_columns(con, "recap_artifacts")

        # Required core columns for this patch.
        _require(
            "recap_artifacts",
            cols,
            ["league_id", "season", "week_index", "artifact_type", "state"],
        )

        # Common/expected columns in this repo (based on your greps and schema.sql presence).
        col_version = "version" if "version" in cols else None
        col_id = "id" if "id" in cols else None

        col_rendered_text = _pick_first(cols, ["rendered_text", "text", "content", "markdown", "body"])
        if not col_rendered_text:
            raise SystemExit(
                "ERROR: recap_artifacts has no rendered_text/content column; cannot seed deterministic recap."
            )

        col_fp = _pick_first(cols, ["selection_fingerprint", "fingerprint"])
        col_created = _pick_first(cols, ["created_at_utc", "created_utc", "created_at"])
        col_approved = _pick_first(cols, ["approved_at_utc", "approved_utc", "approved_at"])
        col_updated = _pick_first(cols, ["updated_at_utc", "updated_utc", "updated_at"])

        rows = _select_latest_for_week(con, cols)

        print("== CI fixture seed: APPROVED WEEKLY_RECAP (v1) ==")
        print(f"db={DB_PATH}")
        print(f"matched_rows={len(rows)}")

        def summarize(r: sqlite3.Row) -> str:
            rid = r[col_id] if (col_id and col_id in r.keys()) else "?"
            ver = r[col_version] if (col_version and col_version in r.keys()) else "?"
            state = r["state"] if "state" in r.keys() else "?"
            txt = r[col_rendered_text] if col_rendered_text in r.keys() else ""
            tlen = len(txt or "")
            fp = (r[col_fp] if (col_fp and col_fp in r.keys()) else None) or ""
            return f"id={rid} version={ver} state={state} text_len={tlen} fp={(fp[:16] + '…') if fp else '(none)'}"

        if rows:
            # If any APPROVED exists, no-op (idempotent).
            for r in rows:
                if r["state"] == TARGET_STATE:
                    print(f"status=already_present {summarize(r)}")
                    return 0

            # Promote the latest row to APPROVED.
            r0 = rows[0]
            if not col_id:
                raise SystemExit("ERROR: cannot promote without primary key column 'id' present")

            rid = r0[col_id]
            assignments: List[str] = ["state=?"]
            params: List[object] = [TARGET_STATE]

            if col_approved:
                assignments.append(f"{col_approved}=?")
                params.append(TS_UTC)
            if col_updated:
                assignments.append(f"{col_updated}=?")
                params.append(TS_UTC)

            # Ensure deterministic rendered text + fingerprint if columns exist.
            assignments.append(f"{col_rendered_text}=?")
            params.append(RENDERED_TEXT)

            if col_fp:
                assignments.append(f"{col_fp}=?")
                params.append(FP64)

            params.append(rid)

            con.execute(
                f"UPDATE recap_artifacts SET {', '.join(assignments)} WHERE id=?",
                params,
            )
            con.commit()

            post = _select_latest_for_week(con, cols)
            if not post:
                raise SystemExit("ERROR: postcondition failed: row disappeared after UPDATE")
            print(f"status=promoted {summarize(post[0])}")
            return 0

        # Insert new deterministic row.
        insert_cols: List[str] = ["league_id", "season", "week_index", "artifact_type", "state", col_rendered_text]
        insert_vals: List[object] = [LEAGUE_ID, SEASON, WEEK_INDEX, ARTIFACT_TYPE, TARGET_STATE, RENDERED_TEXT]

        if col_version:
            # Deterministic first version
            insert_cols.append("version")
            insert_vals.append(1)

        if col_fp:
            insert_cols.append(col_fp)
            insert_vals.append(FP64)

        if col_created:
            insert_cols.append(col_created)
            insert_vals.append(TS_UTC)

        if col_approved:
            insert_cols.append(col_approved)
            insert_vals.append(TS_UTC)

        if col_updated:
            insert_cols.append(col_updated)
            insert_vals.append(TS_UTC)

        ph = ",".join(["?"] * len(insert_cols))
        con.execute(
            f"INSERT INTO recap_artifacts ({', '.join(insert_cols)}) VALUES ({ph})",
            insert_vals,
        )
        con.commit()

        post = _select_latest_for_week(con, cols)
        if not post or not any(r["state"] == TARGET_STATE for r in post):
            raise SystemExit("ERROR: postcondition failed: no APPROVED WEEKLY_RECAP row found.")
        # Report the most recent row.
        print(f"status=inserted {summarize(post[0])}")
        return 0

    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
