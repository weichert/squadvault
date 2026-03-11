#!/usr/bin/env python3

import argparse
import sqlite3
import sys
from typing import List, Tuple
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

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


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except BrokenPipeError:
        raise SystemExit(0)

def _fetch_versions(
    cur: sqlite3.Cursor,
    league_id: str,
    season: int,
    week_index: int,
    artifact_type: str,
) -> List[sqlite3.Row]:
    cur.execute(
        """
        SELECT version, state, supersedes_version, approved_by, approved_at
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = ?
        ORDER BY version ASC
        """,
        (league_id, season, week_index, artifact_type),
    )
    return cur.fetchall()


def _fail(msg: str) -> None:
    print(f"INVARIANT FAILED: {msg}", file=sys.stderr)
    raise SystemExit(1)

def _ok(msg: str) -> None:
    _safe_print(f"OK: {msg}")

def main() -> None:
    p = argparse.ArgumentParser(description="Check recap approval invariants")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)
    p.add_argument("--artifact-type", default="WEEKLY_RECAP")

    # Optional strictness knobs
    p.add_argument(
        "--require-run-approved",
        action="store_true",
        help="Also require recap_runs.state == APPROVED for this week.",
    )
    p.add_argument(
        "--require-approved-is-latest",
        action="store_true",
        help="Require the APPROVED version is the highest version present.",
    )

    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = _fetch_versions(
        cur,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        artifact_type=args.artifact_type,
    )

    if not rows:
        _fail(
            f"No recap_artifacts found for league={args.league_id} "
            f"season={args.season} week={args.week_index} type={args.artifact_type}"
        )

    versions = [int(r["version"]) for r in rows]
    latest_version = max(versions)

    approved_rows = [r for r in rows if r["state"] == "APPROVED"]
    if len(approved_rows) != 1:
        _fail(
            f"Expected exactly 1 APPROVED artifact, found {len(approved_rows)} "
            f"(versions={versions})"
        )

    approved = approved_rows[0]
    approved_version = int(approved["version"])

    # Approval metadata must exist
    if not approved["approved_by"] or not approved["approved_at"]:
        _fail(
            f"APPROVED artifact missing approved_by/approved_at "
            f"(version={approved_version})"
        )

    # No other artifact may be APPROVED
    for r in rows:
        if int(r["version"]) != approved_version and r["state"] == "APPROVED":
            _fail(f"Multiple APPROVED artifacts detected (also version={r['version']})")

    # All prior versions must be SUPERSEDED
    for r in rows:
        v = int(r["version"])
        if v < approved_version and r["state"] != "SUPERSEDED":
            _fail(
                f"Version {v} is below approved_version={approved_version} "
                f"but state={r['state']} (expected SUPERSEDED)"
            )

    # Approved artifact should point back via supersedes_version (unless it's v1)
    if approved_version > 1:
        sv = approved["supersedes_version"]
        if sv is None:
            _fail(
                f"APPROVED version={approved_version} missing supersedes_version "
                f"(expected {approved_version - 1} or earlier)"
            )
        try:
            sv_int = int(sv)
        except Exception:
            _fail(f"APPROVED supersedes_version is not an int: {sv!r}")
        if sv_int >= approved_version:
            _fail(
                f"APPROVED supersedes_version={sv_int} must be < version={approved_version}"
            )

    # Optional: approved must be the latest version
    if args.require_approved_is_latest and approved_version != latest_version:
        _fail(
            f"APPROVED version={approved_version} is not latest_version={latest_version}"
        )

    # Optional: recap_runs must be APPROVED
    if args.require_run_approved:
        cur.execute(
            """
            SELECT state
            FROM recap_runs
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
            LIMIT 1
            """,
            (args.league_id, args.season, args.week_index),
        )
        rr = cur.fetchone()
        if rr is None:
            _fail("recap_runs row missing for this week")
        if rr["state"] != "APPROVED":
            _fail(f"recap_runs.state={rr['state']} (expected APPROVED)")

    conn.close()

    _ok(
        f"Approval invariants satisfied for league={args.league_id} "
        f"season={args.season} week={args.week_index} type={args.artifact_type} "
        f"(approved_version={approved_version}, latest_version={latest_version})"
    )


if __name__ == "__main__":
    main()
