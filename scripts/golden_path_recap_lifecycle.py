#!/usr/bin/env python3
"""
Golden path: Weekly recap lifecycle (ledger-sync aware, idempotency aware)

This script is a validation harness. It MUST NOT implement lifecycle writes itself.
All artifact draft creation and approvals must go through the canonical lifecycle:

- squadvault.recaps.weekly_recap_lifecycle.generate_weekly_recap_draft
- squadvault.recaps.weekly_recap_lifecycle.approve_latest_weekly_recap

Golden-path outcomes after regen:
A) Delta detected OR forced: new DRAFT created -> approve it (explicit)
B) No delta: no new DRAFT created -> skip approval cleanly
"""

from __future__ import annotations

import argparse
import sqlite3
import subprocess

import sys
from dataclasses import dataclass

from typing import Optional

from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)


RUN_STATES = {"REVIEW_REQUIRED", "APPROVED"}
ARTIFACT_STATES = {"DRAFT", "READY", "APPROVED", "WITHHELD", "SUPERSEDED"}


@dataclass(frozen=True)
class LatestArtifact:
    version: int
    state: str
    supersedes_version: Optional[int]
    approved_by: Optional[str]
    approved_at: Optional[str]

import sys

def _print_ok(msg: str) -> None:
    try:
        print(msg)
    except BrokenPipeError:
        # stdout closed by downstream (e.g., head). Exit cleanly.
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(0)

def sh(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_run_state(conn: sqlite3.Connection, league_id: str, season: int, week_index: int) -> Optional[str]:
    row = conn.execute(
        """
        SELECT state
        FROM recap_runs
        WHERE league_id=? AND season=? AND week_index=?
        """,
        (league_id, season, week_index),
    ).fetchone()
    return None if row is None else str(row["state"])


def get_run_reason(conn: sqlite3.Connection, league_id: str, season: int, week_index: int) -> Optional[str]:
    row = conn.execute(
        """
        SELECT reason
        FROM recap_runs
        WHERE league_id=? AND season=? AND week_index=?
        """,
        (league_id, season, week_index),
    ).fetchone()
    return None if row is None else (None if row["reason"] is None else str(row["reason"]))


def get_latest_artifact(conn: sqlite3.Connection, league_id: str, season: int, week_index: int) -> Optional[LatestArtifact]:
    row = conn.execute(
        """
        SELECT version, state, supersedes_version, approved_by, approved_at
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    ).fetchone()
    if row is None:
        return None
    return LatestArtifact(
        version=int(row["version"]),
        state=str(row["state"]),
        supersedes_version=None if row["supersedes_version"] is None else int(row["supersedes_version"]),
        approved_by=None if row["approved_by"] is None else str(row["approved_by"]),
        approved_at=None if row["approved_at"] is None else str(row["approved_at"]),
    )


def assert_in(value: str, allowed: set[str], label: str) -> None:
    if value not in allowed:
        raise AssertionError(f"{label}={value!r} not in allowed={sorted(allowed)}")


def assert_no_approved_ledger_sync(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
    context: str,
) -> None:
    """
    Invariant: never allow APPROVED + LEDGER_SYNC.
    If reason=LEDGER_SYNC, the run must not be APPROVED.
    """
    state = get_run_state(conn, league_id, season, week_index)
    reason = get_run_reason(conn, league_id, season, week_index)

    if state is None:
        raise AssertionError(f"{context}: recap_runs row missing.")

    if state == "APPROVED" and reason == "LEDGER_SYNC":
        raise AssertionError(
            f"{context}: illegal state detected — recap_runs.state='APPROVED' with reason='LEDGER_SYNC'."
        )


def run_week_render(db_path: str, league_id: str, season: int, week_index: int) -> None:
    """
    Render step (selection + render) remains a consumer invocation.
    This harness does NOT mint recap_artifacts here; artifact creation is via lifecycle.
    """
    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_week_render.py",
        "--db",
        db_path,
        "--league-id",
        league_id,
        "--season",
        str(season),
        "--week-index",
        str(week_index),
        "--suppress-render-warning",
    ]
    sh(cmd)


def regen_via_lifecycle(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    reason: str,
    created_by: str,
    force: bool,
):
    """
    Canonical: mint a DRAFT via lifecycle (fingerprint-idempotent unless forced).
    Returns the lifecycle result so main() can decide whether approval is applicable.
    """
    res = generate_weekly_recap_draft(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        reason=reason,
        created_by=created_by,
        force=force,
    )
    print("\n=== Lifecycle: generate_weekly_recap_draft ===")
    print(res)
    return res


def approve_via_lifecycle(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    approved_by: str,
):
    """
    Canonical: approve latest DRAFT via lifecycle.
    """
    res = approve_latest_weekly_recap(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        approved_by=approved_by,
    )
    print("\n=== Lifecycle: approve_latest_weekly_recap ===")
    print(res)
    return res


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)
    p.add_argument("--approved-by", default=None)
    p.add_argument("--legacy-force", action="store_true")
    p.add_argument("--no-force-fallback", action="store_true")
    args = p.parse_args()

    db_path = args.db
    league_id = args.league_id
    season = args.season
    week_index = args.week_index
    approved_by = args.approved_by or "system"

    force = bool(args.legacy_force)

    with db_connect(db_path) as conn:
        before_state = get_run_state(conn, league_id, season, week_index)
        before_art = get_latest_artifact(conn, league_id, season, week_index)

    print("\n=== Entry ===")
    print(f"Before: recap_runs.state={before_state!r}, latest_artifact={before_art}")

    if before_state is not None:
        assert_in(before_state, RUN_STATES, "recap_runs.state")
    if before_art is not None:
        assert_in(before_art.state, ARTIFACT_STATES, "latest_artifact.state")

    with db_connect(db_path) as conn:
        assert_no_approved_ledger_sync(conn, league_id, season, week_index, context="entry")

    # Phase 1: render
    print("\n=== Phase 1: render ===")
    run_week_render(db_path, league_id, season, week_index)

    with db_connect(db_path) as conn:
        mid_state = get_run_state(conn, league_id, season, week_index)
        mid_art = get_latest_artifact(conn, league_id, season, week_index)
        assert_no_approved_ledger_sync(conn, league_id, season, week_index, context="post-render")

    print(f"After render: recap_runs.state={mid_state!r}, latest_artifact={mid_art}")

    # Phase 2: regenerate draft via lifecycle
    print("\n=== Phase 2: regenerate draft via lifecycle ===")
    regen_res = regen_via_lifecycle(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        reason="LEDGER_SYNC",
        created_by=approved_by,
        force=force,
    )

    with db_connect(db_path) as conn:
        after_regen_state = get_run_state(conn, league_id, season, week_index)
        after_regen_art = get_latest_artifact(conn, league_id, season, week_index)
        assert_no_approved_ledger_sync(conn, league_id, season, week_index, context="post-regen")

    print(f"After regen: recap_runs.state={after_regen_state!r}, latest_artifact={after_regen_art}")

    # No-delta path: fingerprint unchanged -> no new DRAFT minted -> approval is not applicable.
    if not getattr(regen_res, "created_new", False):
        print("\n=== Phase 3: approve (explicit) ===")
        print("Skipped: regeneration was a no-op (fingerprint unchanged), so no DRAFT exists to approve.")
        return 0

    # Optional fallback (only if allowed) to validate pipeline when no DRAFT exists
    if (not args.no_force_fallback) and (not force):
        with db_connect(db_path) as conn:
            has_draft = conn.execute(
                """
                SELECT 1
                FROM recap_artifacts
                WHERE league_id=? AND season=? AND week_index=? AND artifact_type='WEEKLY_RECAP' AND state='DRAFT'
                LIMIT 1
                """,
                (league_id, season, week_index),
            ).fetchone() is not None

        if not has_draft:
            print("\n(no DRAFT after regen; running force fallback to validate pipeline)")
            regen_res = regen_via_lifecycle(
                db_path=db_path,
                league_id=league_id,
                season=season,
                week_index=week_index,
                reason="LEDGER_SYNC",
                created_by=approved_by,
                force=True,
            )

    with db_connect(db_path) as conn:
        assert_no_approved_ledger_sync(conn, league_id, season, week_index, context="pre-approve")

    # Phase 3: approve (explicit)
    print("\n=== Phase 3: approve (explicit) ===")
    approve_via_lifecycle(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_index=week_index,
        approved_by=approved_by,
    )

    with db_connect(db_path) as conn:
        final_state = get_run_state(conn, league_id, season, week_index)
        final_art = get_latest_artifact(conn, league_id, season, week_index)
        assert_no_approved_ledger_sync(conn, league_id, season, week_index, context="final")

    print(f"\n=== Final ===\nrecap_runs.state={final_state!r}, latest_artifact={final_art}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Happens when piping to `head`/`grep` and the downstream closes early.
        raise SystemExit(0)

