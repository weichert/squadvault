#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

FILES = [
    Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
]

MARK_BEGIN = "<!-- SV_PATCH: nac fingerprint preflight doc (v1) -->\n"
MARK_END   = "<!-- /SV_PATCH: nac fingerprint preflight doc (v1) -->\n"

BLOCK = (
    MARK_BEGIN +
    "- **NAC fingerprint preflight normalization (Golden Path):** "
    "`scripts/prove_golden_path.sh` normalizes placeholder "
    "`Selection fingerprint: test-fingerprint` to a **64-lower-hex** fingerprint "
    "before running the NAC harness (required by `Tests/_nac_check_assembly_plain_v1.py`).\n"
    + MARK_END
)

def _read(p: Path) -> str:
    if not p.exists():
        raise SystemExit(f"ERROR: missing file: {p}")
    return p.read_text(encoding="utf-8")

def _write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")

def _already_patched(text: str) -> bool:
    return (MARK_BEGIN in text) and (MARK_END in text)

def _insert_before_first_h2(text: str) -> str:
    lines = text.splitlines(True)

    # Find first markdown H2 heading ("## ...")
    idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            idx = i
            break

    if idx is None:
        # No H2; append at end with spacing.
        if not text.endswith("\n"):
            text += "\n"
        return text + "\n" + BLOCK

    # Insert a blank line separation if needed.
    insert = "\n" + BLOCK + "\n"
    lines.insert(idx, insert)
    return "".join(lines)

def main() -> None:
    changed_any = False

    for p in FILES:
        orig = _read(p)
        if _already_patched(orig):
            print(f"OK: already patched: {p}")
            continue

        new = _insert_before_first_h2(orig)

        # Postconditions
        if new.count(MARK_BEGIN) != 1 or new.count(MARK_END) != 1:
            raise SystemExit(f"ERROR: marker count unexpected after patch: {p}")

        _write(p, new)
        changed_any = True
        print(f"OK: patched: {p}")

    print("=== Patch: docs register NAC fingerprint preflight (v1) ===")
    print(f"changed={'yes' if changed_any else 'no'}")

if __name__ == "__main__":
    main()
