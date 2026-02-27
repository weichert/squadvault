from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

# Match any gate invocation line that references scripts/gate_*.sh with optional bash and optional leading ./ on scripts.
# Capture:
#  - indent
#  - gate basename (gate_foo.sh)
#  - args (rest of line, excluding trailing newline)
GATE_CALL_RE = re.compile(
    r"^(?P<indent>\s*)(?:(?:bash)\s+)?(?:(?:\./)?)scripts/(?P<gate>gate_[A-Za-z0-9_]+\.sh)\b(?P<args>.*)\n?$"
)

BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')

def _key_for_call(call_line: str) -> bytes:
    # Sort by the actual line bytes (matches the gate).
    return call_line.encode("utf-8")

def _canonical_call(gate: str, args: str) -> str:
    # Preserve args exactly (including leading spaces).
    if gate == "gate_no_xtrace_v1.sh":
        return f"./scripts/{gate}{args}\n"
    return f"bash scripts/{gate}{args}\n"

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # Find all gate call indices.
    call_idxs: list[int] = []
    for i, ln in enumerate(lines):
        if GATE_CALL_RE.match(ln):
            call_idxs.append(i)

    if not call_idxs:
        print("ERROR: refused to patch (no gate invocations found).", file=sys.stderr)
        return 3

    # We only reorder within the minimal span from first..last gate call.
    first = call_idxs[0]
    last = call_idxs[-1]

    region = lines[first : last + 1]

    # Parse region into blocks: (canonical_call_line, [banner?, canonical_call_line, blanks...])
    blocks: list[tuple[str, list[str]]] = []

    i = 0
    while i < len(region):
        ln = region[i]

        # Banner + gate call => paired block
        if BANNER_RE.match(ln) and i + 1 < len(region) and GATE_CALL_RE.match(region[i + 1]):
            m = GATE_CALL_RE.match(region[i + 1])
            assert m is not None
            gate = m.group("gate")
            args = m.group("args")
            call = _canonical_call(gate, args)
            blk = [ln, call]
            blocks.append((call, blk))
            i += 2
            continue

        # Gate call alone
        m = GATE_CALL_RE.match(ln)
        if m:
            gate = m.group("gate")
            args = m.group("args")
            call = _canonical_call(gate, args)
            blk = [call]
            blocks.append((call, blk))
            i += 1
            continue

        # Blank lines inside region: attach to previous block if any; otherwise keep as prefix pseudo-block
        if ln.strip() == "":
            if blocks:
                blocks[-1][1].append(ln)
            else:
                blocks.append(("", [ln]))
            i += 1
            continue

        # Any other non-blank line: keep it in-place by refusing to patch.
        # This matches the original intent: reorder only gate invocation lines in prove_ci.
        print("ERROR: refused to patch (unexpected non-gate line inside gate region).", file=sys.stderr)
        print(f"Line: {ln.rstrip()}", file=sys.stderr)
        return 4

    # Separate prefix pseudo-blocks (leading blanks) from sortable gate blocks.
    prefix: list[list[str]] = []
    sortable: list[tuple[str, list[str]]] = []
    for call, blk in blocks:
        if call == "":
            prefix.append(blk)
        else:
            sortable.append((call, blk))

    sorted_blocks = sorted(sortable, key=lambda t: _key_for_call(t[0]))

    new_region: list[str] = []
    for blk in prefix:
        new_region.extend(blk)
    for _, blk in sorted_blocks:
        new_region.extend(blk)

    new_lines = lines[:first] + new_region + lines[last + 1 :]
    new_src = "".join(new_lines)

    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
