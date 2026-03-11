from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOW = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")

def insert_sorted_block(text: str, marker: str, wrapper: str) -> str:
    if marker in text:
        if wrapper in text:
            return text
        raise SystemExit("ERROR: marker exists but wrapper missing; refuse ambiguous state")

    # Find th   lock that contains quoted wrapper lines. We’ll insert the new marker+wrapper
    # before EOF, but in sorted order by wrapper path among existing wrapper entries.
    #
    # Strategy:
    #   - parse all existing allowlist entries (marker lines + wrapper line)
    #   - add the new entry
    #   - re-emit as a stable sorted set by wrapper path
    #
    # NOTE: This helper is conservative and expects wrapper lines look like:   "scripts/patch_...sh"
    lines = text.splitlines(True)
    head: list[str] = []
    tail: list[str] = []

    # Split around EOF if present (keep EOF and trailer in tail)
    if "EOF" in text:
        idx = text.rfind("EOF")
        head_text = text[:idx]
        tail_text = text[idx:]
        head = head_text.splitlines(True)
        tail = tail_text.splitlines(True)
    else:
        head = lines
        tail = []

    # Extract entries from head
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(head):
        line = head[i]
        if line.startswith("# SV_ALLOWLIST:"):
            m = line.rstrip("\n")
            # Expect wrapper line soon after
            j = i + 1
            w = None
            while j < len(head) and head[j].strip() == "":
                j += 1
            if j < len(head):
                m2 = re.search(r'"([^"]+)"', head[j])
                if m2:
                    w = m2.group(1)
            if w:
                entries.append((m, w))
                # consume through wrapper line + any trailing blank lines
                k = j + 1
                while k < len(head) and head[k].strip() == "":
                    k += 1
                # remove consumed lines by skipping them
                # We rebuild from scratch later, so just advance:
                i = k
                continue
        i += 1

    # Add new entry
    entries.append((marker.rstrip("\n"), wrapper))

    # Sort by wrapper path (stable, deterministic)
    entries_sorted = sorted({(m, w) for (m, w) in entries}, key=lambda t: t[1])

    # Rebuild allowlist body: keep everything up to the first SV_ALLOWLIST marker untouched.
    # Find first marker line in original head, keep prefix.
    prefix: list[str] = []
    found = False
    for line in head:
        if line.startswith("# SV_ALLOWLIST:"):
            found = True
            break
        prefix.append(line)
    if not found:
        # If no markers found, just treat entire head as prefix and append entries.
        prefix = head

    out: list[str] = []
    out.extend(prefix)
    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    if out and out[-1].strip() != "":
        out.append("\n")

    for m, w in entries_sorted:
        out.append(f"{m}\n")
        out.append(f'  "{w}"\n\n')

    return "".join(out) + "".join(tail)

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: _helper_rewrite_allowlist_patcher_insert_sorted_v1.py <marker> <wrapper_path>")

    marker = sys.argv[1]
    wrapper = sys.argv[2]

    text = ALLOW.read_text(encoding="utf-8")
    new_text = insert_sorted_block(text, marker, wrapper)
    if new_text == text:
        print("OK: allowlist already contains entry (no changes)")
        return
    ALLOW.write_text(new_text, encoding="utf-8")
    print("UPDATED:", ALLOW)

if __name__ == "__main__":
    main()
