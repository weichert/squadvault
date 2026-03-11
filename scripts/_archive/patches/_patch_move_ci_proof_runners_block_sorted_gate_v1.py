from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/prove_ci.sh")

ECHO_LINE = 'echo "=== Gate: CI proof runners block sorted (v1) ==="\n'
CALL_LINE = "bash scripts/gate_ci_proof_runners_block_sorted_v1.sh\n"

ANCHOR = "bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh"

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # No-op if already directly after anchor
    for i, line in enumerate(lines):
        if ANCHOR in line:
            if i + 2 < len(lines) and lines[i + 1] == ECHO_LINE and lines[i + 2] == CALL_LINE:
                return 0
            break

    # Find the block
    block_start = None
    for i in range(len(lines) - 1):
        if lines[i] == ECHO_LINE and lines[i + 1] == CALL_LINE:
            block_start = i
            break

    if block_start is None:
        print("ERROR: refused to patch (could not find CI proof runners gate block).", file=sys.stderr)
        print(f"Expected:\n{ECHO_LINE}{CALL_LINE}", file=sys.stderr)
        return 3

    block = [lines[block_start], lines[block_start + 1]]

    # Remove it
    new_lines = lines[:block_start] + lines[block_start + 2 :]

    # Find anchor and insert after it
    anchor_idx = None
    for i, line in enumerate(new_lines):
        if ANCHOR in line:
            anchor_idx = i
            break

    if anchor_idx is None:
        print("ERROR: refused to patch (anchor not found).", file=sys.stderr)
        print(f"Missing: {ANCHOR}", file=sys.stderr)
        return 4

    out = new_lines[: anchor_idx + 1] + block + new_lines[anchor_idx + 1 :]

    new_src = "".join(out)
    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
