#!/usr/bin/env python3
"""
Approve Rivalry Chronicle v1 (lifecycle-aligned).

Hard constraints:
- Reuse recap_artifacts state machine semantics (DRAFT -> APPROVED, supersede prior APPROVED).
- Do NOT touch recap_runs (weekly run table is weekly recap scoped).
- Deterministic + minimal: no narrative generation; rendered_text stays as-is.
"""

from __future__ import annotations

import argparse
import inspect
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1


def _sv_call_with_signature_filter(fn: Callable[..., Any], **kwargs: Any) -> Any:
    sig = inspect.signature(fn)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return fn(**filtered)


def _db_connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def _latest_version_and_state(
    con: sqlite3.Connection,
    *,
    league_id: int,
    season: int,
    week_index: int,
    artifact_type: str,
) -> tuple[Optional[int], Optional[str]]:
    row = con.execute(
        """
        SELECT version, state
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
        ORDER BY version DESC
        LIMIT 1
        """,
        (str(league_id), int(season), int(week_index), str(artifact_type)),
    ).fetchone()
    if not row:
        return None, None
    return int(row["version"]), str(row["state"] or "")



# LOCK_E_APPROVE_LATEST_DRAFT_V3
def _latest_draft_version(
    con: sqlite3.Connection,
    *,
    league_id: int,
    season: int,
    week_index: int,
    artifact_type: str,
) -> Optional[int]:
    """
    Return latest DRAFT version for this key. If none exists, return None.
    """
    row = con.execute(
        """
        SELECT version
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND state='DRAFT'
        ORDER BY version DESC
        LIMIT 1
        """,
        (str(league_id), int(season), int(week_index), str(artifact_type)),
    ).fetchone()
    if not row:
        return None
    return int(row["version"])
def _find_approve_primitive() -> Callable[..., Any]:
    # Prefer explicit names, but fall back to "any callable with approve in the name".
    from squadvault.core.recaps import recap_artifacts as ra

    candidates = [
        "approve_recap_artifact",
        "approve_recap_artifact_version",
        "approve_artifact",
        "approve_artifact_version",
        "set_artifact_approved",
    ]
    for name in candidates:
        fn = getattr(ra, name, None)
        if callable(fn):
            return fn

    for name in dir(ra):
        if "approve" in name.lower():
            fn = getattr(ra, name, None)
            if callable(fn):
                return fn

    raise RuntimeError("No approve primitive found in squadvault.core.recaps.recap_artifacts")


@dataclass(frozen=True)
class ApproveRequest:
    db: str
    league_id: int
    season: int
    week_index: int
    approved_by: str
    approved_at_utc: Optional[str] = None
    require_draft: bool = False
def approve_latest(req: ApproveRequest) -> int:
    con = _db_connect(req.db)
    try:
        v, st = _latest_version_and_state(
            con,
            league_id=req.league_id,
            season=req.season,
            week_index=req.week_index,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
        )
        if v is None:
            print(
                f"ERROR: No {ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1} artifact found "
                f"(league_id={req.league_id} season={req.season} week_index={req.week_index})."
            )
            return 2

        # LOCK_E_IDEMPOTENT_IF_APPROVED_V7
        # Idempotency: if any APPROVED exists for this key, treat as success and do nothing.
        # This prevents retro-approving older drafts after an approval already exists.
        row = con.execute(
            """
            SELECT 1
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND state='APPROVED'
            LIMIT 1
            """,
            (str(req.league_id), int(req.season), int(req.week_index), str(ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1)),
        ).fetchone()
        if row:
            print(
                f"rivalry_chronicle_approve_v1: OK (idempotent; already approved; artifact_type={ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1})"
            )
            return 0


        draft_v = _latest_draft_version(
            con,
            league_id=req.league_id,
            season=req.season,
            week_index=req.week_index,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
        )

        if draft_v is None:
            if req.require_draft:
                print(
                    f"ERROR: require-draft set, but no DRAFT exists "
                    f"for v_latest={v} state_latest={st!r} "
                    f"({ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1})."
                )
                return 2

            # Idempotency: if an APPROVED exists, treat as success.
            row = con.execute(
                """
                SELECT 1
                FROM recap_artifacts
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND state='APPROVED'
                LIMIT 1
                """,
                (str(req.league_id), int(req.season), int(req.week_index), str(ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1)),
            ).fetchone()
            if row:
                print(
                    f"rivalry_chronicle_approve_v1: OK (idempotent; already approved; artifact_type={ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1})"
                )
                return 0

            print(
                f"ERROR: No DRAFT exists and no APPROVED exists "
                f"for (league_id={req.league_id} season={req.season} week_index={req.week_index}) "
                f"artifact_type={ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1}."
            )
            return 2
        fn = _find_approve_primitive()

        # Call core approve primitive with signature-filtered kwargs.
        # We pass both common naming variants to survive drift.
        # LOCK_E_DB_PATH_COMPAT_V6
        sig = inspect.signature(fn)
        params = set(sig.parameters.keys())
        common = dict(
            league_id=req.league_id,
            season=req.season,
            week_index=req.week_index,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=draft_v,
            approved_by=req.approved_by,
            approved_at=req.approved_at_utc,
            approved_at_utc=req.approved_at_utc,
        )
        # Some core primitives require db_path (and open their own connection),
        # others accept an existing connection via con/conn. Support both.
        # SV_PATCH_APPROVE_GUARD_CANON_V1: single unconditional empty-text guard (draft row; deterministic)
        # Guard: never approve an empty Rivalry Chronicle. Validate the DRAFT row's rendered_text.
        row = con.execute(
            """
            SELECT rendered_text
            FROM recap_artifacts
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = ?
              AND version = ?
              AND state = 'DRAFT'
            ORDER BY version DESC, id DESC
            LIMIT 1
            """,
            (int(req.league_id), int(req.season), int(req.week_index), str(ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1), int(draft_v)),
        ).fetchone()
        txt = "" if row is None else str(row[0] or "")
        if not txt.strip():
            raise SystemExit(
                "ERROR: refusing to approve empty Rivalry Chronicle rendered_text. "
                "Re-run generate; no APPROVED stamp was applied."
            )

        if "db_path" in params:
            _sv_call_with_signature_filter(fn, db_path=req.db, **common)
        elif "db" in params:
            _sv_call_with_signature_filter(fn, db=req.db, **common)
        else:
            _sv_call_with_signature_filter(fn, con=con, conn=con, **common)


        print(f"rivalry_chronicle_approve_v1: OK (approved v{draft_v}; artifact_type={ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1})")
        return 0

    finally:
        con.close()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Approve latest Rivalry Chronicle v1 draft (lifecycle-aligned).")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", type=int, required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True, help="Storage week_index anchor (use start_week).")
    ap.add_argument("--approved-by", dest="approved_by", required=True)
    ap.add_argument("--approved-at-utc", dest="approved_at_utc", default=None)
    ap.add_argument("--require-draft", action="store_true")
    args = ap.parse_args(argv)

    req = ApproveRequest(
        db=str(args.db),
        league_id=int(args.league_id),
        season=int(args.season),
        week_index=int(args.week_index),
        approved_by=str(args.approved_by),
        approved_at_utc=getattr(args, 'approved_at_utc', None),
        require_draft=bool(args.require_draft),
    )
    return int(approve_latest(req))


if __name__ == "__main__":
    raise SystemExit(main())

# LOCK_E_APPROVED_AT_UTC_OPTIONAL_V8

# LOCK_E_DATACLASS_DEFAULT_ORDER_FIX_V9

# LOCK_E_PLUMB_ARGS_APPROVED_AT_UTC_INTO_REQUEST_V11
