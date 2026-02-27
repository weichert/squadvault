from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")

GATE_CALL_RE = re.compile(r"^\s*(?:bash\s+)?(?:\./)?scripts/gate_[A-Za-z0-9_]+\.sh\b.*\n?$")
BANNER_RE = re.compile(r'^\s*echo\s+["\']===\s*Gate:.*===["\']\s*\n?$')

def _key_for_call(call_line: str) -> bytes:
    return call_line.encode("utf-8")

def _is_blank(line: str) -> bool:
    return line.strip() == ""

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # Find first gate call.
    first_call_idx = None
    for i, ln in enumerate(lines):
        if GATE_CALL_RE.match(ln):
            first_call_idx = i
            break
    if first_call_idx is None:
        print("ERROR: refused to patch (no gate invocations found).", file=sys.stderr)
        return 3

    # Expand upward by at most one banner directly above the first call.
    start = first_call_idx
    if start - 1 >= 0 and BANNER_RE.match(lines[start - 1]):
        start -= 1

    # Now find the end of the *gate cluster*:
    # walk forward allowing:
    # - blank lines
    # - banner lines (ONLY if immediately followed by a gate call; otherwise cluster ends before it)
    # - gate call lines
    i = start
    last_in_cluster = start - 1

    while i < len(lines):
        ln = lines[i]

        if _is_blank(ln):
            last_in_cluster = i
            i += 1
            continue

        if GATE_CALL_RE.match(ln):
            last_in_cluster = i
            i += 1
            continue

        if BANNER_RE.match(ln):
            # Only include banners that are directly attached to a following gate call.
            if i + 1 < len(lines) and GATE_CALL_RE.match(lines[i + 1]):
                last_in_cluster = i
                last_in_cluster = i + 1
                i += 2
                continue
            # Banner not followed by gate call => cluster ends.
            break

        # Any other non-blank line => cluster ends.
        break

    if last_in_cluster < start:
        print("ERROR: refused to patch (could not detect a gate cluster to sort).", file=sys.stderr)
        return 4

    region = lines[start : last_in_cluster + 1]

    # Parse region into blocks (banner?, call) and preserve blank lines by attaching to prior block.
    blocks: list[tuple[str, list[str]]] = []
    j = 0
    while j < len(region):
        ln = region[j]

        if _is_blank(ln):
            if blocks:
                blocks[-1][1].append(ln)  # type: ignore[index]
            else:
                blocks.append(("", [ln]))
            j += 1
            continue

        if BANNER_RE.match(ln) and j + 1 < len(region) and GATE_CALL_RE.match(region[j + 1]):
            call = region[j + 1]
            blocks.append((call, [ln, call]))
            j += 2
            continue

        if GATE_CALL_RE.match(ln):
            blocks.append((ln, [ln]))
            j += 1
            continue

        print("ERROR: refused to patch (unexpected line inside gate cluster).", file=sys.stderr)
        print(f"Line: {ln.rstrip()}", file=sys.stderr)
        return 5

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

    new_lines = lines[:start] + new_region + lines[last_in_cluster + 1 :]
    new_src = "".join(new_lines)

    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
