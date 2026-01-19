from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class ApprovedRecapArtifact:
    league_id: str
    season: int
    week_index: int
    version: int

    artifact_type: str
    state: str

    selection_fingerprint: Optional[str]
    window_start: Optional[str]
    window_end: Optional[str]

    approved_by: Optional[str]
    approved_at: Optional[str]

    rendered_text: str
    payload_json: dict[str, Any]


@dataclass(frozen=True)
class ExportManifest:
    out_dir: str
    recap_md: str
    recap_json: str
    metadata_json: str


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}  # row[1] = column name


def _pick_rendered_text(row: sqlite3.Row, cols: set[str]) -> str:
    """
    Be tolerant to evolving schema: prefer the first available "rendered text" column.
    """
    candidates = [
        "rendered_text",
        "rendered_markdown",
        "rendered_md",
        "body",
        "text",
        "content",
        "rendered",
    ]
    for c in candidates:
        if c in cols:
            v = row[c]
            if v:
                return str(v)
    # If present but empty, return empty string (still export metadata/json)
    for c in candidates:
        if c in cols:
            v = row[c]
            return "" if v is None else str(v)
    return ""


def _payload_from_row(row: sqlite3.Row, cols: set[str], rendered_text: str) -> dict[str, Any]:
    """
    Some schemas store full payload JSON; many don't.
    If we have a JSON-ish column, parse it; otherwise synthesize a minimal payload
    using the best available fields.
    """
    json_candidates = ["payload_json", "payload", "artifact_json", "artifact_payload"]
    for c in json_candidates:
        if c in cols and row[c]:
            raw = row[c]
            try:
                return json.loads(raw)
            except Exception:
                return {"_raw_payload": raw, "_raw_payload_column": c}

    # Synthesize minimal payload from known fields
    out: dict[str, Any] = {}
    for c in [
        "league_id",
        "season",
        "week_index",
        "version",
        "artifact_type",
        "state",
        "selection_fingerprint",
        "window_start",
        "window_end",
        "approved_by",
        "approved_at",
        "created_by",
        "created_at",
        "supersedes_version",
        "withheld_reason",
    ]:
        if c in cols:
            out[c] = row[c]
    out["rendered_text"] = rendered_text
    return out


def fetch_latest_approved_weekly_recap(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    *,
    version: int | None = None,
) -> ApprovedRecapArtifact:
    """
    Fetch latest APPROVED WEEKLY_RECAP artifact (or a specific approved version).
    Export-only: does not render/regenerate.

    Schema-resilient: selects only columns that exist.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cols = _table_columns(conn, "recap_artifacts")

        # Required-ish fields (if missing, we still try but may raise clearer errors)
        needed_for_identity = ["league_id", "season", "week_index", "version", "artifact_type", "state"]
        present_identity = [c for c in needed_for_identity if c in cols]

        # Optional fields we’d like to export if present
        optional_fields = [
            "selection_fingerprint",
            "window_start",
            "window_end",
            "approved_by",
            "approved_at",
            "created_by",
            "created_at",
            "supersedes_version",
            "withheld_reason",
            # text/payload columns are handled separately (we’ll include if present)
            "rendered_text",
            "rendered_markdown",
            "rendered_md",
            "body",
            "text",
            "content",
            "rendered",
            "payload_json",
            "payload",
            "artifact_json",
            "artifact_payload",
        ]
        present_optional = [c for c in optional_fields if c in cols]

        select_cols = []
        for c in present_identity + present_optional:
            if c not in select_cols:
                select_cols.append(c)

        if not select_cols:
            raise RuntimeError("recap_artifacts table has no readable columns (?)")

        sql = f"""
        SELECT
            {", ".join(select_cols)}
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND state = 'APPROVED'
        """
        params: list[Any] = [league_id, season, week_index]

        if version is not None:
            sql += " AND version = ?"
            params.append(version)

        sql += " ORDER BY version DESC LIMIT 1"

        row = conn.execute(sql, params).fetchone()
        if not row:
            which = f"version={version}" if version is not None else "latest"
            raise RuntimeError(
                f"No APPROVED WEEKLY_RECAP found for league_id={league_id} season={season} week_index={week_index} ({which})."
            )

        rendered_text = _pick_rendered_text(row, cols)
        payload_json = _payload_from_row(row, cols, rendered_text)

        # Pull fields (tolerant if columns missing)
        def g(name: str) -> Any:
            return row[name] if name in cols else None

        artifact = ApprovedRecapArtifact(
            league_id=str(g("league_id") or league_id),
            season=int(g("season") if g("season") is not None else season),
            week_index=int(g("week_index") if g("week_index") is not None else week_index),
            version=int(g("version")) if g("version") is not None else 0,
            artifact_type=str(g("artifact_type") or "WEEKLY_RECAP"),
            state=str(g("state") or ""),
            selection_fingerprint=g("selection_fingerprint"),
            window_start=g("window_start"),
            window_end=g("window_end"),
            approved_by=g("approved_by"),
            approved_at=g("approved_at"),
            rendered_text=rendered_text,
            payload_json=payload_json,
        )

        if artifact.state != "APPROVED":
            raise RuntimeError(f"Refusing to export non-approved artifact: state={artifact.state}")

        return artifact
    finally:
        conn.close()


def write_approved_weekly_recap_export_bundle(
    artifact: ApprovedRecapArtifact,
    out_dir: str | Path,
    *,
    deterministic: bool = True,
) -> ExportManifest:
    """
    Writes:
      - recap.md (rendered_text; may be empty if schema has no rendered column)
      - recap.json (payload_json; always present as dict)
      - metadata.json (approval + window + fingerprint + file manifest)
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    recap_md_path = out_path / "recap.md"
    recap_json_path = out_path / "recap.json"
    metadata_json_path = out_path / "metadata.json"

    recap_md_path.write_text((artifact.rendered_text or "").rstrip() + "\n", encoding="utf-8")

    recap_json_path.write_text(
        json.dumps(artifact.payload_json, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    meta: dict[str, Any] = {
        "league_id": artifact.league_id,
        "season": artifact.season,
        "week_index": artifact.week_index,
        "version": artifact.version,
        "artifact_type": artifact.artifact_type,
        "state": artifact.state,
        "selection_fingerprint": artifact.selection_fingerprint,
        "window_start": artifact.window_start,
        "window_end": artifact.window_end,
        "approved_by": artifact.approved_by,
        "approved_at": artifact.approved_at,
        "export_format": "bundle_v1",
        "files": {
            "recap_md": recap_md_path.name,
            "recap_json": recap_json_path.name,
            "metadata_json": metadata_json_path.name,
        },
    }

    if not deterministic:
        meta["exported_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
        meta["export_host"] = os.uname().nodename if hasattr(os, "uname") else None

    metadata_json_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return ExportManifest(
        out_dir=str(out_path),
        recap_md=str(recap_md_path),
        recap_json=str(recap_json_path),
        metadata_json=str(metadata_json_path),
    )
