from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional, Tuple

from squadvault.core.recaps.render.render_recap_text_v1 import render_recap_text_from_path_v1
from squadvault.core.recaps.recap_runs import (
    get_recap_run_state,
    sync_recap_run_state_from_artifacts,
)
from squadvault.core.recaps.recap_artifacts import latest_approved_version


ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"


# =============================================================================
# Public result types
# =============================================================================

@dataclass(frozen=True)
class GenerateDraftResult:
    version: int
    created_new: bool
    selection_fingerprint: str
    window_start: Optional[str]
    window_end: Optional[str]
    prev_approved_version: Optional[int]
    synced_recap_run_state: Optional[str]
    reason: str


@dataclass(frozen=True)
class ApproveResult:
    approved_version: int
    superseded_version: Optional[int]
    synced_recap_run_state: Optional[str]


# =============================================================================
# Internal DB helpers (ported from your scripts, unchanged behavior)
# =============================================================================

def _utc_now_sql() -> str:
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def _get_active_artifact_path(db_path: str, league_id: str, season: int, week_index: int) -> str:
    """
    Legacy source of the rendered recap text: reads from recaps.status='ACTIVE'
    and uses artifact_path to load the text to mint into recap_artifacts.

    This is intentionally preserved to avoid behavior drift during hardening.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT artifact_path
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=? AND status='ACTIVE'
            ORDER BY recap_version DESC
            LIMIT 1;
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        raise SystemExit("No ACTIVE recap with artifact_path found for that week.")

    return str(row[0])


def _get_recap_run_trace(
    db_path: str, league_id: str, season: int, week_index: int
) -> tuple[str, Optional[str], Optional[str]]:
    """
    Reads the selection fingerprint + window bounds from recap_runs.

    This is the canonical trace linkage between (week selection) and (artifact versions).
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT selection_fingerprint, window_start, window_end
            FROM recap_runs
            WHERE league_id=? AND season=? AND week_index=?
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        raise SystemExit("No recap_runs row found (missing selection_fingerprint).")

    return str(row[0]), (str(row[1]) if row[1] else None), (str(row[2]) if row[2] else None)


def _create_recap_artifact_draft_always_new(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    selection_fingerprint: str,
    window_start: str | None,
    window_end: str | None,
    rendered_text: str,
    created_by: str,
    supersedes_version: int | None,
    force: bool = False,
) -> tuple[int, bool]:
    """
    Option B: fingerprint-idempotent regeneration (with explicit force override).

    Behavior:
    - If the latest artifact (ANY state) already has the same selection_fingerprint and force=False,
      return (latest_version, False) and do not create a new row.
    - Otherwise, create a new DRAFT artifact version and return (new_version, True).

    supersedes_version:
    - If not provided and we are creating a new artifact, default it to the latest version (ANY state).
    """
    # Normalize fingerprint defensively; treat empty as None-like.
    fp = (selection_fingerprint or "").strip()
    if not fp:
        raise ValueError("selection_fingerprint must be a non-empty string")

    con = sqlite3.connect(db_path)
    try:
        # Acquire a write lock early to avoid concurrent writers racing version numbers.
        con.execute("BEGIN IMMEDIATE")

        # Look at latest artifact (any state) for idempotency.
        row = con.execute(
            """
            SELECT version, selection_fingerprint
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()

        latest_v: Optional[int] = None
        latest_fp: Optional[str] = None

        if row:
            latest_v = int(row[0])
            latest_fp = (row[1] or "").strip() or None

            # Idempotent no-op unless forced.
            if (not force) and (latest_fp is not None) and (latest_fp == fp):
                con.execute("COMMIT")
                return latest_v, False

            # Default supersedes to latest if not explicitly provided (only if creating a new row).
            if supersedes_version is None:
                supersedes_version = latest_v

        # Compute next version inside the same transaction to prevent races.
        v_row = con.execute(
            """
            SELECT COALESCE(MAX(version), 0) + 1
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
            """,
            (league_id, season, week_index),
        ).fetchone()
        v = int(v_row[0])

        # Insert new DRAFT artifact row (insert-only).
        con.execute(
            f"""
            INSERT INTO recap_artifacts (
              league_id, season, week_index, artifact_type,
              version, state,
              selection_fingerprint, window_start, window_end,
              rendered_text,
              created_at, created_by,
              supersedes_version
            ) VALUES (?, ?, ?, 'WEEKLY_RECAP', ?, 'DRAFT', ?, ?, ?, ?, {_utc_now_sql()}, ?, ?)
            """,
            (
                league_id,
                season,
                week_index,
                v,
                fp,
                window_start,
                window_end,
                rendered_text,
                created_by,
                supersedes_version,
            ),
        )

        con.execute("COMMIT")
        return v, True

    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        con.close()


def _latest_artifact_in_state(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
    state: str,
) -> Optional[Tuple[int, str]]:
    """
    Returns (version, state) for latest artifact in the given state.
    """
    row = con.execute(
        """
        SELECT version, state
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND state=?
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index, state),
    ).fetchone()
    if not row:
        return None
    return int(row[0]), str(row[1])

def _latest_draft_artifact_version(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[int]:
    row = con.execute(
        """
        SELECT version
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
          AND state IN ('DRAFT','DRAFTED')
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    ).fetchone()
    return None if not row else int(row[0])

def _latest_draft_version(con, league_id, season, week_index) -> Optional[int]:
    row = con.execute(
        """
        SELECT version
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
          AND state IN ('DRAFT','DRAFTED')
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    ).fetchone()
    return None if not row else int(row[0])

def _approve_version_and_supersede_previous(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version_to_approve: int,
    approved_by: str,
) -> Tuple[int, Optional[int]]:
    """
    Approves a specific version and supersedes the prior APPROVED (if any).
    Returns (approved_version, superseded_version).
    """
    con = sqlite3.connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")

        # Ensure the target exists and is DRAFT (we keep MVP rules tight).
        row = con.execute(
            """
            SELECT state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND version=?
            """,
            (league_id, season, week_index, version_to_approve),
        ).fetchone()
        if not row:
            raise SystemExit(f"No WEEKLY_RECAP artifact found for version={version_to_approve}.")
        if str(row[0]) not in ("DRAFT", "DRAFTED"):
            raise SystemExit(f"Refusing to approve version={version_to_approve} because state is '{row[0]}', not DRAFT.")

        prev = _latest_artifact_in_state(con, league_id, season, week_index, "APPROVED")
        prev_approved_version = prev[0] if prev else None

        # Approve the target version.
        con.execute(
            f"""
            UPDATE recap_artifacts
            SET state='APPROVED',
                approved_by=?,
                approved_at={_utc_now_sql()}
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND version=?
            """,
            (approved_by, league_id, season, week_index, version_to_approve),
        )

        # Supersede previous approved (if any).
        if prev_approved_version is not None:
            con.execute(
                """
                UPDATE recap_artifacts
                SET state='SUPERSEDED'
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND version=? AND state='APPROVED'
                """,
                (league_id, season, week_index, prev_approved_version),
            )

        con.execute("COMMIT")
        return version_to_approve, prev_approved_version

    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        con.close()


# =============================================================================
# Canonical lifecycle API (THIS is what scripts/CLIs should call)
# =============================================================================

def generate_weekly_recap_draft(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    reason: str,
    force: bool = False,
    created_by: str = "system",
) -> GenerateDraftResult:
    """
    Canonical entrypoint: mint a WEEKLY_RECAP DRAFT artifact version.

    Preserves current behavior:
    - Requires an existing recap_runs row (explicit workflow)
    - Reads recap_runs.selection_fingerprint + window bounds
    - Loads rendered recap text from legacy recaps.ACTIVE artifact_path
    - Creates a new DRAFT version unless fingerprint unchanged (unless force=True)
    - Syncs recap_runs state from artifact truth
    """
    # Ensure the week exists in recap_runs (explicit workflow)
    state = get_recap_run_state(db_path, league_id, season, week_index)
    if state is None:
        raise SystemExit("No recap_runs row found for that week.")

    # Render from existing ACTIVE recap artifact path (legacy storage)
    path = _get_active_artifact_path(db_path, league_id, season, week_index)
    rendered_text = render_recap_text_from_path_v1(path)

    selection_fingerprint, window_start, window_end = _get_recap_run_trace(
        db_path, league_id, season, week_index
    )

    prev_approved = latest_approved_version(db_path, league_id, season, week_index)

    v, created_new = _create_recap_artifact_draft_always_new(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        selection_fingerprint=selection_fingerprint,
        window_start=window_start,
        window_end=window_end,
        rendered_text=rendered_text,
        created_by=created_by,
        supersedes_version=None,
        force=force,
    )

    # Artifact truth -> recap_runs derived state
    synced_state = sync_recap_run_state_from_artifacts(db_path, league_id, season, week_index)

    return GenerateDraftResult(
        version=v,
        created_new=created_new,
        selection_fingerprint=selection_fingerprint,
        window_start=window_start,
        window_end=window_end,
        prev_approved_version=prev_approved,
        synced_recap_run_state=synced_state,
        reason=reason,
    )


def approve_latest_weekly_recap(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    approved_by: str,
) -> ApproveResult:
    """
    Canonical entrypoint: approve the latest DRAFT WEEKLY_RECAP artifact.

    Tight MVP rules:
    - Only DRAFT can be approved
    - Approval marks that version APPROVED and supersedes prior APPROVED (if any)
    - Then sync recap_runs from artifacts
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT version
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND state IN ('DRAFT','DRAFTED')
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()

    if not row:
        raise SystemExit("No DRAFT WEEKLY_RECAP artifact found to approve for that week.")

    draft_version = int(row[0])

    approved_version, superseded_version = _approve_version_and_supersede_previous(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        version_to_approve=draft_version,
        approved_by=approved_by,
    )

    synced_state = sync_recap_run_state_from_artifacts(db_path, league_id, season, week_index)

    return ApproveResult(
        approved_version=approved_version,
        superseded_version=superseded_version,
        synced_recap_run_state=synced_state,
    )
