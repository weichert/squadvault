import argparse
import sqlite3
from typing import Optional, Tuple


def _get_recap_run_row(
    db_path: str, league_id: str, season: int, week_index: int
) -> Optional[Tuple[str, Optional[str], str, str, Optional[str]]]:
    """
    Returns: (state, reason, selection_fingerprint, created_at, updated_at)
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT state, reason, selection_fingerprint, created_at, updated_at
            FROM recap_runs
            WHERE league_id=? AND season=? AND week_index=?
            """,
            (league_id, season, week_index),
        ).fetchone()
        return tuple(row) if row else None
    finally:
        con.close()


def _get_latest_recap_row(
    db_path: str, league_id: str, season: int, week_index: int
) -> Optional[Tuple[int, str, str]]:
    """
    Returns: (recap_version, selection_fingerprint, status)
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT recap_version, selection_fingerprint, status
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=?
            ORDER BY recap_version DESC
            LIMIT 1;
            """,
            (league_id, season, week_index),
        ).fetchone()
        if not row:
            return None
        return (int(row[0]), str(row[1]), str(row[2]))
    finally:
        con.close()


def _get_active_artifact_path(db_path: str, league_id: str, season: int, week_index: int) -> Optional[str]:
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
        return None
    return str(row[0])

def _suggest_next_action(
    state: Optional[str],
    has_active_artifact: bool,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> str:
    common = (
        f"./scripts/py -u "
        f"--db {db_path} --league-id {league_id} --season {season} --week-index {week_index}"
    )

    if state is None:
        return (
            "NEXT: init\n"
            f"  ./scripts/py -u src/squadvault/consumers/recap_week_init.py "
            f"--db {db_path} --league-id {league_id} --season {season} --week-index {week_index}"
        )

    if state == "WITHHELD":
        return "NEXT: none (WITHHELD)"

    if state == "DRAFTED":
        return (
            "NEXT: write artifact (creates artifact -> REVIEW_REQUIRED)\n"
            f"  ./scripts/py -u src/squadvault/consumers/recap_week_write_artifact.py "
            f"--db {db_path} --base-dir artifacts --league-id {league_id} --season {season} --week-index {week_index}"
        )

    if state == "REVIEW_REQUIRED":
        if has_active_artifact:
            return (
                "NEXT: human review (view recap)\n"
                f"  ./scripts/py -u src/squadvault/consumers/recap_week_render.py "
                f"--db {db_path} --league-id {league_id} --season {season} --week-index {week_index}\n"
                "\n"
                "NEXT (manual approval):\n"
                f"  ./scripts/py -u src/squadvault/consumers/recap_week_approve.py "
                f"--db {db_path} --league-id {league_id} --season {season} --week-index {week_index}"

            )
        return (
            "NEXT: write artifact (artifact missing)\n"
            f"  ./scripts/py -u src/squadvault/consumers/recap_week_write_artifact.py "
            f"--db {db_path} --base-dir artifacts --league-id {league_id} --season {season} --week-index {week_index}"
        )

    if state == "APPROVED":
        return "NEXT: none (APPROVED)"

    return f"NEXT: unknown state '{state}' (no automatic action)"

def main() -> None:
    ap = argparse.ArgumentParser(description="Show weekly recap pipeline status (single pane of glass).")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    args = ap.parse_args()

    run_row = _get_recap_run_row(args.db, args.league_id, args.season, args.week_index)
    latest = _get_latest_recap_row(args.db, args.league_id, args.season, args.week_index)
    artifact_path = _get_active_artifact_path(args.db, args.league_id, args.season, args.week_index)

    print("=== SquadVault Recap Week Status ===")
    print(f"DB     : {args.db}")
    print(f"League : {args.league_id}")
    print(f"Season : {args.season}")
    print(f"Week   : {args.week_index}")

    state: Optional[str] = None

    print("\nrecap_runs:")
    if run_row is None:
        print("  (none)")
    else:
        state, reason, fp, created_at, updated_at = run_row
        print(f"  state      : {state}")
        print(f"  reason     : {reason or ''}")
        print(f"  fingerprint: {fp}")
        print(f"  created_at : {created_at}")
        print(f"  updated_at : {updated_at or ''}")

    print("\nrecaps (latest):")
    if latest is None:
        print("  (none)")
    else:
        v, fp, status = latest
        print(f"  version    : {v}")
        print(f"  status     : {status}")
        print(f"  fingerprint: {fp}")

    print("\nartifact:")
    print(f"  active_path: {artifact_path or '(none)'}")

    print(
        "\n"
        + _suggest_next_action(
            state,
            has_active_artifact=bool(artifact_path),
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
)

if __name__ == "__main__":
    main()