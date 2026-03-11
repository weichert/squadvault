#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

ROW = "scripts/gate_no_xtrace_v1.sh\tNo forbidden set -x in prove/gate scripts (v1)"

def parse_row(row: str) -> tuple[str, str]:
    if "\t" not in row:
        raise RuntimeError(f"invalid row: {row}")
    rel_path, label = row.split("\t", 1)
    rel_path = rel_path.strip()
    label = label.strip()
    if not rel_path or not label:
        raise RuntimeError(f"invalid row: {row}")
    return rel_path, label

def main() -> int:
    if not REGISTRY.is_file():
        raise RuntimeError(f"missing registry: {REGISTRY}")

    target_path, target_label = parse_row(ROW)
    existing: dict[str, str] = {}

    for raw in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rel_path, label = parse_row(raw)
        if rel_path in existing and existing[rel_path] != label:
            raise RuntimeError(f"conflicting registry row for {rel_path}")
        existing[rel_path] = label

    if target_path in existing:
        if existing[target_path] != target_label:
            raise RuntimeError(
                f"registry row mismatch for {target_path}: "
                f"have {existing[target_path]!r}, want {target_label!r}"
            )
        return 0

    existing[target_path] = target_label
    new_text = "\n".join(f"{rel_path}\t{existing[rel_path]}" for rel_path in sorted(existing)) + "\n"
    REGISTRY.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
