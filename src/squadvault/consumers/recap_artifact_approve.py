import argparse

from squadvault.core.recaps.recap_runs import sync_recap_run_state_from_artifacts
from squadvault.core.recaps.recap_artifacts import (
    approve_recap_artifact,
    latest_approved_version,
    supersede_approved_recap_artifact,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--approved-by", required=True)

    args = ap.parse_args()

    prev = latest_approved_version(args.db, args.league_id, args.season, args.week_index)

    # Approve requested version (must be DRAFT)
    approve_recap_artifact(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        version=args.version,
        approved_by=args.approved_by,
    )

    # Only after new version is approved, supersede the previous approved one (if any)
    if prev is not None and prev != args.version:
        supersede_approved_recap_artifact(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            version=prev,
        )

    # Explicit sync of recap_runs from artifact truth
    synced = sync_recap_run_state_from_artifacts(args.db, args.league_id, args.season, args.week_index)

    print(
        f"recap_approve: OK (approved v{args.version}; previous_approved={prev}; ledger={synced})"
    )


if __name__ == "__main__":
    main()
