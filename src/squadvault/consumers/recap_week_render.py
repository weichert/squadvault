#!/usr/bin/env python3

import argparse
import sqlite3
import sys
from typing import Any, Dict, Optional


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _fetch_latest_weekly_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


def _fetch_weekly_recap_artifact_by_version(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND version = ?
        LIMIT 1
        """,
        (league_id, season, week_index, version),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


def _fetch_approved_weekly_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND state = 'APPROVED'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


def _print_rendered_text_or_die(artifact: Dict[str, Any]) -> None:
    rendered = artifact.get("rendered_text")
    if not rendered:
        raise SystemExit("Artifact missing rendered_text; cannot render.")
    print(rendered)

def main() -> None:
    p = argparse.ArgumentParser(description="Render (view) a weekly recap artifact")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    p.add_argument(
        "--approved-only",
        action="store_true",
        help="Render ONLY an APPROVED recap artifact; error if none exists.",
    )
    p.add_argument(
        "--version",
        type=int,
        default=None,
        help="Render a specific recap artifact version (overrides latest).",
    )
    p.add_argument(
        "--suppress-render-warning",
        action="store_true",
        help="Suppress warning when rendering latest artifact without approval gate (internal use only).",
    )

    args = p.parse_args()

    # Priority order:
    # 1) explicit version
    # 2) approved-only
    # 3) latest (any state)

    if args.version is not None:
        artifact = _fetch_weekly_recap_artifact_by_version(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            version=args.version,
        )
        if artifact is None:
            raise SystemExit(f"No WEEKLY_RECAP artifact found for version={args.version}.")
        _print_rendered_text_or_die(artifact)
        return

    if args.approved_only:
        artifact = _fetch_approved_weekly_recap_artifact(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
        if artifact is None:
            raise SystemExit(
                "No APPROVED WEEKLY_RECAP artifact found for this week. "
                "Refusing to render drafts/ready artifacts."
            )
        _print_rendered_text_or_die(artifact)
        return

    # Default: render latest artifact (any state). Warn unless explicitly suppressed.
    artifact = _fetch_latest_weekly_recap_artifact(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
    )
    if artifact is None:
        raise SystemExit("No WEEKLY_RECAP artifacts found for this week.")

    if not args.suppress_render_warning:
        print(
            "WARNING: rendering latest artifact without approval gate. "
            "Use --approved-only for any UI/export path.",
            file=sys.stderr,
        )

    _print_rendered_text_or_die(artifact)
    return


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        # argparse uses SystemExit too; preserve normal behavior.
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
