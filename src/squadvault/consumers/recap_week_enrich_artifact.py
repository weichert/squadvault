#!/usr/bin/env python3
"""
Enrich a written weekly recap JSON artifact on disk, and update rendered_text for the
corresponding recap_artifacts row in SQLite.

Important behavior (safe / lifecycle-preserving):
- If recap_vXX_enriched.json already exists, we preserve it (do not clobber facts),
  but we may re-stamp metadata fields.
- selection_fingerprint/window_start/window_end are read from recap_runs (source of truth),
  because selection_fingerprint is NOT NULL in recap_artifacts schema.
- This script MUST NOT mutate lifecycle fields in recap_artifacts (state, approval, supersedence).
  It only updates rendered_text for an existing (league, season, week, version) row.

Operational guard:
- We refuse to update DB rendered_text for a non-latest DB version, to prevent historical
  versions (e.g., v1) from being accidentally rewritten when later versions exist.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ARTIFACT_TYPE = "WEEKLY_RECAP"
BASE_DIR_DEFAULT = "artifacts"


def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _get_db_latest_version(conn: sqlite3.Connection, league_id: str, season: int, week_index: int) -> int:
    row = conn.execute(
        """
        SELECT MAX(version) AS max_v
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
        """,
        (league_id, season, week_index, ARTIFACT_TYPE),
    ).fetchone()
    return int(row["max_v"]) if row and row["max_v"] is not None else 0


def fetch_run_trace(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
) -> Tuple[str, Optional[str], Optional[str]]:
    row = conn.execute(
        """
        SELECT selection_fingerprint, window_start, window_end
        FROM recap_runs
        WHERE league_id=? AND season=? AND week_index=?
        """,
        (league_id, season, week_index),
    ).fetchone()
    if row is None:
        raise RuntimeError("recap_runs row missing; run init/write workflow first.")
    return str(row["selection_fingerprint"]), row["window_start"], row["window_end"]


def find_latest_written_artifact_path(
    league_id: str,
    season: int,
    week_index: int,
    base_dir: str = BASE_DIR_DEFAULT,
) -> Tuple[Path, int]:
    week_dir = Path(base_dir) / "recaps" / str(league_id) / str(season) / f"week_{week_index:02d}"
    if not week_dir.exists():
        raise RuntimeError(f"Week directory not found: {week_dir}")

    pat = re.compile(r"^recap_v(\d{2})\.json$")
    candidates: List[Tuple[int, Path]] = []
    for p in week_dir.iterdir():
        m = pat.match(p.name)
        if m:
            candidates.append((int(m.group(1)), p))

    if not candidates:
        raise RuntimeError(f"No written recap_vXX.json found in {week_dir}")

    candidates.sort(key=lambda t: t[0])
    version, path = candidates[-1]
    return path, version


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def compute_facts_count(enriched: Dict[str, Any]) -> int:
    # best-effort; extend as needed
    if isinstance(enriched.get("facts"), list):
        return len(enriched["facts"])
    if isinstance(enriched.get("fact_rows"), list):
        return len(enriched["fact_rows"])
    if isinstance(enriched.get("items"), list):
        return len(enriched["items"])
    if isinstance(enriched.get("facts_json"), list):
        return len(enriched["facts_json"])
    return int(enriched.get("facts_count", 0) or 0)


def build_rendered_text_minimal(
    *,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    window_start: Optional[str],
    window_end: Optional[str],
    selection_fingerprint: str,
    facts_count: int,
) -> str:
    lines: List[str] = []
    lines.append(f"SquadVault Weekly Recap — League {league_id} — Season {season} — Week {week_index} (v{version})")
    lines.append("")
    if window_start and window_end:
        lines.append(f"Window: {window_start} → {window_end}")
    else:
        lines.append("Window: (unknown)")
    lines.append(f"Selection fingerprint: {selection_fingerprint}")
    lines.append("")
    lines.append(f"Facts: {facts_count}")
    lines.append("")
    lines.append("Note: This recap is summary-only and intentionally avoids fabricating details not present in event payloads.")
    return "\n".join(lines)


def update_rendered_text_only(
    conn: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    rendered_text: str,
) -> None:
    """
    Enrichment is NOT allowed to mutate lifecycle fields (state, approval, supersedence, traceability).
    It may ONLY update rendered_text for an existing recap_artifacts row.
    """
    cur = conn.execute(
        """
        UPDATE recap_artifacts
        SET rendered_text = ?
        WHERE league_id=?
          AND season=?
          AND week_index=?
          AND artifact_type=?
          AND version=?
        """,
        (rendered_text, league_id, season, week_index, ARTIFACT_TYPE, version),
    )
    conn.commit()

    if cur.rowcount == 0:
        raise SystemExit(
            "No recap_artifacts row found to update rendered_text. "
            "Run recap_week_init + recap_week_write_artifact first (or ensure the DB row exists)."
        )


def _restamp_metadata_in_enriched_json(
    enriched: Dict[str, Any],
    *,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    selection_fingerprint: str,
    window_start: Optional[str],
    window_end: Optional[str],
) -> Dict[str, Any]:
    """
    Best-effort metadata stamping. We keep this intentionally conservative:
    - Preserve existing facts/rows/etc.
    - Add/update a small 'meta' object and a few top-level convenience fields.
    """
    meta = enriched.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    meta.update(
        {
            "league_id": str(league_id),
            "season": int(season),
            "week_index": int(week_index),
            "version": int(version),
            "selection_fingerprint": str(selection_fingerprint),
            "window_start": window_start,
            "window_end": window_end,
            "enriched_at": _utc_now_iso(),
        }
    )
    enriched["meta"] = meta

    # Also stamp common top-level fields if present/expected by other consumers (safe additions).
    enriched["league_id"] = str(league_id)
    enriched["season"] = int(season)
    enriched["week_index"] = int(week_index)
    enriched["version"] = int(version)
    enriched["selection_fingerprint"] = str(selection_fingerprint)
    enriched["window_start"] = window_start
    enriched["window_end"] = window_end

    return enriched


def main() -> None:
    p = argparse.ArgumentParser(description="Enrich weekly recap artifact and update rendered_text in recap_artifacts")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)
    p.add_argument("--base-dir", default=BASE_DIR_DEFAULT, help="Artifact base dir (default: artifacts)")
    args = p.parse_args()

    league_id = str(args.league_id)
    season = int(args.season)
    week_index = int(args.week_index)
    base_dir = str(args.base_dir)

    conn = db_connect(args.db)

    written_path, version = find_latest_written_artifact_path(
        league_id=league_id,
        season=season,
        week_index=week_index,
        base_dir=base_dir,
    )
    enriched_path = written_path.with_name(f"recap_v{version:02d}_enriched.json")

    # Preserve existing enriched file if it exists (do NOT clobber facts)
    if enriched_path.exists():
        enriched: Dict[str, Any] = load_json(enriched_path)
    else:
        enriched = load_json(written_path)

    selection_fingerprint, window_start, window_end = fetch_run_trace(conn, league_id, season, week_index)

    # Re-stamp metadata (but keep facts intact)
    enriched = _restamp_metadata_in_enriched_json(
        enriched,
        league_id=league_id,
        season=season,
        week_index=week_index,
        version=version,
        selection_fingerprint=selection_fingerprint,
        window_start=window_start,
        window_end=window_end,
    )

    # Write enriched JSON (always)
    write_json(enriched_path, enriched)

    facts_count = compute_facts_count(enriched)
    print(f"enriched_written: {enriched_path}")
    print(f"facts_count: {facts_count}")

    # Build rendered text (this is what render/view paths show)
    rendered_text = build_rendered_text_minimal(
        league_id=league_id,
        season=season,
        week_index=week_index,
        version=version,
        window_start=window_start,
        window_end=window_end,
        selection_fingerprint=selection_fingerprint,
        facts_count=facts_count,
    )

    # Guard: never rewrite historical DB versions.
    db_latest = _get_db_latest_version(conn, league_id, season, week_index)
    if db_latest == 0:
        print(
            "WARNING: no recap_artifacts rows exist for this week yet; "
            "wrote enriched file only (run recap_week_init + recap_week_write_artifact first).",
            file=sys.stderr,
        )
        return

    if db_latest and version != db_latest:
        print(
            f"WARNING: refusing to update DB rendered_text for non-latest version "
            f"(week={week_index} version={version} latest={db_latest}); wrote enriched file only.",
            file=sys.stderr,
        )
        return

    # Update rendered_text only (no upsert of lifecycle fields).
    update_rendered_text_only(
        conn,
        league_id=league_id,
        season=season,
        week_index=week_index,
        version=version,
        rendered_text=rendered_text,
    )
    print(f"db_updated: recap_artifacts week={week_index} version={version} rendered_text_len={len(rendered_text)}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
