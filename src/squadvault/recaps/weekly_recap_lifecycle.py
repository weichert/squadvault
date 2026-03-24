"""Weekly recap lifecycle: draft generation, approval, and state management."""

from __future__ import annotations

import json
import re
import sqlite3
import warnings
from dataclasses import dataclass
from pathlib import Path
from squadvault.core.eal.editorial_attunement_v1 import EALMeta, evaluate_editorial_attunement_v1
from typing import Any, List, Optional, Tuple
from squadvault.core.eal.consume_v1 import load_eal_directives_v1, EALDirectivesV1
from squadvault.errors import RecapNotFoundError, RecapStateError, RecapDataError
from squadvault.core.recaps.render.render_recap_text_v1 import (
    render_recap_text_from_path_v1,
    render_recap_text_v1,
)
from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    CanonicalEventRow,
    render_deterministic_bullets_v1,
)
from squadvault.core.resolvers import PlayerResolver, FranchiseResolver
from squadvault.core.recaps.recap_runs import (
    get_recap_run_state,
    sync_recap_run_state_from_artifacts,
)
from squadvault.core.recaps.recap_artifacts import latest_approved_version
from squadvault.core.storage.session import DatabaseSession
from squadvault.ai.creative_layer_v1 import draft_narrative_v1
from squadvault.core.tone.tone_profile_v1 import get_tone_preset
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
    render_season_context_for_prompt,
)
from squadvault.core.recaps.context.league_history_v1 import (
    derive_league_history_v1,
    load_all_matchups,
    build_cross_season_name_resolver,
    render_league_history_for_prompt,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    detect_narrative_angles_v1,
    render_angles_for_prompt,
)
from squadvault.core.recaps.context.writer_room_context_v1 import (
    derive_scoring_deltas,
    derive_faab_spending,
    render_writer_room_context_for_prompt,
)


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
    """Return SQL expression for current UTC timestamp."""
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def _get_active_artifact_path(db_path: str, league_id: str, season: int, week_index: int) -> str:
    """
    Legacy source of the rendered recap text: reads from recaps.status='ACTIVE'
    and uses artifact_path to load the text to mint into recap_artifacts.
    Preserved to avoid behavior drift during hardening.
    """
    with DatabaseSession(db_path) as con:
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

    if not row or not row[0]:
        raise RecapNotFoundError("No ACTIVE recap with artifact_path found for that week.")

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
    with DatabaseSession(db_path) as con:
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

    if not row or not row[0]:
        raise RecapNotFoundError("No recap_runs row found (missing selection_fingerprint).")

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
    """Persist EAL directive into recap_runs as audit metadata.

    The editorial_attunement_v1 column is defined in schema.sql.
    Schema is the sole authority for table structure — no runtime
    DDL permitted (Phase 2: Eliminate Runtime Schema Mutation).
    """
    directive = (directive or "").strip()
    if not directive:
        return

    with DatabaseSession(db_path) as con:
        con.execute(
            "UPDATE recap_runs SET editorial_attunement_v1=? WHERE league_id=? AND season=? AND week_index=?",
            (directive, league_id, season, week_index),
        )
        con.commit()

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

    with DatabaseSession(db_path) as con:
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


def _latest_artifact_in_state(
    con: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
    state: str,
) -> Optional[int]:
    """Return latest artifact version in a given state, or None."""
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
    """Approve a version and supersede prior APPROVED if any."""
    with DatabaseSession(db_path) as con:
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
            raise RecapNotFoundError(f"No WEEKLY_RECAP artifact found for version={version_to_approve}.")
        if str(row[0]) not in ("DRAFT", "DRAFTED"):
            raise RecapStateError(
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


# =============================================================================
# Artifact materialization helper
# =============================================================================

def _ensure_artifact_on_disk(
    path: str,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> None:
    """Materialize ACTIVE recap JSON if missing on disk.

    CI runners start from a clean checkout; artifacts/ may not exist yet.
    Creates a minimal deterministic artifact (no event invention).
    """
    p = Path(path)
    if p.exists():
        return

    p.parent.mkdir(parents=True, exist_ok=True)

    m = re.search(r"recap_v(\d+)\.json$", p.name)
    if not m:
        raise RecapDataError(f"Active recap artifact path has unexpected filename: {path}")
    recap_version = int(m.group(1))

    selection_fingerprint, window_start, window_end = _get_recap_run_trace(
        db_path, league_id, season, week_index
    )

    artifact = {
        "league_id": league_id,
        "season": season,
        "week_index": week_index,
        "recap_version": recap_version,
        "window": {"start": window_start, "end": window_end},
        "selection": {
            "fingerprint": selection_fingerprint,
            "event_count": 0,
            "counts_by_type": {},
            "canonical_ids": [],
        },
    }

    with open(p, "w", encoding="utf-8") as f:
        json.dump(artifact, f, sort_keys=True)
        f.write("\n")


# =============================================================================
# Canonical lifecycle API (scripts should call ONLY these)
# =============================================================================

def _load_canonical_event_rows(
    db_path: str,
    canonical_ids: List[str],
) -> List[CanonicalEventRow]:
    """Load canonical event rows with payloads from v_canonical_best_events.

    canonical_ids are action fingerprints stored in recap_runs.canonical_ids_json.
    Returns CanonicalEventRow objects suitable for the bullets renderer.
    IDs that don't resolve are silently skipped (defensive).
    """
    if not canonical_ids:
        return []

    rows: List[CanonicalEventRow] = []
    with DatabaseSession(db_path) as con:
        # Check if view exists (defensive for minimal test DBs)
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
        ).fetchall()}
        if "v_canonical_best_events" not in tables:
            return []

        ids_str = [str(cid).strip() for cid in canonical_ids if str(cid).strip()]
        if not ids_str:
            return []

        CHUNK = 900
        for i in range(0, len(ids_str), CHUNK):
            chunk = ids_str[i:i + CHUNK]
            placeholders = ",".join(["?"] * len(chunk))
            db_rows = con.execute(
                f"""SELECT canonical_event_id, event_type, occurred_at, payload_json
                    FROM v_canonical_best_events
                    WHERE action_fingerprint IN ({placeholders})""",
                chunk,
            ).fetchall()

            for r in db_rows:
                try:
                    payload = json.loads(r[3]) if r[3] else {}
                except (ValueError, TypeError):
                    payload = {}
                if not isinstance(payload, dict):
                    payload = {}
                rows.append(CanonicalEventRow(
                    canonical_id=str(r[0]),
                    event_type=str(r[1] or ""),
                    occurred_at=str(r[2] or ""),
                    payload=payload,
                ))

    return rows


def _collect_ids_from_payloads(
    events: List[CanonicalEventRow],
) -> tuple[set, set]:
    """Extract all player IDs and franchise IDs from event payloads."""
    player_ids: set = set()
    franchise_ids: set = set()

    for e in events:
        p = e.payload
        for key in ("player_id", "player"):
            v = p.get(key)
            if v is not None:
                player_ids.add(str(v).strip())

        for key in ("franchise_id", "team_id", "from_franchise_id", "to_franchise_id",
                     "from_team_id", "to_team_id", "winner_franchise_id", "loser_franchise_id",
                     "winner_team_id", "loser_team_id"):
            v = p.get(key)
            if v is not None:
                franchise_ids.add(str(v).strip())

        # Handle list-valued player IDs (added/dropped)
        for key in ("players_added_ids", "players_dropped_ids"):
            v = p.get(key)
            if isinstance(v, list):
                for item in v:
                    if item is not None:
                        player_ids.add(str(item).strip())
            elif isinstance(v, str) and v.strip():
                for item in v.split(","):
                    s = item.strip()
                    if s:
                        player_ids.add(s)

        # Extract IDs from embedded MFL trade JSON (franchise + player IDs)
        raw_mfl = p.get("raw_mfl_json")
        if raw_mfl and isinstance(raw_mfl, str):
            try:
                mfl = json.loads(raw_mfl)
                if isinstance(mfl, dict):
                    for fkey in ("franchise", "franchise2"):
                        fv = mfl.get(fkey)
                        if fv:
                            franchise_ids.add(str(fv).strip())
                    for pkey in ("franchise1_gave_up", "franchise2_gave_up"):
                        pv = mfl.get(pkey, "")
                        if pv:
                            for pid in str(pv).split(","):
                                s = pid.strip()
                                if s:
                                    player_ids.add(s)
            except (ValueError, TypeError):
                pass

    player_ids.discard("")
    franchise_ids.discard("")
    return player_ids, franchise_ids


def _render_text_from_recap_runs(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    *,
    eal_directives: Optional[EALDirectivesV1] = None,
) -> Optional[str]:
    """Render recap text directly from recap_runs data (no recaps table needed).

    Returns rendered text if recap_runs has sufficient data, else None.
    This is the canonical path — it reads from recap_runs which is the
    authoritative process ledger. Includes deterministic event bullets
    with name resolution from franchise_directory and player_directory.
    """
    _ = eal_directives  # EAL v1: accepted but not applied at render layer
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT selection_fingerprint, canonical_ids_json,
                      counts_by_type_json, window_start, window_end
               FROM recap_runs
               WHERE league_id=? AND season=? AND week_index=?""",
            (league_id, season, week_index),
        ).fetchone()

    if not row or not row[0]:
        return None

    fp, ids_json, counts_json, win_start, win_end = row

    try:
        canonical_ids = json.loads(ids_json) if ids_json else []
    except (ValueError, TypeError):
        canonical_ids = []

    try:
        counts_by_type = json.loads(counts_json) if counts_json else {}
    except (ValueError, TypeError):
        counts_by_type = {}

    # Build the structural summary
    artifact = {
        "league_id": league_id,
        "season": season,
        "week_index": week_index,
        "recap_version": 0,
        "window": {"start": win_start, "end": win_end},
        "selection": {
            "fingerprint": fp,
            "event_count": len(canonical_ids) if isinstance(canonical_ids, list) else 0,
            "counts_by_type": counts_by_type if isinstance(counts_by_type, dict) else {},
            "canonical_ids": canonical_ids if isinstance(canonical_ids, list) else [],
        },
    }

    summary = render_recap_text_v1(artifact)

    # Load canonical events and render deterministic bullets with name resolution
    if isinstance(canonical_ids, list) and canonical_ids:
        event_rows = _load_canonical_event_rows(db_path, canonical_ids)

        if event_rows:
            player_ids, franchise_ids = _collect_ids_from_payloads(event_rows)

            # Build resolvers (fail-safe: if directories are empty, IDs pass through)
            player_res = PlayerResolver(db_path, league_id, season)
            franchise_res = FranchiseResolver(db_path, league_id, season)

            if player_ids:
                player_res.load_for_ids(player_ids)
            if franchise_ids:
                franchise_res.load_for_ids(franchise_ids)

            bullets = render_deterministic_bullets_v1(
                event_rows,
                team_resolver=franchise_res.one,
                player_resolver=player_res.one,
            )

            if bullets:
                lines = ["\nWhat happened this week:"]
                for b in bullets:
                    lines.append(f"  - {b}")
                summary += "\n".join(lines) + "\n"

    return summary


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

    Rendering priority:
    1. Render from recap_runs data directly (canonical path, no recaps table needed)
    2. Fall back to legacy recaps.artifact_path if recap_runs data is insufficient
       (emits DeprecationWarning — this path will be removed)
    """
    state = get_recap_run_state(db_path, league_id, season, week_index)
    if state is None:
        raise RecapNotFoundError("No recap_runs row found for that week.")

    # --- EAL v1 writer consumption boundary (read-only) ---
    eal_directives = load_eal_directives_v1(
        db_path=db_path,
        recap_run_id=state,
    )

    # Canonical path: render directly from recap_runs (no recaps table dependency)
    rendered_text = _render_text_from_recap_runs(
        db_path, league_id, season, week_index,
        eal_directives=eal_directives,
    )

    if rendered_text is None:
        # Legacy fallback: read from recaps table + filesystem
        warnings.warn(
            f"generate_weekly_recap_draft: falling back to legacy recaps table "
            f"for league={league_id} season={season} week={week_index}. "
            f"This path is deprecated and will be removed.",
            DeprecationWarning,
            stacklevel=2,
        )
        path = _get_active_artifact_path(db_path, league_id, season, week_index)
        _ensure_artifact_on_disk(path, db_path, league_id, season, week_index)
        rendered_text = render_recap_text_from_path_v1(
            path,
            eal_directives=eal_directives,
        )

    selection_fingerprint, window_start, window_end = _get_recap_run_trace(
        db_path, league_id, season, week_index
    )

    # SV_EAL_V1_BEGIN: Editorial Attunement Layer v1 (restraint-only, metadata-only)
    # NOTE: This must not modify selection, ordering, or facts. It only constrains expression.
    included_count = None
    # Read canonical_ids_json from recap_runs for deterministic included_count.
    # SV_DEFECT1_EAL_FALLBACK_COUNT: fall back to canonical_events table if NULL.
    with DatabaseSession(db_path) as _eal_con:
        _eal_row = _eal_con.execute(
            "SELECT canonical_ids_json FROM recap_runs WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week_index),
        ).fetchone()
        if _eal_row and _eal_row[0]:
            try:
                _ids = json.loads(_eal_row[0])
                if isinstance(_ids, list):
                    included_count = len(_ids)
            except (ValueError, TypeError):
                pass
        # Fallback: if canonical_ids_json is NULL but window bounds are known,
        # count canonical events directly. The data exists in the DB — the
        # recap_runs column just wasn't populated for this week.
        if included_count is None and window_start and window_end:
            _fallback_row = _eal_con.execute(
                "SELECT COUNT(*) FROM canonical_events"
                " WHERE league_id=? AND season=?"
                " AND occurred_at IS NOT NULL"
                " AND occurred_at >= ? AND occurred_at < ?",
                (league_id, int(season), window_start, window_end),
            ).fetchone()
            # SV_DEFECT1_ZERO_COUNT_FIX: COUNT(*)=0 is valid (quiet week).
            # Previous condition `_fallback_row[0] and int(...) > 0` excluded
            # zero because 0 is falsy — gave None instead of 0.
            if _fallback_row is not None:
                included_count = int(_fallback_row[0])
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

    # SV_CREATIVE_LAYER_V1_BEGIN
    # Attempt governed narrative prose draft constrained by EAL directive.
    # Falls back silently to deterministic facts-only if EAL vetoes, key absent, or any error.
    # Facts block is always preserved — narrative is additive only, never a replacement.
    #
    # Context feed: season context + league history + narrative angles + writer room
    # enrichments are derived from canonical data and rendered as text blocks for the
    # creative layer prompt. These are derived, non-authoritative, and never modify facts.
    _creative_bullets: list[str] = []
    _season_context_text = ""
    _league_history_text = ""
    _narrative_angles_text = ""
    _writer_room_text = ""

    with DatabaseSession(db_path) as _cl_con:
        _cl_row = _cl_con.execute(
            "SELECT canonical_ids_json FROM recap_runs"
            " WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week_index),
        ).fetchone()
        if _cl_row and _cl_row[0]:
            try:
                _cl_ids = json.loads(_cl_row[0])
                if isinstance(_cl_ids, list) and _cl_ids:
                    _cl_events = _load_canonical_event_rows(db_path, _cl_ids)
                    if _cl_events:
                        _cl_pids, _cl_fids = _collect_ids_from_payloads(_cl_events)
                        _cl_pres = PlayerResolver(db_path, league_id, season)
                        _cl_fres = FranchiseResolver(db_path, league_id, season)
                        if _cl_pids:
                            _cl_pres.load_for_ids(_cl_pids)
                        if _cl_fids:
                            _cl_fres.load_for_ids(_cl_fids)
                        _creative_bullets = render_deterministic_bullets_v1(
                            _cl_events,
                            team_resolver=_cl_fres.one,
                            player_resolver=_cl_pres.one,
                        )
            except Exception:
                _creative_bullets = []

    # --- Context derivation (all derived, non-authoritative, silent on failure) ---
    try:
        _cl_name_map = build_cross_season_name_resolver(db_path, league_id)
    except Exception:
        _cl_name_map = {}

    try:
        _cl_season_ctx = derive_season_context_v1(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _season_context_text = render_season_context_for_prompt(
            _cl_season_ctx, team_resolver=lambda fid: _cl_name_map.get(fid, fid),
        )
    except Exception:
        _cl_season_ctx = None

    try:
        _cl_history_ctx = derive_league_history_v1(db_path=db_path, league_id=league_id)
        _league_history_text = render_league_history_for_prompt(
            _cl_history_ctx, name_map=_cl_name_map,
        )
    except Exception:
        _cl_history_ctx = None

    try:
        _cl_all_matchups = load_all_matchups(db_path, league_id)
    except Exception:
        _cl_all_matchups = None

    try:
        if _cl_season_ctx is not None:
            _cl_angles = detect_narrative_angles_v1(
                season_ctx=_cl_season_ctx,
                history_ctx=_cl_history_ctx,
                all_matchups=_cl_all_matchups,
            )
            _narrative_angles_text = render_angles_for_prompt(
                _cl_angles, name_map=_cl_name_map,
            )
    except Exception:
        pass

    try:
        _cl_deltas = derive_scoring_deltas(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _cl_faab = derive_faab_spending(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _writer_room_text = render_writer_room_context_for_prompt(
            deltas=_cl_deltas, faab=_cl_faab, name_map=_cl_name_map,
        )
    except Exception:
        pass

    # Read governed tone preset (commissioner-configured, defaults to POINTED)
    try:
        _cl_tone_preset = get_tone_preset(db_path, league_id)
    except Exception:
        _cl_tone_preset = ""

    _narrative_draft = draft_narrative_v1(
        facts_bullets=_creative_bullets,
        eal_directive=editorial_attunement_v1,
        league_id=league_id,
        season=season,
        week_index=week_index,
        season_context=_season_context_text,
        league_history=_league_history_text,
        narrative_angles=_narrative_angles_text,
        writer_room_context=_writer_room_text,
        tone_preset=_cl_tone_preset,
    )
    if _narrative_draft:
        rendered_text = (
            rendered_text.rstrip()
            + "\n\n--- Narrative Draft (AI-assisted, requires human approval) ---\n"
            + _narrative_draft
            + "\n"
        )
    # SV_CREATIVE_LAYER_V1_END

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
    with DatabaseSession(db_path) as con:
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

    if not row:
        raise RecapNotFoundError("No DRAFT WEEKLY_RECAP artifact found to approve for that week.")

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
