from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gen_creative_sharepack_v1.py")

GEN_TEXT = r"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_FILES = [
    "README.md",
    "memes_caption_set_v1.md",
    "commentary_short_v1.md",
    "stats_fun_facts_v1.md",
    "manifest_v1.json",
]


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read_text(p: Path) -> str:
    # Read as text; normalize line endings to LF.
    s = p.read_text(encoding="utf-8", errors="strict")
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _write_text(p: Path, s: str) -> None:
    # Enforce LF line endings and trailing newline.
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    if not s.endswith("\n"):
        s += "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


def _int_env(*names: str) -> int | None:
    for n in names:
        v = os.environ.get(n)
        if v is None or v == "":
            continue
        try:
            return int(v)
        except ValueError:
            raise SystemExit(f"ERROR: env {n} must be int, got: {v!r}")
    return None


def _str_env(*names: str) -> str | None:
    for n in names:
        v = os.environ.get(n)
        if v is None or v == "":
            continue
        return v
    return None


def _week_dirname(week_index: int) -> str:
    if week_index < 0 or week_index > 99:
        raise SystemExit(f"ERROR: week_index out of range 0..99: {week_index}")
    return f"week_{week_index:02d}"


def _discover_approved_sources(exports_root: Path) -> list[Path]:
    # Prefer explicit “approved” markdown exports. Keep deterministic ordering.
    # Accept either "__approved_" or "_approved_" naming (repo history varies).
    patterns = [
        "**/*__approved_*.md",
        "**/*_approved_*.md",
    ]
    found: list[Path] = []
    for pat in patterns:
        for p in exports_root.glob(pat):
            if p.is_file():
                found.append(p)
    # De-dup, stable sort by POSIX path.
    uniq = sorted({p.resolve(): p for p in found}.values(), key=lambda x: x.as_posix())
    return uniq


def _stable_unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in items:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _extract_caption_lines(text: str, limit: int = 25) -> list[str]:
    # Captions are text-only; we must not invent. Extract candidate lines from source content.
    # Deterministic heuristic:
    # - Prefer markdown list items ("- " or "* ") and numbered lists ("1. ")
    # - Fallback: short non-empty lines
    lines = text.split("\n")
    candidates: list[str] = []

    for ln in lines:
        t = ln.strip()
        if not t:
            continue
        if t.startswith("- ") or t.startswith("* "):
            candidates.append(t[2:].strip())
        elif len(t) >= 3 and t[0].isdigit() and t[1] == "." and t[2] == " ":
            candidates.append(t[3:].strip())

    if len(candidates) < limit:
        for ln in lines:
            t = ln.strip()
            if not t:
                continue
            # Avoid headings as captions; prefer regular lines.
            if t.startswith("#"):
                continue
            if len(t) > 140:
                continue
            candidates.append(t)

    candidates = [c for c in candidates if c]
    candidates = _stable_unique(candidates)
    return candidates[:limit]


def _extract_commentary_excerpt(text: str, max_lines: int = 20) -> str:
    lines = [ln.rstrip() for ln in text.split("\n")]
    # keep non-empty lines but preserve spacing deterministically
    kept: list[str] = []
    for ln in lines:
        if ln.strip() == "":
            continue
        kept.append(ln)
        if len(kept) >= max_lines:
            break
    return "\n".join(kept).strip()


def _extract_fun_facts(text: str, limit: int = 25) -> list[str]:
    lines = [ln.strip() for ln in text.split("\n")]
    candidates: list[str] = []
    for ln in lines:
        if not ln:
            continue
        # Prefer lines with digits (stats-ish), but avoid pure code fences.
        if any(ch.isdigit() for ch in ln):
            if ln.startswith("```") or ln.endswith("```"):
                continue
            if len(ln) > 220:
                continue
            candidates.append(ln)

    candidates = _stable_unique(candidates)
    return candidates[:limit]


@dataclass(frozen=True)
class Inputs:
    league_id: str
    season: int
    week_index: int


def _parse_args() -> Inputs:
    p = argparse.ArgumentParser(description="Generate Creative Sharepack (v1) from verified approved exports.")
    p.add_argument("--league-id", dest="league_id", default=None, help="League identifier (defaults from env if set).")
    p.add_argument("--season", dest="season", type=int, default=None, help="Season (int; defaults from env if set).")
    p.add_argument("--week-index", dest="week_index", type=int, default=None, help="Week index (intn: int; defaults from env if set).")

    args = p.parse_args()

    league_id = args.league_id or _str_env("SV_LEAGUE_ID", "LEAGUE_ID", "SQUADVAULT_LEAGUE_ID")
    season = args.season if args.season is not None else _int_env("SV_SEASON", "SEASON", "SQUADVAULT_SEASON")
    week_index = args.week_index if args.week_index is not None else _int_env("SV_WEEK_INDEX", "WEEK_INDEX", "SQUADVAULT_WEEK_INDEX")

    missing = []
    if not league_id:
        missing.append("league_id (--league-id or env SV_LEAGUE_ID/LEAGUE_ID)")
    if season is None:
        missing.append("season (--season or env SV_SEASON/SEASON)")
    if week_index is None:
        missing.append("week_index (--week-index or env SV_WEEK_INDEX/WEEK_INDEX)")
    if missing:
        raise SystemExit("ERROR: missing required inputs: " + ", ".join(missing))

    league_id = str(league_id).strip()
    if not league_id:
        raise SystemExit("ERROR: league_id must be non-empty")

    return Inputs(league_id=league_id, season=int(season), week_index=int(week_index))


def _repo_root() -> Path:
    # CWD independence: resolve relative to this script location.
    return Path(__file__).resolve().parents[1]


def _build_sharepack(inputs: Inputs) -> None:
    root = _repo_root()

    week_dir = _week_dirname(inputs.week_index)

    exports_root = root / "artifacts" / "exports" / inputs.league_id / str(inputs.season) / week_dir
    if not exports_root.exists():
        raise SystemExit(
            f"ERROR: verified exports root not found: {exports_root}\n"
            "Expected approved exports under artifacts/exports/<league>/<season>/week_<NN>/..."
        )

    sources = _discover_approved_sources(exports_root)
    if not sources:
        raise SystemExit(
            f"ERROR: no approved markdown sources found under: {exports_root}\n"
            "Expected files matching **/*__approved_*.md (or **/*_approved_*.md)."
        )

    # Deterministic combined text with explicit provenance.
    parts: list[str] = []
    for p in sources:
        rel = p.resolve().relative_to(root)
        txt = _read_text(p)
        parts.append(f"<!-- SOURCE: {rel.as_posix()} -->\n" + txt.strip())
    combined = "\n\n---\n\n".join(parts).strip() + "\n"

    out_dir = root / "artifacts" / "creative" / inputs.league_id / str(inputs.season) / week_dir / "sharepack_v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    # README.md
    readme = [
        "# Sharepack (v1)",
        "",
        "Deterministic creative bundle generated from verified, approved exports.",
        "",
        "## Inputs",
        f"- league_id: `{inputs.league_id}`",
        f"- season: `{inputs.season}`",
        f"- week_index: `{inputs.week_index}`",
        "",
        "## Verified Sources (approved markdown)",
    ]
    for p in sources:
        rel = p.resolve().relative_to(root).as_posix()
        readme.append(f"- `{rel}`")
    readme.append("")
    _write_text(out_dir / "README.md", "\n".join(readme))

    # memes_caption_set_v1.md
    captions = _extract_caption_lines(combined, limit=25)
    memes_lines = ["# Memes (captions only) (v1)", "", "All lines below are extracted from verified approved sources.", ""]
    for i, c in enumerate(captions, start=1):
        memes_lines.append(f"{i}. {c}")
    memes_lines.append("")
    _write_text(out_dir / "memes_caption_set_v1.md", "\n".join(memes_lines))

    # commentary_short_v1.md
    excerpt = _extract_commentary_excerpt(combined, max_lines=20)
    commentary = [
        "# Commentary (short) (v1)",
        "",
        "Excerpted lines from verified approved sources (deterministic selection).",
        "",
        excerpt.strip(),
        "",
    ]
    _write_text(out_dir / "commentary_short_v1.md", "\n".join([ln for ln in commentary if ln is not None]))

    # stats_fun_facts_v1.md
    facts = _extract_fun_facts(combined, limit=25)
    facts_lines = ["# Stats & Fun Facts (v1)", "", "Lines below are extracted from verified approved sources.", ""]
    for f in facts:
        facts_lines.append(f"- {f}")
    facts_lines.append("")
    _write_text(out_dir / "stats_fun_facts_v1.md", "\n".join(facts_lines))

    # manifest_v1.json (computed from the other required files; excludes itself while computing)
    files_for_manifest = [f for f in REQUIRED_FILES if f != "manifest_v1.json"]
    manifest_files = []
    for rel_name in sorted(files_for_manifest):
        fp = out_dir / rel_name
        b = fp.read_bytes()
        manifest_files.append(
            {
                "path": rel_name,
                "sha256": _sha256_bytes(b),
                "bytes": len(b),
            }
        )

    manifest = {
        "version": "v1",
        "root": "sharepack_v1",
        "inputs": {"league_id": inputs.league_id, "season": inputs.season, "week_index": inputs.week_index},
        "files": manifest_files,
    }
    manifest_txt = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    _write_text(out_dir / "manifest_v1.json", manifest_txt)

    # Final sanity: required files present, no missing.
    missing = [f for f in REQUIRED_FILES if not (out_dir / f).is_file()]
    if missing:
        raise SystemExit(f"ERROR: missing required output files: {missing}")

    print(f"OK: wrote sharepack to {out_dir}")


def main() -> None:
    inputs = _parse_args()
    _build_sharepack(inputs)


if __name__ == "__main__":
    main()
"""

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def main() -> None:
    if TARGET.exists():
        cur = _read(TARGET)
        if cur == GEN_TEXT:
            print("OK")
            return
        raise SystemExit(
            f"REFUSE: {TARGET} exists but does not match expected generator content. "
            "Manual edits detected; update patcher intentionally."
        )

    _write(TARGET, GEN_TEXT)
    print("OK")

if __name__ == "__main__":
    main()
