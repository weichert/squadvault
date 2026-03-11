from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

# The gate invocation to move (allow optional leading "bash").
CALL_RE = re.compile(r"^\s*(?:bash\s+)?scripts/gate_no_mapfile_readarray_in_scripts_v1\.sh\b.*\n?$")

# If the line immediately above looks like a gate banner echo, move it too.
BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')

# Canonical insertion point: immediately after this gate invocation.
ANCHOR_RE = re.compile(r"^\s*(?:bash\s+)?scripts/gate_no_double_scripts_prefix_v2\.sh\b.*\n?$")


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    call_idx = None
    for i, line in enumerate(lines):
        if CALL_RE.match(line):
            call_idx = i
            break
    if call_idx is None:
        print("ERROR: refused to patch (could not find gate_no_mapfile_readarray_in_scripts invocation).", file=sys.stderr)
        return 3

    # Determine block to move: [banner?, call]
    start = call_idx
    if call_idx - 1 >= 0 and BANNER_RE.match(lines[call_idx - 1]):
        start = call_idx - 1
    block = lines[start : call_idx + 1]

    # Find anchor (in original file)
    anchor_idx = None
    for i, line in enumerate(lines):
        if ANCHOR_RE.match(line):
            anchor_idx = i
            break
    if anchor_idx is None:
        print("ERROR: refused to patch (anchor not found).", file=sys.stderr)
        print("Missing: scripts/gate_no_double_scripts_prefix_v2.sh invocation", file=sys.stderr)
        return 4

    # If already immediately after anchor, no-op
    insert_at = anchor_idx + 1
    if lines[insert_at : insert_at + len(block)] == block:
        return 0

    # Remove the block
    new_lines = lines[:start] + lines[call_idx + 1 :]

    # Re-find anchor after removal (safer)
    new_anchor_idx = None
    for i, line in enumerate(new_lines):
        if ANCHOR_RE.match(line):
            new_anchor_idx = i
            break
    if new_anchor_idx is None:
        print("ERROR: internal: anchor disappeared after removal.", file=sys.stderr)
        return 5

    out = new_lines[: new_anchor_idx + 1] + block + new_lines[new_anchor_idx + 1 :]
    new_src = "".join(out)

    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
