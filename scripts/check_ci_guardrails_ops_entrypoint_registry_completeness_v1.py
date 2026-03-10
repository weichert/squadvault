from __future__ import annotations

from pathlib import Path
import csv
import re
import sys
from collections import defaultdict

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

BLOCK_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
BLOCK_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

PATH_PATTERNS = (
    r"`(scripts/[A-Za-z0-9_./-]+\.sh)`",
    r"`(scripts/[A-Za-z0-9_./-]+\.py)`",
    r"\b(scripts/[A-Za-z0-9_./-]+\.sh)\b",
    r"\b(scripts/[A-Za-z0-9_./-]+\.py)\b",
)

def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)

def read_text(path: Path) -> str:
    if not path.exists():
        die(f"ERROR: missing required file: {path.relative_to(REPO)}")
    return path.read_text(encoding="utf-8")

def find_bounded_block(text: str) -> str:
    if BLOCK_BEGIN not in text or BLOCK_END not in text:
        die(
            "ERROR: could not locate bounded Ops guardrails block in "
            "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
        )
    bi = text.index(BLOCK_BEGIN) + len(BLOCK_BEGIN)
    ei = text.index(BLOCK_END, bi)
    return text[bi:ei]

def extract_entrypoints(block: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for pat in PATH_PATTERNS:
        for m in re.finditer(pat, block):
            val = m.group(1).strip()
            if not val.startswith("scripts/"):
                continue
            if val not in seen:
                seen.add(val)
                out.append(val)
    out.sort()
    if not out:
        die("ERROR: bounded Ops guardrails block contained no entrypoint paths")
    return out

def parse_tsv_rows(path: Path) -> dict[str, list[list[str]]]:
    text = read_text(path)
    rows_by_entrypoint: dict[str, list[list[str]]] = defaultdict(list)

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw_line.split("\t")
        if len(parts) != 2:
            die(
                f"ERROR: invalid label registry row at {path.relative_to(REPO)}:{lineno}: "
                "expected exactly <path><TAB><label>"
            )
        rel_path = parts[0].strip()
        label = parts[1].strip()
        if not rel_path or not label:
            die(
                f"ERROR: invalid label registry row at {path.relative_to(REPO)}:{lineno}: "
                "empty path or label"
            )
        rows_by_entrypoint[rel_path].append(parts)

    if not rows_by_entrypoint:
        die(f"ERROR: empty registry TSV: {path.relative_to(REPO)}")

    return dict(rows_by_entrypoint)

def main() -> int:
    doc_text = read_text(DOC)
    block = find_bounded_block(doc_text)
    rendered = extract_entrypoints(block)
    rows_by_entrypoint = parse_tsv_rows(TSV)

    missing: list[str] = []
    duplicate: list[str] = []

    for ep in rendered:
        count = len(rows_by_entrypoint.get(ep, []))
        if count == 0:
            missing.append(ep)
        elif count > 1:
            duplicate.append(ep)

    if missing or duplicate:
        if missing:
            print("ERROR: missing registry row(s) for rendered bounded-block entrypoint(s):", file=sys.stderr)
            for ep in sorted(missing):
                print(f"  - {ep}", file=sys.stderr)
        if duplicate:
            print("ERROR: duplicate registry row(s) for rendered bounded-block entrypoint(s):", file=sys.stderr)
            for ep in sorted(duplicate):
                print(f"  - {ep}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
