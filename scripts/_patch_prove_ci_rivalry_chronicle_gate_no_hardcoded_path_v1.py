from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("scripts/prove_ci.sh")

OLD = "bash scripts/gate_rivalry_chronicle_output_contract_v1.sh artifacts/exports/70985/2024/week_06/rivalry_chronicle_v1__approved_latest.md"
NEW = "bash scripts/gate_rivalry_chronicle_output_contract_v1.sh"

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing file: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")

    if OLD not in src:
        # Idempotence / safety: if already patched, no-op; if unexpected, refuse.
        if NEW in src:
            return 0
        print("ERROR: refused to patch (expected invocation not found).", file=sys.stderr)
        print(f"Missing exact line:\n{OLD}", file=sys.stderr)
        return 3

    # Replace exactly once.
    new_src = src.replace(OLD, NEW, 1)

    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
