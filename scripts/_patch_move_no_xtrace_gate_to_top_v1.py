from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

# Target call (exactly ./scripts/... per expected sorted order).
CALL_RE = re.compile(r"^\s*\./scripts/gate_no_xtrace_v1\.sh\b.*\n?$")

# Optional banner line immediately preceding the call.
BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')

# Anchor: insert immediately BEFORE this (i.e., no_xtrace should precede it).
ANCHOR_RE = re.compile(r"^\s*bash\s+scripts/gate_allowlist_patchers_must_insert_sorted_v1\.sh\b.*\n?$")


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
        print("ERROR: refused to patch (could not find ./scripts/gate_no_xtrace_v1.sh invocation).", file=sys.stderr)
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
        print("Missing: bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh invocation", file=sys.stderr)
        return 4

    # If already immediately before anchor, no-op
    if lines[anchor_idx - len(block) : anchor_idx] == block:
        return 0

    # Remove the block
    new_lines = lines[:start] + lines[call_idx + 1 :]

    # Re-find anchor after removal
    new_anchor_idx = None
    for i, line in enumerate(new_lines):
        if ANCHOR_RE.match(line):
            new_anchor_idx = i
            break
    if new_anchor_idx is None:
        print("ERROR: internal: anchor disappeared after removal.", file=sys.stderr)
        return 5

    # Insert block immediately before anchor
    out = new_lines[:new_anchor_idx] + block + new_lines[new_anchor_idx:]
    new_src = "".join(out)

    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
