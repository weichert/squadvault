#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_eal_calibration_type_a_v1.sh")
MARK = "SV_PATCH: drop TEST_DIR auto-detect + duplicate pytest runs (case-safe)"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines()

    if any(MARK in ln for ln in lines):
        print("OK: patch already applied.")
        return

    idxs = [i for i, ln in enumerate(lines) if 'echo "Using TEST_DIR=${TEST_DIR}"' in ln]
    if len(idxs) < 2:
        raise SystemExit(f"ERROR: expected >=2 Using TEST_DIR echoes; found {len(idxs)}")

    second = idxs[1]

    new_lines = []
    new_lines.extend(lines[:second])
    new_lines.append(f"# {MARK}")
    new_lines.append("# Repo uses git-tracked test paths; avoid tests/ vs Tests/ case collisions.")
    new_lines.append("# The tracked-only pytest run is executed earlier in this script.")
    new_lines.append(f"# /{MARK}")

    TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("OK: removed TEST_DIR block and duplicate pytest runs (dropped second pass).")

if __name__ == "__main__":
    main()
