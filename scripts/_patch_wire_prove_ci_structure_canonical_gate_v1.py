from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

ALREADY = re.compile(r"\bgate_prove_ci_structure_canonical_v1\.sh\b")
ANCHOR = re.compile(r"\bbash\s+scripts/gate_enforce_test_db_routing_v1\.sh\b")

INSERT = [
    'echo "=== Gate: prove_ci structure canonical (v1) ==="\n',
    "bash scripts/gate_prove_ci_structure_canonical_v1.sh\n",
]

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    if ALREADY.search(src):
        return 0

    lines = src.splitlines(keepends=True)
    out: list[str] = []
    inserted = False

    for line in lines:
        out.append(line)
        if (not inserted) and ANCHOR.search(line):
            out.extend(INSERT)
            inserted = True

    if not inserted:
        print("ERROR: refused to patch (anchor not found).", file=sys.stderr)
        print("Missing: bash scripts/gate_enforce_test_db_routing_v1.sh", file=sys.stderr)
        return 3

    TARGET.write_text("".join(out), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
