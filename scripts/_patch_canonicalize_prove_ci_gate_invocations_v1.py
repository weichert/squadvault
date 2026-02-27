from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

# Gate invocation line forms (must start at bol; allow leading spaces):
#   ./scripts/gate_foo.sh ...
#   bash scripts/gate_foo.sh ...
GATE_CALL_RE = re.compile(r"^\s*(?:bash\s+)?(?:\./)?scripts/gate_[A-Za-z0-9_]+\.sh\b.*\n?$")

# Banner we treat as "attached" only if it is immediately above a gate call.
BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')


def _key_for_call(call_line: str) -> bytes:
    # Lexicographic byte-order sort (matches the gate’s intent).
    return call_line.encode("utf-8")


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # Identify indices of gate call lines.
    call_idxs: list[int] = [i for i, ln in enumerate(lines) if GATE_CALL_RE.match(ln)]
    if not call_idxs:
        print("ERROR: refused to patch (no gate invocations found).", file=sys.stderr)
        return 3

    # We only want to reorder the *gate invocation section*.
    # We'll take the minimal contiguous region spanning the first..last gate call.
    first = call_idxs[0]
    last = call_idxs[-1]

    # Expand upward to include any banner immediately preceding a gate call at the top edge.
    start = first
    if start - 1 >= 0 and BANNER_RE.match(lines[start - 1]):
        start -= 1

    # Expand downward is unnecessary: banners precede calls, not follow.

    region = lines[start : last + 1]

    # Parse region into (banner?, call) blocks, preserving *only* banners directly above a call.
    blocks: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(region):
        ln = region[i]
        if GATE_CALL_RE.match(ln):
            blocks.append((ln, [ln]))
            i += 1
            continue

        # If banner followed by call, make a paired block.
        if BANNER_RE.match(ln) and i + 1 < len(region) and GATE_CALL_RE.match(region[i + 1]):
            call = region[i + 1]
            blocks.append((call, [ln, call]))
            i += 2
            continue

        # Non-gate line inside region — keep it in-place by refusing to patch.
        # This avoids accidentally reordering unrelated logic.
        # If you later intentionally add non-gate lines into this region, adjust this rule.
        if ln.strip() != "":
            print("ERROR: refused to patch (unexpected non-gate line inside gate region).", file=sys.stderr)
            print(f"Line: {ln.rstrip()}", file=sys.stderr)
            return 4
        # Allow blank lines; keep them but attach to previous block if present.
        if blocks:
            blocks[-1][1].append(ln)  # type: ignore[index]
        else:
            # Leading blank line before first block — keep it as its own pseudo-block.
            blocks.append(("", [ln]))
        i += 1

    # Sort only real blocks (those with a call key); keep leading blank pseudo-block(s) in front.
    prefix: list[list[str]] = []
    sortable: list[tuple[str, list[str]]] = []
    for call, blk in blocks:
        if call == "":
            prefix.append(blk)
        else:
            sortable.append((call, blk))

    sorted_blocks = sorted(sortable, key=lambda t: _key_for_call(t[0]))
    new_region_lines: list[str] = []
    for blk in prefix:
        new_region_lines.extend(blk)
    for _, blk in sorted_blocks:
        new_region_lines.extend(blk)

    new_lines = lines[:start] + new_region_lines + lines[last + 1 :]
    new_src = "".join(new_lines)

    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
