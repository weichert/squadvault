import json
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RecapRunRecord:
    league_id: str
    season: int
    week_index: int
    state: str  # ELIGIBLE | DRAFTED | REVIEW_REQUIRED | APPROVED | WITHHELD | SUPERSEDED

    window_mode: Optional[str]
    window_start: Optional[str]
    window_end: Optional[str]

    selection_fingerprint: str
    canonical_ids: List[str]
    counts_by_type: Dict[str, int]

    reason: Optional[str] = None


def upsert_recap_run(db_path: str, r: RecapRunRecord) -> None:
    """
    Idempotently write recap workflow state + deterministic selection trace for a week.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO recap_runs (
              league_id, season, week_index,
              state,
              window_mode, window_start, window_end,
              selection_fingerprint,
              canonical_ids_json,
              counts_by_type_json,
              reason,
              updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            ON CONFLICT(league_id, season, week_index) DO UPDATE SET
              state=excluded.state,
              window_mode=excluded.window_mode,
              window_start=excluded.window_start,
              window_end=excluded.window_end,
              selection_fingerprint=excluded.selection_fingerprint,
              canonical_ids_json=excluded.canonical_ids_json,
              counts_by_type_json=excluded.counts_by_type_json,
              reason=excluded.reason,
              updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """,
            (
                r.league_id,
                r.season,
                r.week_index,
                r.state,
                r.window_mode,
                r.window_start,
                r.window_end,
                r.selection_fingerprint,
                json.dumps(r.canonical_ids),
                json.dumps(r.counts_by_type, sort_keys=True),
                r.reason,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_recap_run_state(db_path: str, league_id: str, season: int, week_index: int) -> Optional[str]:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT state
            FROM recap_runs
            WHERE league_id=? AND season=? AND week_index=?
            """,
            (league_id, season, week_index),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def update_recap_run_state(db_path: str, league_id: str, season: int, week_index: int, new_state: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            """
            UPDATE recap_runs
            SET state=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE league_id=? AND season=? AND week_index=?
            """,
            (new_state, league_id, season, week_index),
        )
        if cur.rowcount != 1:
            raise RuntimeError(
                f"Expected exactly 1 recap_runs row to update for "
                f"{league_id}/{season}/week={week_index}, got {cur.rowcount}"
            )
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# Explicit reconciliation: recap_runs state derived from recap_artifacts truth
# =============================================================================

def _latest_artifact_state_for_week(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Tuple[int, str]]:
    """
    Returns (version, state) for the latest recap_artifacts row for this week,
    or None if no artifacts exist.
    """
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT version, state
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()
        if not row:
            return None
        return int(row[0]), str(row[1])
    finally:
        conn.close()


def _has_any_approved_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
              AND state='APPROVED'
            LIMIT 1
            """,
            (league_id, season, week_index),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def sync_recap_run_state_from_artifacts(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[str]:
    """
    Explicit reconciliation step (call it from render/approve/regenerate).

    Rule (MVP):
    - If latest artifact is DRAFT => recap_runs.state = REVIEW_REQUIRED
    - If latest artifact is WITHHELD => recap_runs.state = WITHHELD
    - Else if there exists any APPROVED artifact => recap_runs.state = APPROVED
      (covers case where latest is SUPERSEDED but an approved exists)
    - If no artifacts exist => no-op, return None

    Returns the state that was written, or None if no-op.
    """
    latest = _latest_artifact_state_for_week(db_path, league_id, season, week_index)
    if latest is None:
        return None

    _v, latest_state = latest

    if latest_state == "DRAFT":
        new_state = "REVIEW_REQUIRED"
    elif latest_state == "WITHHELD":
        new_state = "WITHHELD"
    else:
        # latest_state could be APPROVED or SUPERSEDED
        new_state = "APPROVED" if _has_any_approved_artifact(db_path, league_id, season, week_index) else None

    if new_state is None:
        return None

    update_recap_run_state(db_path, league_id, season, week_index, new_state)
    return new_state
