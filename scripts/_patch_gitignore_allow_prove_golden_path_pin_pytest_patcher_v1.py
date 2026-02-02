# DEPRECATED — DO NOT USE
# Superseded by:
#   scripts/_patch_prove_golden_path_pin_pytest_list_v3.py
#
# This patcher is retained for audit/history only.
# Golden Path pytest pinning was finalized in v3.

from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")
IGNORE_LINE = "scripts/_patch_*.py"
ALLOWLINE = "!scripts/_patch_prove_golden_path_pin_pytest_list_v1.py"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    s = TARGET.read_text(encoding="utf-8")
    if IGNORE_LINE not in s:
        raise SystemExit(f"ERROR: could not find ignore rule: {IGNORE_LINE}")

    if ALLOWLINE in s:
        return  # idempotent

    lines = s.splitlines(True)

    ignore_idx = None
    first_canonical_idx = None

    for i, line in enumerate(lines):
        if ignore_idx is None and line.rstrip("\n") == IGNORE_LINE:
            ignore_idx = i
        if first_canonical_idx is None and line.rstrip("\n") == "# Canonical patchers (DO track these)":
            first_canonical_idx = i

    if ignore_idx is None:
        raise SystemExit("ERROR: internal: ignore_idx missing")

    # Prefer inserting inside the first canonical patchers list (right after its header),
    # otherwise insert immediately after the ignore line.
    if first_canonical_idx is not None:
        insert_at = first_canonical_idx + 1
    else:
        insert_at = ignore_idx + 1

    lines.insert(insert_at, ALLOWLINE + "\n")
    TARGET.write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
