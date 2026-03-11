#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

NEEDLE_1 = "SV_STRICT_EXPORTS=1 bash scripts/prove_golden_path.sh"
ANCHOR = re.compile(r"^\s*(?:bash\s+)?scripts/prove_golden_path\.sh\b", re.M)

def _repo_root_from_this_file() -> Path:
    return Path(__file__).resolve().parent.parent

def main() -> int:
    os.chdir(_repo_root_from_this_file())

    if not TARGET.exists():
        print(f"ERROR: missing {TARGET}", file=sys.stderr)
        return 2

    s = TARGET.read_text(encoding="utf-8")

    if NEEDLE_1 in s:
        # Already strict (your repo currently has it twice).
        print("OK: strict exports already enabled in prove_ci.sh for golden path")
        return 0

    if not ANCHOR.search(s):
        print("ERROR: could not find prove_golden_path.sh invocation in prove_ci.sh", file=sys.stderr)
        return 3

    # Prefix the first occurrence; do not attempt clever multi-editing without seeing file shape.
    def repl(m: re.Match) -> str:
        line = m.group(0).strip()
        if line.startswith("bash "):
            return "SV_STRICT_EXPORTS=1 " + line
        return "SV_STRICT_EXPORTS=1 bash " + line

    s2, n = ANCHOR.subn(repl, s, count=1)
    if n != 1:
        print(f"ERROR: expected to patch exactly 1 invocation; got {n}", file=sys.stderr)
        return 4

    TARGET.write_text(s2, encoding="utf-8")
    print("OK: enabled strict exports for golden path invocation in prove_ci.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
