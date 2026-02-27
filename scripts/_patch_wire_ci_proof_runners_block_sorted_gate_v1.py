from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

ALREADY_RE = re.compile(r"\bgate_ci_proof_runners_block_sorted_v1\.sh\b")

# A generic "Gate banner" line used throughout prove_ci
GATE_BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:\s*.*===["\']\s*$')

INSERT_BLOCK = [
    'echo "=== Gate: CI proof runners block sorted (v1) ==="\n',
    "bash scripts/gate_ci_proof_runners_block_sorted_v1.sh\n",
]


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    if ALREADY_RE.search(src):
        return 0

    lines = src.splitlines(keepends=True)

    # Insert immediately before the first "=== Gate:" banner.
    insert_at = None
    for i, line in enumerate(lines):
        if GATE_BANNER_RE.match(line):
            insert_at = i
            break

    if insert_at is None:
        print("ERROR: refused to patch scripts/prove_ci.sh (could not find any '=== Gate:' banner line).", file=sys.stderr)
        print("Expected at least one line like: echo \"=== Gate: ... ===\"", file=sys.stderr)
        return 3

    new_lines = lines[:insert_at] + INSERT_BLOCK + lines[insert_at:]
    new_src = "".join(new_lines)

    if new_src == src:
        return 0

    TARGET.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
