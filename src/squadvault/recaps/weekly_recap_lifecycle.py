from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from squadvault.core_engine.editorial_attunement_v1 import EALMeta, evaluate_editorial_attunement_v1
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
# Internal helpers (ported from your existing script behavior)
# =============================================================================

def _utc_now_sql() -> str:
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def _get_active_artifact_path(db_path: str, league_id: str, season: int, week_index: int) -> str:
    """
    Legacy source of the rendered recap text: reads from recaps.status='ACTIVE'
    and uses artifact_path to load the text to mint into recap_artifacts.
    Preserved to avoid behavior drift during hardening.
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


# SV_FIX_GET_RECAP_RUN_TRACE_OPTIONAL_EAL_RETURN_V1
def _get_recap_run_trace(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    include_editorial: bool = False,
) -> tuple[str, str | None, str | None] | tuple[str, str | None, str | None, str | None]:
    """Reads selection_fingerprint + window bounds from recap_runs.

    If include_editorial=True:
      - returns (fp, window_start, window_end, editorial_attunement_v1_or_None)
      - if recap_runs lacks the column, the editorial value is None

    If include_editorial=False:
      - returns (fp, window_start, window_end)
    """
    con = sqlite3.connect(db_path)
    try:
        if include_editorial:
            cols = {str(r[1]) for r in con.execute("PRAGMA table_info(recap_runs)").fetchall()}
            has_eal = "editorial_attunement_v1" in cols

            if has_eal:
                row = con.execute(
                    """
                    SELECT selection_fingerprint, window_start, window_end, editorial_attunement_v1
                    FROM recap_runs
                    WHERE league_id=? AND season=? AND week_index=?
                    """,
                    (league_id, season, week_index),
                ).fetchone()
            else:
                row = con.execute(
                    """
                    SELECT selection_fingerprint, window_start, window_end
                    FROM recap_runs
                    WHERE league_id=? AND season=? AND week_index=?
                    """,
                    (league_id, season, week_index),
                ).fetchone()

                if row:
                    row = (row[0], row[1], row[2], None)

        else:
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

    fp = str(row[0])
    ws = (str(row[1]) if row[1] else None)
    we = (str(row[2]) if row[2] else None)

    if include_editorial:
        eal = (str(row[3]) if row[3] else None)
        return fp, ws, we, eal

    return fp, ws, we

def _persist_editorial_attunement_v1_to_recap_runs(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    directive: str,
) -> None:
    """Persist EAL directive into recap_runs in a runtime-safe, additive way.

    - If recap_runs lacks editorial_attunement_v1, add the column.
    - Update all rows for (league_id, season, week_index). Safe for both
      one-row-per-week and multi-row-per-week schemas.
    """
    directive = (directive or "").strip()
    if not directive:
        return

    con = sqlite3.connect(db_path)
    try:
        cur = con.execute("PRAGMA table_info(recap_runs)")
        cols = {str(r[1]) for r in cur.fetchall()}  # (cid, name, type, notnull, dflt_value, pk)
        if "editorial_attunement_v1" not in cols:
            con.execute("ALTER TABLE recap_runs ADD COLUMN editorial_attunement_v1 TEXT")

        con.execute(
            "UPDATE recap_runs SET editorial_attunement_v1=? WHERE league_id=? AND season=? AND week_index=?",
            (directive, league_id, season, week_index),
        )
        con.commit()
    finally:
        con.close()

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
    fp = (selection_fingerprint or "").strip()
    if not fp:
        raise ValueError("selection_fingerprint must be a non-empty string")

    con = sqlite3.connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")

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

            if (not force) and (latest_fp is not None) and (latest_fp == fp):
                con.execute("COMMIT")
                return latest_v, False

            if supersedes_version is None:
                supersedes_version = latest_v

        v_row = con.execute(
            """
            SELECT COALESCE(MAX(version), 0) + 1
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
            """,
            (league_id, season, week_index),
        ).fetchone()
        v = int(v_row[0])

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
) -> Optional[int]:
    row = con.execute(
        """
        SELECT version
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND state=?
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index, state),
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
    con = sqlite3.connect(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")

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
            raise SystemExit(
                f"Refusing to approve version={version_to_approve} because state is '{row[0]}', not DRAFT."
            )

        prev_approved_version = _latest_artifact_in_state(con, league_id, season, week_index, "APPROVED")

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

        if prev_approved_version is not None:
            con.execute(
                """
                UPDATE recap_artifacts
                SET state='SUPERSEDED'
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
                  AND version=? AND state='APPROVED'
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
# Canonical lifecycle API (scripts should call ONLY these)
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

    Preserves your current behavior:
    - Requires recap_runs row to exist
    - Reads selection_fingerprint + window bounds from recap_runs
    - Renders text from recaps.ACTIVE artifact_path
    - Fingerprint-idempotent unless force=True
    - Syncs recap_runs derived state from recap_artifacts
    """
    state = get_recap_run_state(db_path, league_id, season, week_index)
    if state is None:
        raise SystemExit("No recap_runs row found for that week.")

    path = _get_active_artifact_path(db_path, league_id, season, week_index)
    rendered_text = render_recap_text_from_path_v1(path)

    selection_fingerprint, window_start, window_end = _get_recap_run_trace(
        db_path, league_id, season, week_index
    )

    # SV_EAL_V1_BEGIN: Editorial Attunement Layer v1 (restraint-only, metadata-only)
    # NOTE: This must not modify selection, ordering, or facts. It only constrains expression.
    included_count = None
    # Prefer deterministic locals if present; otherwise remain None.
    for _name in ('events_selected', 'selected_count', 'n_selected', 'num_selected'):
        if _name in locals() and isinstance(locals()[_name], int):
            included_count = int(locals()[_name])
            break
    meta = EALMeta(
        has_selection_set=True,
        has_window=True,
        included_count=included_count,
        excluded_count=None,
    )
    editorial_attunement_v1 = evaluate_editorial_attunement_v1(meta)


    # SV_EAL_RECAP_RUNS_PERSIST_V1_CALL: persist directive into recap_runs (additive metadata)
    _persist_editorial_attunement_v1_to_recap_runs(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        directive=editorial_attunement_v1,
    )
    # SV_EAL_V1_END

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
    - Only DRAFT can be approved
    - Supersedes prior APPROVED (if any)
    - Sync recap_runs from artifact truth
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
