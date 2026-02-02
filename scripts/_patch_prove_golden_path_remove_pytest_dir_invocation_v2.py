# DEPRECATED — DO NOT USE
# Superseded by:
#   scripts/_patch_prove_golden_path_pin_pytest_list_v3.py
#
# This patcher is retained for audit/history only.
# Golden Path pytest pinning was finalized in v3.

from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
FORBIDDEN_LINE = "pytest -q Tests"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    out: list[str] = []
    removed = 0
    for line in lines:
        if line.strip() == FORBIDDEN_LINE:
            removed += 1
            continue
        out.append(line)

    if removed == 0:
        # idempotent: ensure no standalone forbidden invocation exists
        for line in lines:
            if line.strip() == FORBIDDEN_LINE:
                raise SystemExit("ERROR: internal: standalone forbidden line still present")
        return

    new = "".join(out)

    # Postcondition: no standalone invocation remains (comments may mention it).
    for line in new.splitlines():
        if line.strip() == FORBIDDEN_LINE:
            raise SystemExit("ERROR: standalone forbidden invocation still present after removal")

    TARGET.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
