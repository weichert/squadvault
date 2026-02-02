from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from squadvault.core.exports.approved_rivalry_chronicle_export_v1 import (
    ApprovedRivalryChronicleArtifactV1,
    fetch_latest_approved_rivalry_chronicle_v1,
)

# No canonical markers should ever appear in Chronicle export outputs.
CANONICAL_MARKER_PREFIX = "<!-- BEGIN_CANONICAL_"


@dataclass(frozen=True)
class RivalryChronicleExportResultV1:
    out_dir: str
    chronicle_md: str
    chronicle_json: str


def _default_out_dir(repo_root: Path, league_id: int, season: int, anchor_week_index: int) -> Path:
    # Deterministic and reproducible; matches existing exports convention.
    return (
        repo_root
        / "artifacts"
        / "exports"
        / str(int(league_id))
        / str(int(season))
        / f"week_{int(anchor_week_index):02d}"
        / "chronicle_export_v1"
    )


def _repo_root_from_here() -> Path:
    # CWD-independent: derive repo root by walking upward until we find repo markers.
    # Prefer pyproject.toml, else .git, else a directory containing "src".
    here = Path(__file__).resolve()
    for d in [here.parent, *here.parents]:
        if (d / "pyproject.toml").exists():
            return d
        if (d / ".git").exists():
            return d
        if (d / "src").exists() and (d / "src" / "squadvault").exists():
            return d
    # Fall back: assume standard layout .../<repo>/src/...
    # (This is conservative and keeps behavior deterministic.)
    return here.parents[4]


def _write_text_exact(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def _write_json_deterministic(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    # Deterministic: sorted keys, stable indent, newline.
    payload = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    p.write_text(payload, encoding="utf-8")


def export_latest_approved_rivalry_chronicle_v1(
    *,
    db_path: str,
    out_dir: Optional[str] = None,
) -> RivalryChronicleExportResultV1:
    """
    Chronicle Export v1 (projection-only):

    - Reads latest APPROVED RIVALRY_CHRONICLE_V1 via mode=ro connection
    - Writes chronicle.md and chronicle.json
    - No DB writes, no inference, no mutation of stored content
    """
    debug = os.environ.get("SV_DEBUG") == "1"

    artifact: ApprovedRivalryChronicleArtifactV1 = fetch_latest_approved_rivalry_chronicle_v1(db_path)


    # Guard: never export an empty approved chronicle.
    if not (artifact.rendered_text or '').strip():
        raise SystemExit('ERROR: Approved chronicle rendered_text is empty; refusing export.')
    repo_root = _repo_root_from_here()
    outp = Path(out_dir).resolve() if out_dir else _default_out_dir(repo_root, artifact.league_id, artifact.season, artifact.anchor_week_index)

    md_path = outp / "chronicle.md"
    json_path = outp / "chronicle.json"

    # 1) Write chronicle.md verbatim (rendered_text already includes NON-CANONICAL header).
    rendered = artifact.rendered_text if artifact.rendered_text is not None else ""
    _write_text_exact(md_path, rendered)

    # 2) Write chronicle.json (no derived data).
    meta: Dict[str, Any] = {
        "league_id": int(artifact.league_id),
        "season": int(artifact.season),
        "anchor_week_index": int(artifact.anchor_week_index),
        "artifact_type": str(artifact.artifact_type),
        "version": int(artifact.version),
        "selection_fingerprint": str(artifact.selection_fingerprint),
        "provenance": dict(artifact.provenance or {}),
    }
    _write_json_deterministic(json_path, meta)

    if debug:
        # Debug-only sanity: ensure we didn't introduce canonical markers in the MD.
        txt = md_path.read_text(encoding="utf-8")
        has_marker = CANONICAL_MARKER_PREFIX in txt
        print(f"SV_DEBUG=1: export out_dir={outp}", file=os.sys.stderr)
        print(f"SV_DEBUG=1: wrote md={md_path} json={json_path}", file=os.sys.stderr)
        print(f"SV_DEBUG=1: md_has_canonical_marker={has_marker}", file=os.sys.stderr)

    return RivalryChronicleExportResultV1(
        out_dir=str(outp),
        chronicle_md=str(md_path),
        chronicle_json=str(json_path),
    )
