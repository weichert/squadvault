#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from squadvault.core.recaps.render.render_recap_text_v1 import render_recap_text_v1
from squadvault.core.recaps.render.voice_variants_v1 import format_variant_block


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


def _recap_dir(base_dir: str, league_id: str, season: int, week_index: int) -> Path:
    return Path(base_dir) / "recaps" / str(league_id) / str(season) / f"week_{int(week_index):02d}"


def _load_payload_from_recaps_table_or_disk(
    *,
    db_path: str,
    base_dir: str,
    league_id: str,
    season: int,
    week_index: int,
    selection_fingerprint: str,
) -> Dict[str, Any]:
    """
    Truth source for rendering variants:
      - Prefer recaps.artifact_json (canonical recap JSON)
      - Fallback to recaps.artifact_path
      - (last resort) look for recap_v01.json on disk for the week (should usually exist for ACTIVE recap_version)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT recap_version, artifact_path, artifact_json
            FROM recaps
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND selection_fingerprint = ?
            ORDER BY recap_version DESC
            LIMIT 1
            """,
            (league_id, int(season), int(week_index), selection_fingerprint),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if row is not None:
        # 1) artifact_json (preferred)
        raw = row["artifact_json"]
        if isinstance(raw, str) and raw.strip():
            return json.loads(raw)

        # 2) artifact_path (fallback)
        apath = row["artifact_path"]
        if isinstance(apath, str) and apath.strip():
            p = Path(apath)
            # allow relative paths stored in db
            if not p.is_absolute():
                p = Path(".") / p
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))

    # 3) last resort disk heuristic: recap_v01.json in week dir
    week_dir = _recap_dir(base_dir, league_id, season, week_index)
    candidate = week_dir / "recap_v01.json"
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    raise SystemExit(
        "Unable to locate recap JSON for rendering.\n"
        f"Expected recaps.artifact_json or recaps.artifact_path for fingerprint={selection_fingerprint}, "
        f"or a disk file like {candidate}."
    )


def _render_variants(payload: Dict[str, Any], voices: list[str]) -> None:
    multi = len(voices) > 1
    for v in voices:
        body = render_recap_text_v1(payload, voice_id=v)
        if multi:
            print(format_variant_block(voice_id=v, body=body))
        else:
            print(body)


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
    voices = args.voice or ["neutral"]
    want_variants = args.voice is not None  # only switch to recap-json rendering when explicitly requested

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

        if want_variants:
            fp = artifact.get("selection_fingerprint")
            if not fp:
                raise SystemExit("Artifact missing selection_fingerprint; cannot locate recap JSON for variants.")
            payload = _load_payload_from_recaps_table_or_disk(
                db_path=args.db,
                base_dir=args.base_dir,
                league_id=args.league_id,
                season=args.season,
                week_index=args.week_index,
                selection_fingerprint=str(fp),
            )
            _render_variants(payload, voices)
            return

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

        if want_variants:
            fp = artifact.get("selection_fingerprint")
            if not fp:
                raise SystemExit("Artifact missing selection_fingerprint; cannot locate recap JSON for variants.")
            payload = _load_payload_from_recaps_table_or_disk(
                db_path=args.db,
                base_dir=args.base_dir,
                league_id=args.league_id,
                season=args.season,
                week_index=args.week_index,
                selection_fingerprint=str(fp),
            )
            _render_variants(payload, voices)
            return

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

    if want_variants:
        fp = artifact.get("selection_fingerprint")
        if not fp:
            raise SystemExit("Artifact missing selection_fingerprint; cannot locate recap JSON for variants.")
        payload = _load_payload_from_recaps_table_or_disk(
            db_path=args.db,
            base_dir=args.base_dir,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            selection_fingerprint=str(fp),
        )
        _render_variants(payload, voices)
        return

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
