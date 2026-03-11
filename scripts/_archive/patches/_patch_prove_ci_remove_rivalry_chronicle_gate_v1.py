from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("scripts/prove_ci.sh")

# Current invocation after your last patch:
LINE = "bash scripts/gate_rivalry_chronicle_output_contract_v1.sh\n"

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing file: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")

    if LINE not in src:
        # If already removed, no-op.
        if "gate_rivalry_chronicle_output_contract_v1.sh" not in src:
            return 0
        print("ERROR: refused to patch (unexpected rivalry gate invocation form).", file=sys.stderr)
        return 3

    new_src = src.replace(LINE, "", 1)

    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
