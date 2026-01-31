#!/usr/bin/env python3
from __future__ import annotations

import io
import os
import sys

BANNER_BEGIN = "# === CI CLEANLINESS GUARDRAIL (v1) ==="
BANNER_END   = "# === /CI CLEANLINESS GUARDRAIL (v1) ==="

INSERT_BLOCK = f"""{BANNER_BEGIN}
# Enforce: CI proofs must not dirty the working tree.
# - Fail early if starting dirty
# - Fail on exit if anything dirtied the repo (even on proof failure)
./scripts/check_repo_cleanliness_ci.sh --phase before
trap './scripts/check_repo_cleanliness_ci.sh --phase after' EXIT
{BANNER_END}
"""

def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    target = os.path.join(repo_root, "scripts", "prove_ci.sh")

    if not os.path.exists(target):
        print(f"ERROR: missing target: {target}", file=sys.stderr)
        return 2

    with io.open(target, "r", encoding="utf-8") as f:
        src = f.read()

    if BANNER_BEGIN in src:
        print("OK: guardrail already present (no-op).")
        return 0

    # Insert after the first occurrence of 'set -euo pipefail' if present,
    # otherwise fail (we don't guess structure for an authoritative entrypoint).
    needle = "set -euo pipefail"
    idx = src.find(needle)
    if idx == -1:
        print("ERROR: could not find 'set -euo pipefail' anchor in scripts/prove_ci.sh", file=sys.stderr)
        return 2

    # Find end of that line
    line_end = src.find("\n", idx)
    if line_end == -1:
        print("ERROR: unexpected file shape (no newline after set -euo pipefail)", file=sys.stderr)
        return 2

    patched = src[: line_end + 1] + "\n" + INSERT_BLOCK + "\n" + src[line_end + 1 :]

    with io.open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(patched)

    print("OK: patched scripts/prove_ci.sh (added CI cleanliness guardrail v1).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
