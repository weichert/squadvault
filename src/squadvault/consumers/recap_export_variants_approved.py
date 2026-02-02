#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _fetch_approved_weekly_recap_artifact(
    *,
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
        (league_id, int(season), int(week_index)),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


@dataclass(frozen=True)
class ExportMetadata:
    export_kind: str
    league_id: str
    season: int
    week_index: int
    lifecycle_version: int
    lifecycle_state: str
    selection_fingerprint: str
    voices: List[str]
    generated_at: str
    output_path: str


def _export_dir(base_dir: str, league_id: str, season: int, week_index: int) -> Path:
    return Path(base_dir) / "exports" / str(league_id) / str(season) / f"week_{int(week_index):02d}"


def _run_renderer(
    *,
    db: str,
    league_id: str,
    season: int,
    week_index: int,
    voices: List[str],
    base_dir: str,
) -> str:
    """
    Use the existing renderer to produce the variant blocks.
    We keep this strictly downstream and do not mutate any core engine state.
    """
    py = "src/squadvault/consumers/recap_week_render.py"
    cmd = [
        sys.executable, "-u", py,
        "--db", db,
        "--league-id", league_id,
        "--season", str(season),
        "--week-index", str(week_index),
        "--approved-only",
        "--suppress-render-warning",
        "--base-dir", base_dir,
    ]
    for v in voices:
        cmd += ["--voice", v]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        raise RuntimeError(f"recap_week_render failed (rc={proc.returncode}). stderr:\n{err}")
    if not out:
        raise RuntimeError("recap_week_render produced no stdout output.")
    return out


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Export APPROVED weekly recap voice variants as a shareable pack")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--base-dir", default="artifacts", help="Artifact base dir (default: artifacts)")
    ap.add_argument("--export-dir", default="artifacts", help="Exports base dir root (default: artifacts)")
    ap.add_argument("--voice", action="append", default=[], help="Repeatable. Default: neutral, playful, dry")
    args = ap.parse_args(argv)

    voices = args.voice or ["neutral", "playful", "dry"]

    approved = _fetch_approved_weekly_recap_artifact(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
    )
    if approved is None:
        print("ERROR: No APPROVED WEEKLY_RECAP artifact found for this week. Refusing export.", file=sys.stderr)
        return 2

    lifecycle_version = _safe_int(approved.get("version"), 0)
    lifecycle_state = str(approved.get("state") or "")
    selection_fp = str(approved.get("selection_fingerprint") or "")

    rendered_pack = _run_renderer(
        db=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        voices=voices,
        base_dir=args.base_dir,
    )

    out_dir = _export_dir(args.export_dir, args.league_id, args.season, args.week_index)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"variants_pack_v{lifecycle_version:02d}.md"
    meta_path = out_dir / f"variants_pack_v{lifecycle_version:02d}.metadata.json"

    header = [
        f"# SquadVault Voice Variant Pack (Approved)",
        "",
        f"- League: {args.league_id}",
        f"- Season: {args.season}",
        f"- Week: {args.week_index}",
        f"- Lifecycle version: v{lifecycle_version:02d} ({lifecycle_state})",
        f"- Selection fingerprint: {selection_fp}",
        f"- Voices: {', '.join(voices)}",
        f"- Generated at: {utc_now_iso()}",
        "",
        "---",
        "",
    ]
    md_body = "\n".join(header) + rendered_pack.strip() + "\n"

    md_path.write_text(md_body, encoding="utf-8")

    meta = ExportMetadata(
        export_kind="APPROVED_WEEKLY_RECAP_VOICE_VARIANTS_V1",
        league_id=str(args.league_id),
        season=int(args.season),
        week_index=int(args.week_index),
        lifecycle_version=int(lifecycle_version),
        lifecycle_state=str(lifecycle_state),
        selection_fingerprint=str(selection_fp),
        voices=list(voices),
        generated_at=utc_now_iso(),
        output_path=str(md_path),
    )
    meta_path.write_text(json.dumps(asdict(meta), indent=2), encoding="utf-8")

    print(str(md_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
