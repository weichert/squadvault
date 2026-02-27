from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

# Gate invocation line:
#   ./scripts/gate_foo.sh ...
#   bash scripts/gate_foo.sh ...
#   scripts/gate_foo.sh ...   (rare, but tolerate)
GATE_CALL_RE = re.compile(
    r"^(?P<indent>\s*)(?:(?:bash)\s+)?(?:(?:\./)?)scripts/(?P<gate>gate_[A-Za-z0-9_]+\.sh)\b(?P<args>.*)\n?$"
)

# Banner line we consider "attached" only if it is immediately above a gate call.
BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')

def _canonical_call(indent: str, gate: str, args: str) -> str:
    # Preserve args exactly (including leading spaces).
    if gate == "gate_no_xtrace_v1.sh":
        return f"{indent}./scripts/{gate}{args}\n"
    return f"{indent}bash scripts/{gate}{args}\n"

def _sort_key(call_line: str) -> bytes:
    # Gate expects lexicographic byte-order by path/line.
    return call_line.encode("utf-8")

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # Build "slots": each gate block becomes one slot placeholder in the output skeleton.
    # We collect blocks (banner?, canonical_call) in discovery order, then sort them, then
    # fill the placeholders sequentially.
    skeleton: list[str] = []
    blocks: list[tuple[str, list[str]]] = []

    i = 0
    while i < len(lines):
        ln = lines[i]

        # Banner + gate call => one movable block / one slot
        if BANNER_RE.match(ln) and i + 1 < len(lines):
            m2 = GATE_CALL_RE.match(lines[i + 1])
            if m2:
                indent = m2.group("indent")
                gate = m2.group("gate")
                args = m2.group("args")
                call = _canonical_call(indent, gate, args)
                blocks.append((call, [ln, call]))
                skeleton.append("__SV_GATE_SLOT__\n")
                i += 2
                continue

        # Gate call alone => one movable block / one slot
        m = GATE_CALL_RE.match(ln)
        if m:
            indent = m.group("indent")
            gate = m.group("gate")
            args = m.group("args")
            call = _canonical_call(indent, gate, args)
            blocks.append((call, [call]))
            skeleton.append("__SV_GATE_SLOT__\n")
            i += 1
            continue

        # Non-gate line: preserved exactly, in place
        skeleton.append(ln)
        i += 1

    if not blocks:
        print("ERROR: refused to patch (no gate invocations found).", file=sys.stderr)
        return 3

    # Sort blocks by canonical call line bytes
    blocks_sorted = sorted(blocks, key=lambda t: _sort_key(t[0]))

    # Fill skeleton slots with sorted blocks in order
    out: list[str] = []
    slot_idx = 0
    for ln in skeleton:
        if ln == "__SV_GATE_SLOT__\n":
            if slot_idx >= len(blocks_sorted):
                print("ERROR: internal: too many slots.", file=sys.stderr)
                return 4
            out.extend(blocks_sorted[slot_idx][1])
            slot_idx += 1
        else:
            out.append(ln)

    if slot_idx != len(blocks_sorted):
        print("ERROR: internal: unused blocks after fill.", file=sys.stderr)
        return 5

    new_src = "".join(out)
    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
