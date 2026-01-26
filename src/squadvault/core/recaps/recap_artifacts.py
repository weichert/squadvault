import sqlite3
from typing import Optional, Tuple


ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"

ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1 = "RIVALRY_CHRONICLE_V1"

# Artifact state machine: DRAFT | APPROVED | WITHHELD | SUPERSEDED
_ALLOWED_TRANSITIONS = {
    ("DRAFT", "APPROVED"),
    ("DRAFT", "WITHHELD"),
    ("APPROVED", "SUPERSEDED"),
}


def _utc_now_sql() -> str:
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def _assert_transition(old: str, new: str) -> None:
    if (old, new) not in _ALLOWED_TRANSITIONS:
        raise ValueError(f"Invalid artifact transition: {old} -> {new}")


def _normalize_withheld_reason(withheld_reason: str) -> str:
    """
    Normalize withheld_reason to reduce drift while preserving backward compatibility.

    - If caller passes a stable deterministic code (e.g., WINDOW_* or DNG_*), keep it.
    - If empty/whitespace, fall back to a stable generic value.
    - Otherwise, preserve the provided string (we do not want to break callers).
    """
    r = (withheld_reason or "").strip()
    if not r:
        return "WITHHELD"

    # Preserve known stable prefixes used elsewhere in the system.
    if r.startswith("WINDOW_") or r.startswith("DNG_"):
        return r

    return r


def _latest_artifact_row_any_state(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int, artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP) -> Optional[sqlite3.Row]:
    return con.execute(
        """
        SELECT version, state, selection_fingerprint
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index, artifact_type),
    ).fetchone()


def _latest_artifact_version_any_state(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int, artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP) -> Optional[int]:
    row = _latest_artifact_row_any_state(con, league_id, season, week_index, artifact_type)
    return int(row[0]) if row else None


def _latest_artifact_fingerprint_any_state(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int, artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP) -> Optional[str]:
    row = _latest_artifact_row_any_state(con, league_id, season, week_index, artifact_type)
    if not row:
        return None
    fp = row[2]
    return str(fp) if fp else None


def latest_approved_version(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    artifact_type: str = ARTIFACT_TYPE_WEEKLY_RECAP,
) -> Optional[int]:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT version
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
              AND state='APPROVED'
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index, artifact_type),
        ).fetchone()
        return int(row[0]) if row else None
    finally:
        con.close()


def _latest_approved_fingerprint(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
    artifact_type: str = ARTIFACT_TYPE_WEEKLY_RECAP,
) -> Optional[str]:
    row = con.execute(
        """
        SELECT selection_fingerprint
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
          AND state='APPROVED'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index, artifact_type),
    ).fetchone()
    return str(row[0]) if row and row[0] else None


def _latest_approved_version_in_conn(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int, artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP) -> Optional[int]:
    row = con.execute(
        """
        SELECT version
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
          AND state='APPROVED'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index, artifact_type),
    ).fetchone()
    return int(row[0]) if row else None


def _find_existing_draft_version(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
    selection_fingerprint: str,
    artifact_type: str = ARTIFACT_TYPE_WEEKLY_RECAP,
) -> Optional[int]:
    """
    Idempotency helper: if a DRAFT already exists for this exact fingerprint,
    return its version.
    """
    row = con.execute(
        """
        SELECT version
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
          AND state='DRAFT'
          AND selection_fingerprint=?
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index, artifact_type, selection_fingerprint),
    ).fetchone()
    return int(row[0]) if row else None


def _next_version(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int, artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP) -> int:
    row = con.execute(
        """
        SELECT COALESCE(MAX(version), 0)
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
        """,
        (league_id, season, week_index, artifact_type),
    ).fetchone()
    return int(row[0]) + 1


def create_recap_artifact_draft_idempotent(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    selection_fingerprint: str,
    window_start: Optional[str],
    window_end: Optional[str],
    rendered_text: str,
    artifact_type: str = ARTIFACT_TYPE_WEEKLY_RECAP,
    created_by: str = "system",
    supersedes_version: Optional[int] = None,
    force: bool = False,
) -> Tuple[int, bool]:
    """
    Option B: fingerprint-idempotent regeneration.

    Creates a new DRAFT recap artifact version unless:
      1) the latest artifact (ANY state) already has the same selection_fingerprint and force=False, OR
      2) a DRAFT already exists for the same selection_fingerprint, OR
      3) the latest APPROVED artifact already has the same selection_fingerprint (legacy guard)

    Returns: (version, created_new)

    NOTE:
    - If case (1) hits, we return the latest artifact version and created_new=False.
    - If case (3) hits, we return the latest approved version and created_new=False.
    """
    con = sqlite3.connect(db_path)
    try:
        # Case (1): latest artifact (ANY state) already matches fingerprint => no-op (unless forced).
        latest_fp = _latest_artifact_fingerprint_any_state(con, league_id, season, week_index, artifact_type)
        if (not force) and (latest_fp is not None) and (latest_fp == selection_fingerprint):
            latest_v = _latest_artifact_version_any_state(con, league_id, season, week_index, artifact_type)
            if latest_v is not None:
                return latest_v, False

        # Case (3): already approved with same fingerprint => do nothing (prevents version spam).
        approved_fp = _latest_approved_fingerprint(con, league_id, season, week_index, artifact_type)
        if (not force) and (approved_fp is not None) and (approved_fp == selection_fingerprint):
            approved_v = _latest_approved_version_in_conn(con, league_id, season, week_index, artifact_type)
            if approved_v is not None:
                return approved_v, False

        # Case (2): draft already exists for this fingerprint => idempotent.
        existing = _find_existing_draft_version(con, league_id, season, week_index, selection_fingerprint, artifact_type)
        if existing is not None:
            return existing, False

        # Default supersedes_version to latest version (ANY state) if not provided.
        if supersedes_version is None:
            supersedes_version = _latest_artifact_version_any_state(con, league_id, season, week_index, artifact_type)

        v = _next_version(con, league_id, season, week_index, artifact_type)
        con.execute(
            f"""
            INSERT INTO recap_artifacts (
              league_id, season, week_index, artifact_type,
              version, state,
              selection_fingerprint, window_start, window_end,
              rendered_text,
              created_at, created_by,
              supersedes_version
            ) VALUES (?, ?, ?, ?, ?, 'DRAFT', ?, ?, ?, ?, {_utc_now_sql()}, ?, ?)
            """,
            (
                league_id,
                season,
                week_index,
                artifact_type,
                v,
                selection_fingerprint,
                window_start,
                window_end,
                rendered_text,
                created_by,
                supersedes_version,
            ),
        )
        con.commit()
        return v, True
    finally:
        con.close()


def approve_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    approved_by: str,
    artifact_type: str = ARTIFACT_TYPE_WEEKLY_RECAP,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
            """,
            (league_id, season, week_index, artifact_type, version),
        ).fetchone()
        if not row:
            raise RuntimeError("Artifact not found to approve.")
        _assert_transition(str(row[0]), "APPROVED")

        cur = con.execute(
            f"""
            UPDATE recap_artifacts
            SET state='APPROVED',
                approved_at={_utc_now_sql()},
                approved_by=?
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
              AND state='DRAFT'
            """,
            (approved_by, league_id, season, week_index, artifact_type, version),
        )
        if cur.rowcount != 1:
            raise RuntimeError("Approve failed (state not DRAFT or row missing).")
        con.commit()
    finally:
        con.close()


def withhold_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    withheld_reason: str,
    artifact_type: str = ARTIFACT_TYPE_WEEKLY_RECAP,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
            """,
            (league_id, season, week_index, artifact_type, version),
        ).fetchone()
        if not row:
            raise RuntimeError("Artifact not found to withhold.")
        _assert_transition(str(row[0]), "WITHHELD")

        withheld_reason_norm = _normalize_withheld_reason(withheld_reason)

        cur = con.execute(
            """
            UPDATE recap_artifacts
            SET state='WITHHELD',
                withheld_reason=?
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
              AND state='DRAFT'
            """,
            (withheld_reason_norm, league_id, season, week_index, artifact_type, version),
        )
        if cur.rowcount != 1:
            raise RuntimeError("Withhold failed (state not DRAFT or row missing).")
        con.commit()
    finally:
        con.close()


def supersede_approved_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
            """,
            (league_id, season, week_index, artifact_type, version),
        ).fetchone()
        if not row:
            raise RuntimeError("Artifact not found to supersede.")
        _assert_transition(str(row[0]), "SUPERSEDED")

        cur = con.execute(
            """
            UPDATE recap_artifacts
            SET state='SUPERSEDED'
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND version=?
              AND state='APPROVED'
            """,
            (league_id, season, week_index, artifact_type, version),
        )
        if cur.rowcount != 1:
            raise RuntimeError("Supersede failed (state not APPROVED or row missing).")
        con.commit()
    finally:
        con.close()
