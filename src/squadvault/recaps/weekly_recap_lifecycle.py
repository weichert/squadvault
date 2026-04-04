"""Weekly recap lifecycle: draft generation, approval, and state management."""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass

from squadvault.ai.creative_layer_v1 import draft_narrative_v1
from squadvault.core.eal.consume_v1 import EALDirectivesV1, load_eal_directives_v1
from squadvault.core.eal.editorial_attunement_v1 import EALMeta, evaluate_editorial_attunement_v1
from squadvault.core.recaps.context.auction_draft_angles_v1 import (
    detect_auction_draft_angles_v1,
)
from squadvault.core.recaps.context.bye_week_context_v1 import (
    detect_bye_week_angles_v1,
)
from squadvault.core.recaps.context.franchise_deep_angles_v1 import (
    detect_franchise_deep_angles_v1,
)
from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
    compute_franchise_tenures,
    derive_league_history_v1,
    load_all_matchups,
    render_league_history_for_prompt,
)
from squadvault.core.recaps.context.league_rules_context_v1 import (
    detect_scoring_rules_angles_v1,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    NarrativeAngle,
    detect_narrative_angles_v1,
)
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    detect_player_narrative_angles_v1,
)
from squadvault.core.recaps.context.player_week_context_v1 import (
    derive_player_week_context_v1,
    render_player_highlights_for_prompt,
)
from squadvault.core.recaps.context.season_context_v1 import (
    derive_season_context_v1,
    render_season_context_for_prompt,
)
from squadvault.core.recaps.context.writer_room_context_v1 import (
    derive_faab_spending,
    derive_scoring_deltas,
    render_writer_room_context_for_prompt,
)
from squadvault.core.recaps.recap_artifacts import latest_approved_version
from squadvault.core.recaps.recap_runs import (
    get_recap_run_state,
    sync_recap_run_state_from_artifacts,
)
from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    CanonicalEventRow,
    render_deterministic_bullets_v1,
)
from squadvault.core.recaps.render.render_recap_text_v1 import (
    render_recap_text_v1,
)
from squadvault.core.recaps.verification.recap_verifier_v1 import (
    VerificationResult,
    verify_recap_v1,
)
from squadvault.core.resolvers import FranchiseResolver, PlayerResolver, build_player_name_map
from squadvault.core.storage.session import DatabaseSession
from squadvault.core.tone.tone_profile_v1 import get_tone_preset
from squadvault.core.tone.voice_profile_v1 import get_voice_profile
from squadvault.errors import RecapDataError, RecapNotFoundError, RecapStateError
from squadvault.recaps.preflight import check_duplicate_matchup_week

ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"

logger = logging.getLogger(__name__)




# =============================================================================
# Public result types
# =============================================================================

@dataclass(frozen=True)
class GenerateDraftResult:
    version: int
    created_new: bool
    selection_fingerprint: str
    window_start: str | None
    window_end: str | None
    prev_approved_version: int | None
    synced_recap_run_state: str | None
    reason: str
    verification_result: VerificationResult | None = None
    verification_attempts: int = 0


@dataclass(frozen=True)
class ApproveResult:
    approved_version: int
    superseded_version: int | None
    synced_recap_run_state: str | None


# =============================================================================
# Internal helpers (ported from your existing script behavior)
# =============================================================================

def _utc_now_sql() -> str:
    """Return SQL expression for current UTC timestamp."""
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"




# SV_FIX_GET_RECAP_RUN_TRACE_OPTIONAL_EAL_RETURN_V1
def _get_recap_run_trace(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> tuple[str, str | None, str | None]:
    """Reads selection_fingerprint + window bounds from recap_runs."""
    with DatabaseSession(db_path) as con:
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

        latest_v: int | None = None
        latest_fp: str | None = None

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
) -> int | None:
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
) -> tuple[int, int | None]:
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



# =============================================================================
# Canonical lifecycle API (scripts should call ONLY these)
# =============================================================================

def _load_canonical_event_rows(
    db_path: str,
    canonical_ids: list[str],
) -> list[CanonicalEventRow]:
    """Load canonical event rows with payloads from v_canonical_best_events.

    canonical_ids are action fingerprints stored in recap_runs.canonical_ids_json.
    Returns CanonicalEventRow objects suitable for the bullets renderer.
    IDs that don't resolve are silently skipped (defensive).
    """
    if not canonical_ids:
        return []

    rows: list[CanonicalEventRow] = []
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
    events: list[CanonicalEventRow],
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
    eal_directives: EALDirectivesV1 | None = None,
) -> str | None:
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


@dataclass(frozen=True)
class _PromptContext:
    """All derived, non-authoritative context fed to the creative layer prompt."""

    season_context_text: str
    league_history_text: str
    narrative_angles_text: str
    writer_room_text: str
    player_highlights_text: str
    tone_preset: str
    voice_profile: str
    seasons_count: int


def _derive_prompt_context(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    window_end: str | None,
) -> _PromptContext:
    """Derive all non-authoritative context blocks for the creative layer prompt.

    Every derivation is wrapped in try/except — failure is silent (debug-logged)
    and produces an empty default. This is consistent with the governing principle
    that context enrichments are derived, never fact-creating.
    """
    season_context_text = ""
    league_history_text = ""
    narrative_angles_text = ""
    writer_room_text = ""
    _tenure_map = None
    _history_ctx = None
    _season_ctx = None
    _all_matchups = None

    # -- Name resolution --
    try:
        _name_map = build_cross_season_name_resolver(db_path, league_id)
    except Exception as e:
        logger.debug("Cross-season name resolver failed: %s", e)
        _name_map = {}

    _player_name_map: dict[str, str] = {}
    try:
        _player_name_map = build_player_name_map(db_path, league_id)
    except Exception as e:
        logger.debug("Player name map failed: %s", e)

    # -- Season context --
    try:
        _season_ctx = derive_season_context_v1(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        season_context_text = render_season_context_for_prompt(
            _season_ctx, team_resolver=lambda fid: _name_map.get(fid, fid),
        )
    except Exception as e:
        logger.debug("Season context derivation failed: %s", e)
        _season_ctx = None

    # -- League history --
    try:
        _history_ctx = derive_league_history_v1(db_path=db_path, league_id=league_id)
        _tenure_map = compute_franchise_tenures(db_path, league_id)
        league_history_text = render_league_history_for_prompt(
            _history_ctx, name_map=_name_map, tenure_map=_tenure_map,
        )
    except Exception as e:
        logger.debug("League history context failed: %s", e)
        _history_ctx = None

    # -- Historical matchups --
    try:
        _all_matchups = load_all_matchups(db_path, league_id)
    except Exception as e:
        logger.debug("Load all matchups failed: %s", e)
        _all_matchups = None

    # -- Narrative angle detection (all 6 modules → unified budget) --
    try:
        _all_angles: list[NarrativeAngle] = []

        if _season_ctx is not None:
            _cl_angles = detect_narrative_angles_v1(
                season_ctx=_season_ctx,
                history_ctx=_history_ctx,
                all_matchups=_all_matchups,
                tenure_map=_tenure_map,
                fname=lambda fid: _name_map.get(fid, fid),
            )
            _all_angles.extend(_cl_angles.angles)

        try:
            _all_angles.extend(detect_player_narrative_angles_v1(
                db_path=db_path, league_id=league_id, season=season, week=week_index,
                tenure_map=_tenure_map,
                pname=lambda pid: _player_name_map.get(pid, pid),
                fname=lambda fid: _name_map.get(fid, fid),
            ))
        except Exception as e:
            logger.debug("Player narrative angles failed: %s", e)

        try:
            _all_angles.extend(detect_auction_draft_angles_v1(
                db_path=db_path, league_id=league_id, season=season, week=week_index,
                pname=lambda pid: _player_name_map.get(pid, pid),
                fname=lambda fid: _name_map.get(fid, fid),
            ))
        except Exception as e:
            logger.debug("Auction draft angles failed: %s", e)

        try:
            _all_angles.extend(detect_franchise_deep_angles_v1(
                db_path=db_path, league_id=league_id, season=season, week=week_index,
                tenure_map=_tenure_map,
                pname=lambda pid: _player_name_map.get(pid, pid),
                fname=lambda fid: _name_map.get(fid, fid),
            ))
        except Exception as e:
            logger.debug("Franchise deep angles failed: %s", e)

        try:
            _all_angles.extend(detect_bye_week_angles_v1(
                db_path=db_path, league_id=league_id, season=season, week=week_index,
                all_matchups=_all_matchups,
                fname=lambda fid: _name_map.get(fid, fid),
            ))
        except Exception as e:
            logger.debug("Bye week angles failed: %s", e)

        try:
            _all_angles.extend(detect_scoring_rules_angles_v1(
                db_path=db_path, league_id=league_id, season=season, week=week_index,
            ))
        except Exception as e:
            logger.debug("Scoring rules angles failed: %s", e)

        _all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))

        # Tiered angle budget (per scope doc):
        #   HEADLINE (strength 3): cap 3, NOTABLE (strength 2): cap 6,
        #   MINOR (strength 1): cap 4 (only if total < 12). Total cap: 15.
        if _all_angles:
            budgeted: list[NarrativeAngle] = []
            h_count = n_count = m_count = 0
            for a in _all_angles:
                if a.strength >= 3 and h_count < 3:
                    budgeted.append(a)
                    h_count += 1
                elif a.strength == 2 and n_count < 6:
                    budgeted.append(a)
                    n_count += 1
                elif a.strength <= 1 and m_count < 4 and len(budgeted) < 12:
                    budgeted.append(a)
                    m_count += 1

            lines: list[str] = [
                f"Narrative angles for Week {week_index} (what's interesting):",
                "IMPORTANT: Each angle is about the NAMED franchise ONLY. "
                "Never apply an angle about one franchise to a different franchise.",
            ]
            for a in budgeted:
                slabel = {3: "HEADLINE", 2: "NOTABLE", 1: "MINOR"}.get(a.strength, "")
                # Resolve franchise names for attribution tag
                fnames = [_name_map.get(fid, fid) for fid in a.franchise_ids if fid]
                ftag = f" [RE: {', '.join(fnames)}]" if fnames else ""
                line = f"  [{slabel}]{ftag} {a.headline}"
                if a.detail:
                    line += f" — {a.detail}"
                lines.append(line)
            remaining = len(_all_angles) - len(budgeted)
            if remaining > 0:
                lines.append(f"  (+ {remaining} minor angles omitted)")
            narrative_angles_text = "\n".join(lines) + "\n"
    except Exception as e:
        logger.debug("Narrative angle rendering failed: %s", e)

    # -- Writer room context (scoring deltas + FAAB) --
    try:
        _deltas = derive_scoring_deltas(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
        )
        _faab = derive_faab_spending(
            db_path=db_path, league_id=league_id, season=season, week_index=week_index,
            through_occurred_at=window_end,
        )
        writer_room_text = render_writer_room_context_for_prompt(
            deltas=_deltas, faab=_faab,
            name_map=_name_map,
        )
    except Exception as e:
        logger.debug("Writer room context failed: %s", e)

    # -- Player highlights (per-franchise starter/bench scoring) --
    player_highlights_text = ""
    try:
        _player_ctx = derive_player_week_context_v1(
            db_path=db_path, league_id=league_id, season=season, week=week_index,
        )
        if _player_ctx.has_data:
            _ph_pres = PlayerResolver(db_path, league_id, season)
            _ph_fres = FranchiseResolver(db_path, league_id, season)
            _ph_pids: set[str] = set()
            _ph_fids: set[str] = set()
            for _fc in _player_ctx.franchises:
                _ph_fids.add(_fc.franchise_id)
                for _ps in _fc.starters:
                    _ph_pids.add(_ps.player_id)
                for _ps in _fc.bench:
                    _ph_pids.add(_ps.player_id)
            if _ph_pids:
                _ph_pres.load_for_ids(_ph_pids)
            if _ph_fids:
                _ph_fres.load_for_ids(_ph_fids)
            player_highlights_text = render_player_highlights_for_prompt(
                _player_ctx,
                team_resolver=_ph_fres.one,
                player_resolver=_ph_pres.one,
            )
    except Exception as e:
        logger.debug("Player highlights derivation failed: %s", e)

    # -- Tone & voice --
    tone_preset = ""
    try:
        tone_preset = get_tone_preset(db_path, league_id)
    except Exception as e:
        logger.debug("Tone preset lookup failed: %s", e)

    voice_profile = ""
    try:
        voice_profile = get_voice_profile(db_path, league_id) or ""
    except Exception as e:
        logger.debug("Voice profile lookup failed: %s", e)

    return _PromptContext(
        season_context_text=season_context_text,
        league_history_text=league_history_text,
        narrative_angles_text=narrative_angles_text,
        writer_room_text=writer_room_text,
        player_highlights_text=player_highlights_text,
        tone_preset=tone_preset,
        voice_profile=voice_profile,
        seasons_count=(
            len(_history_ctx.seasons_available) if _history_ctx is not None else 0
        ),
    )


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

    Renders from recap_runs data directly (canonical path, no recaps table needed).
    Raises RecapDataError if recap_runs has insufficient data for rendering.
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
        raise RecapDataError(
            f"Cannot render recap for league={league_id} season={season} "
            f"week={week_index}: recap_runs has insufficient data. "
            f"Ensure the week has been processed (ingest → canonicalize → select)."
        )

    selection_fingerprint, window_start, window_end = _get_recap_run_trace(
        db_path, league_id, season, week_index
    )

    # SV_EAL_V1_BEGIN: Editorial Attunement Layer v1 (restraint-only, metadata-only)
    # NOTE: This must not modify selection, ordering, or facts. It only constrains expression.
    included_count = None
    _is_playoff = False
    # Read canonical_ids_json from recap_runs for deterministic included_count.
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

        # Playoff detection: find the last week with full matchup count (= last regular
        # season week). Any week after that is a playoff, even if it has no matchup results.
        try:
            _last_regular_row = _eal_con.execute(
                "SELECT MAX(week) FROM ("
                "  SELECT CAST(json_extract(payload_json, '$.week') AS INTEGER) as week,"
                "         COUNT(*) as cnt"
                "  FROM v_canonical_best_events"
                "  WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
                "  GROUP BY json_extract(payload_json, '$.week')"
                "  HAVING cnt = ("
                "    SELECT MAX(cnt2) FROM ("
                "      SELECT COUNT(*) as cnt2 FROM v_canonical_best_events"
                "      WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
                "      GROUP BY json_extract(payload_json, '$.week')"
                "    )"
                "  )"
                ")",
                (league_id, season, league_id, season),
            ).fetchone()
            _last_regular_week = _last_regular_row[0] if _last_regular_row else None
            if _last_regular_week and week_index > _last_regular_week:
                _is_playoff = True
        except Exception:
            pass  # Playoff detection is best-effort; default to non-playoff

        # If canonical_ids_json is NULL or empty string, included_count stays None
        # (unknown). This is distinct from "[]" which parses to 0 (zero events selected).
        # None → EAL_LOW_CONFIDENCE_RESTRAINT (restrained but not silenced).
        # 0 → EAL_AMBIGUITY_PREFER_SILENCE (silenced).
    meta = EALMeta(
        has_selection_set=True,
        has_window=True,
        included_count=included_count,
        excluded_count=None,
        is_playoff=_is_playoff,
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

    # Duplicate matchup gate: skip creative layer if all matchups duplicate the prior week.
    # MFL sometimes records championship results in multiple week slots.
    _dup_verdict = check_duplicate_matchup_week(db_path, league_id, season, week_index)
    _skip_creative = False
    if _dup_verdict is not None:
        logger.debug(
            "Duplicate matchup week detected (week %d): %s",
            week_index, _dup_verdict.evidence,
        )
        rendered_text = (
            rendered_text.rstrip()
            + f"\n\nNote: Week {week_index} matchup results are identical to week {week_index - 1}. "
            + "This appears to be a platform duplicate, not a distinct game. "
            + "Creative narrative skipped — silence over fabrication.\n"
        )
        _skip_creative = True

    _creative_bullets: list[str] = []

    # Maximum verification retry attempts before falling back to facts-only.
    # Each attempt is an independent LLM call — stochastic output means
    # different drafts may pass verification even with identical inputs.
    _MAX_VERIFICATION_RETRIES = 3
    _verification_result: VerificationResult | None = None
    _verification_attempts = 0

    if not _skip_creative:
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
                except Exception as e:
                    logger.debug("Creative bullets rendering failed: %s", e)
                    _creative_bullets = []

        _ctx = _derive_prompt_context(
            db_path=db_path, league_id=league_id, season=season,
            week_index=week_index, window_end=window_end,
        )

        # Save pre-narrative rendered text — reset to this on each retry
        _base_rendered_text = rendered_text

        # SV_VERIFICATION_RETRY_LOOP_BEGIN
        _retry_feedback = ""  # Verification corrections for retry attempts
        for _attempt in range(1, _MAX_VERIFICATION_RETRIES + 1):
            _verification_attempts = _attempt

            # Reset to pre-narrative state
            rendered_text = _base_rendered_text

            _narrative_draft = draft_narrative_v1(
                facts_bullets=_creative_bullets,
                eal_directive=editorial_attunement_v1,
                league_id=league_id,
                season=season,
                week_index=week_index,
                season_context=_ctx.season_context_text,
                league_history=_ctx.league_history_text,
                narrative_angles=_ctx.narrative_angles_text,
                writer_room_context=_ctx.writer_room_text,
                player_highlights=_ctx.player_highlights_text,
                tone_preset=_ctx.tone_preset,
                voice_profile=_ctx.voice_profile,
                seasons_count=_ctx.seasons_count,
                verification_feedback=_retry_feedback,
            )

            if not _narrative_draft:
                # No narrative produced (API key missing, EAL silence, etc.)
                # Nothing to verify — exit loop.
                break

            rendered_text = (
                rendered_text.rstrip()
                + "\n\n--- SHAREABLE RECAP ---\n"
                + _narrative_draft
                + "\n--- END SHAREABLE RECAP ---\n"
            )

            # Verify the draft against canonical data
            try:
                _verification_result = verify_recap_v1(
                    rendered_text,
                    db_path=db_path,
                    league_id=league_id,
                    season=season,
                    week=week_index,
                )
            except Exception as e:
                logger.debug("Verification V1 failed on attempt %d: %s", _attempt, e)
                _verification_result = None
                break  # Verification error — keep this draft, don't retry

            if _verification_result.passed:
                logger.debug(
                    "Verification V1: passed on attempt %d (%d checks) "
                    "for league=%s season=%d week=%d",
                    _attempt, _verification_result.checks_run,
                    league_id, season, week_index,
                )
                break  # Clean draft — done

            # Hard failure(s) detected
            if _attempt < _MAX_VERIFICATION_RETRIES:
                # Build correction feedback for the next attempt
                _fb_lines: list[str] = []
                for _vf in _verification_result.hard_failures:
                    _fb_lines.append(
                        f"- ERROR: {_vf.claim}. CORRECTION: {_vf.evidence}"
                    )
                _retry_feedback = "\n".join(_fb_lines)

                logger.info(
                    "Verification V1: %d hard failure(s) on attempt %d/%d, "
                    "retrying with corrections — league=%s season=%d week=%d",
                    _verification_result.hard_failure_count,
                    _attempt, _MAX_VERIFICATION_RETRIES,
                    league_id, season, week_index,
                )
            else:
                # All retries exhausted — fall back to facts-only.
                # Silence over fabrication: if the model can't produce a clean
                # draft after N attempts, the narrative is not trustworthy.
                _fail_details = "; ".join(
                    f"[{f.category}] {f.claim}"
                    for f in _verification_result.hard_failures
                )
                logger.warning(
                    "Verification V1: failed after %d attempt(s), falling back "
                    "to facts-only — league=%s season=%d week=%d — %s",
                    _attempt, league_id, season, week_index, _fail_details,
                )
                rendered_text = (
                    _base_rendered_text.rstrip()
                    + "\n\nNote: Narrative draft failed verification after "
                    + f"{_attempt} attempt(s). Falling back to facts-only "
                    + "output — silence over fabrication.\n"
                )
        # SV_VERIFICATION_RETRY_LOOP_END
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
        verification_result=_verification_result,
        verification_attempts=_verification_attempts,
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
