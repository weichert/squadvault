from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

# Any invocation of the worktree cleanliness gate (assert/end variants).
WT_CALL_RE = re.compile(r"^\s*(?:bash\s+)?scripts/gate_worktree_cleanliness_v1\.sh\b.*\n?$")

# Optional banner line to carry with the immediately-following call.
BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')

# Canonical insertion point: immediately after this gate invocation.
ANCHOR_RE = re.compile(r"^\s*(?:bash\s+)?scripts/gate_standard_show_input_need_coverage_v1\.sh\b.*\n?$")


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # Collect all (banner?, call) pairs for worktree_cleanliness in their current order.
    blocks: list[list[str]] = []
    i = 0
    while i < len(lines):
        if WT_CALL_RE.match(lines[i]):
            start = i
            if i - 1 >= 0 and BANNER_RE.match(lines[i - 1]):
                # Only treat it as paired if it is immediately preceding.
                # (We will remove it alongside the call.)
                start = i - 1
            block = lines[start : i + 1]
            blocks.append(block)
            # Mark consumed lines by advancing; removal done later by filtering.
            i += 1
            continue
        i += 1

    if not blocks:
        print("ERROR: refused to patch (no gate_worktree_cleanliness_v1.sh invocations found).", file=sys.stderr)
        return 3

    # Flatten blocks for equality checks and removal.
    # We'll remove by index mask to avoid accidental duplicate-line removal.
    remove = [False] * len(lines)

    for i in range(len(lines)):
        if WT_CALL_RE.match(lines[i]):
            remove[i] = True
            if i - 1 >= 0 and BANNER_RE.match(lines[i - 1]):
                remove[i - 1] = True

    # Build list without the removed lines
    new_lines = [line for j, line in enumerate(lines) if not remove[j]]

    # Find anchor in new_lines
    anchor_idx = None
    for j, line in enumerate(new_lines):
        if ANCHOR_RE.match(line):
            anchor_idx = j
            break

    if anchor_idx is None:
        print("ERROR: refused to patch (anchor not found).", file=sys.stderr)
        print("Missing: scripts/gate_standard_show_input_need_coverage_v1.sh invocation", file=sys.stderr)
        return 4

    # Construct insertion payload (all blocks in original order, concatenated)
    payload: list[str] = []
    for b in blocks:
        payload.extend(b)

    # No-op if payload already sits immediately after anchor (rare, but safe)
    insert_at = anchor_idx + 1
    if new_lines[insert_at : insert_at + len(payload)] == payload:
        return 0

    out = new_lines[:insert_at] + payload + new_lines[insert_at:]
    new_src = "".join(out)

    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
