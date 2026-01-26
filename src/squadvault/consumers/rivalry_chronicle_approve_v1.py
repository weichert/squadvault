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
    require_draft: bool


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

        if req.require_draft and st != "DRAFT":
            print(
                f"ERROR: require-draft set, but latest is state={st!r} "
                f"for v{v} ({ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1})."
            )
            return 2

        fn = _find_approve_primitive()

        # Call core approve primitive with signature-filtered kwargs.
        # We pass both common naming variants to survive drift.
        _sv_call_with_signature_filter(
            fn,
            con=con,
            conn=con,
            league_id=req.league_id,
            season=req.season,
            week_index=req.week_index,
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=v,
            approved_by=req.approved_by,
            approved_at=None,  # allow core default/now semantics
        )

        print(f"rivalry_chronicle_approve_v1: OK (approved v{v}; artifact_type={ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1})")
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
    ap.add_argument("--require-draft", action="store_true")
    args = ap.parse_args(argv)

    req = ApproveRequest(
        db=str(args.db),
        league_id=int(args.league_id),
        season=int(args.season),
        week_index=int(args.week_index),
        approved_by=str(args.approved_by),
        require_draft=bool(args.require_draft),
    )
    return int(approve_latest(req))


if __name__ == "__main__":
    raise SystemExit(main())
