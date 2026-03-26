"""Render and display weekly recap artifacts."""

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, Optional

from squadvault.core.storage.session import DatabaseSession
from squadvault.errors import RecapDataError
from squadvault.core.storage.db_utils import row_to_dict as _row_to_dict




def _fetch_latest_weekly_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    """Fetch latest WEEKLY_RECAP artifact row for a week."""
    with DatabaseSession(db_path) as conn:
        row = conn.execute(
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
        ).fetchone()
    return None if row is None else _row_to_dict(row)


def _fetch_weekly_recap_artifact_by_version(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
) -> Optional[Dict[str, Any]]:
    """Fetch a specific WEEKLY_RECAP artifact version."""
    with DatabaseSession(db_path) as conn:
        row = conn.execute(
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
        ).fetchone()
    return None if row is None else _row_to_dict(row)


def _fetch_approved_weekly_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    """Fetch latest approved WEEKLY_RECAP artifact for a week."""
    with DatabaseSession(db_path) as conn:
        row = conn.execute(
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
        ).fetchone()
    return None if row is None else _row_to_dict(row)



def _print_rendered_text_or_die(artifact: Dict[str, Any]) -> None:
    """Print artifact rendered_text, or raise error if missing."""
    rendered = artifact.get("rendered_text")
    if not rendered:
        raise RecapDataError("Artifact missing rendered_text; cannot render.")
    print(rendered)


def main() -> None:
    """CLI entrypoint: render and display weekly recap artifacts."""
    p = argparse.ArgumentParser(description="Render (view) a weekly recap artifact")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    p.add_argument(
        "--base-dir",
        default="artifacts",
        help="Artifact base dir (default: artifacts). Used for voice variant rendering.",
    )
    p.add_argument(
        "--voice",
        action="append",
        default=None,
        help="Render using a declared voice. Repeatable. Default: neutral.",
    )

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

    if args.voice is not None:
        raise SystemExit(
            "Voice variant rendering (--voice) has been retired. "
            "Use rendered_text from recap_artifacts instead."
        )

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
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
