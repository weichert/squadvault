#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
PROVE = REPO / "scripts" / "prove_ci.sh"
REGISTRY = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
OUT = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Surface_Fingerprint_v1.txt"

PROVE_BEGIN = "# SV_GATE: proof_registry_excludes_gates (v1) begin"
PROVE_END = 'echo "==> Gate: no pasted terminal banners in scripts/"'

INDEX_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
INDEX_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"


def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)


def read_text(path: Path) -> str:
    if not path.is_file():
        die(f"ERROR: missing required file: {path}")
    return path.read_text(encoding="utf-8")


def normalize_lines(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in text.split("\n")]


def extract_between_lines(path: Path, begin_line: str, end_line: str) -> str:
    lines = normalize_lines(read_text(path))
    try:
        begin_i = lines.index(begin_line)
    except ValueError:
        die(f"ERROR: begin marker not found in {path}: {begin_line}")
    try:
        end_i = lines.index(end_line, begin_i + 1)
    except ValueError:
        die(f"ERROR: end marker not found in {path}: {end_line}")
    if end_i <= begin_i:
        die(f"ERROR: invalid marker ordering in {path}")
    block = lines[begin_i:end_i]
    return "\n".join(block).strip() + "\n"


def extract_between_markers(path: Path, begin_marker: str, end_marker: str) -> str:
    lines = normalize_lines(read_text(path))
    begin_idxs = [i for i, line in enumerate(lines) if line == begin_marker]
    end_idxs = [i for i, line in enumerate(lines) if line == end_marker]
    if len(begin_idxs) != 1 or len(end_idxs) != 1:
        die(
            f"ERROR: expected exactly one bounded marker pair in {path}: "
            f"{begin_marker} / {end_marker}"
        )
    begin_i = begin_idxs[0]
    end_i = end_idxs[0]
    if end_i <= begin_i:
        die(f"ERROR: invalid marker ordering in {path}")
    block = lines[begin_i : end_i + 1]
    return "\n".join(block).strip() + "\n"


def registry_block(path: Path) -> str:
    lines = normalize_lines(read_text(path))
    filtered = [line for line in lines if line != ""]
    return "\n".join(filtered).strip() + "\n"


def canonical_payload() -> str:
    sections = [
        "### CI_GUARDRAILS_PROVE_BLOCK_BEGIN ###",
        extract_between_lines(PROVE, PROVE_BEGIN, PROVE_END).rstrip("\n"),
        "### CI_GUARDRAILS_PROVE_BLOCK_END ###",
        "### CI_GUARDRAILS_REGISTRY_BEGIN ###",
        registry_block(REGISTRY).rstrip("\n"),
        "### CI_GUARDRAILS_REGISTRY_END ###",
        "### CI_GUARDRAILS_INDEX_BLOCK_BEGIN ###",
        extract_between_markers(INDEX, INDEX_BEGIN, INDEX_END).rstrip("\n"),
        "### CI_GUARDRAILS_INDEX_BLOCK_END ###",
    ]
    return "\n".join(sections) + "\n"


def fingerprint_text() -> str:
    payload = canonical_payload()
    sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return sha + "\n"


def write_if_changed(path: Path, text: str) -> bool:
    old = None
    if path.exists():
        old = path.read_text(encoding="utf-8")
    if old == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    text = fingerprint_text()
    changed = write_if_changed(OUT, text)
    if changed:
        print(f"OK: wrote {OUT.relative_to(REPO)}")
    else:
        print("OK: fingerprint already canonical (noop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
