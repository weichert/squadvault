#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_eal_calibration_type_a_v1.sh")

MARK = "SV_PATCH: prune redundant TEST_DIR tail + dedupe tracked pytest run"

ANCHOR = "# Always run from repo root (pytest path resolution depends on cwd)"
DEDUP_ANCHOR = "# Run exactly what git says exists"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines()

    if any(MARK in ln for ln in lines):
        print("OK: prune patch already applied.")
        return

    # 1) Remove the redundant second tracked pytest run block if present.
    # We keep the earlier SV_PATCH tracked-only pytest run and remove:
    #   # Run exactly what git says exists
    #   ./scripts/py -m pytest -q "${eal_tests[@]}"
    new_lines: list[str] = []
    i = 0
    removed_dedupe = False
    while i < len(lines):
        ln = lines[i]
        if (not removed_dedupe) and ln.strip() == DEDUP_ANCHOR:
            # drop this line plus subsequent blank lines and the immediate pytest line (if it matches)
            removed_dedupe = True
            i += 1
            # skip optional blank lines
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines) and 'pytest -q "${eal_tests[@]}"' in lines[i]:
                i += 1
            # also skip trailing blank lines after that block
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        new_lines.append(ln)
        i += 1

    lines = new_lines

    # 2) Prune everything from ANCHOR to EOF.
    try:
        anchor_idx = next(i for i, ln in enumerate(lines) if ln.strip() == ANCHOR)
    except StopIteration:
        raise SystemExit(
            f"ERROR: could not find anchor line to prune tail:\n  {ANCHOR}\n"
        )

    pruned = lines[:anchor_idx]
    pruned.append(f"# {MARK}")
    pruned.append("# Removed redundant TEST_DIR auto-detect tail (case-collision risk).")
    pruned.append("# EAL tests are executed via git-tracked eal_tests[] above.")
    pruned.append(f"# /{MARK}")

    TARGET.write_text("\n".join(pruned) + "\n", encoding="utf-8")
    print("OK: pruned redundant tail + deduped tracked pytest run.")

if __name__ == "__main__":
    main()
