from __future__ import annotations

import re
from pathlib import Path

ALLOW = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")

WRAPPER = "scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v4.sh"
MARKER = "# SV_ALLOWLIST: ci_guardrails_ops_entrypoint_parity_awk_fix (v4)"

def _extract_entries(head_lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(head_lines):
        line = head_lines[i]
        if line.startswith("# SV_ALLOWLIST:"):
            m = line.rstrip("\n")
            # wrapper line expected next (skipping blanks)
            j = i + 1
            while j < len(head_lines) and head_lines[j].strip() == "":
                j += 1
            w = None
            if j < len(head_lines):
                m2 = re.search(r'"([^"]+)"', head_lines[j])
                if m2:
                    w = m2.group(1)
            if w:
                entries.append((m, w))
                # consume wrapper + trailing blanks
                k = j + 1
                while k < len(head_lines) and head_lines[k].strip() == "":
                    k += 1
                i = k
                continue
        i += 1
    return entries

def _prefix_before_first_marker(head_lines: list[str]) -> list[str]:
    prefix: list[str] = []
    for line in head_lines:
        if line.startswith("# SV_ALLOWLIST:"):
            break
        prefix.append(line)
    return prefix

def _split_head_tail(text: str) -> tuple[list[str], list[str]]:
    # Preserve EOF + anything after it as tail (so we don't disturb the here-doc close).
    if "EOF" in text:
        idx = text.rfind("EOF")
        head_text = text[:idx]
        tail_text = text[idx:]
        return head_text.splitlines(True), tail_text.splitlines(True)
    return text.splitlines(True), []

def _upsert_sorted(text: str, marker: str, wrapper: str) -> str:
    # If marker exists, wrapper must also exist (refuse ambiguity).
    if marker in text:
        if wrapper in text:
            return text
        raise SystemExit("ERROR: marker exists but wrapper missing; refuse ambiguous state")

    head_lines, tail_lines = _split_head_tail(text)

    entries = _extract_entries(head_lines)
    entries.append((marker.rstrip("\n"), wrapper))

    # Sort by wrapper path (stable/deterministic)
    entries_sorted = sorted({(m, w) for (m, w) in entries}, key=lambda t: t[1])

    prefix = _prefix_before_first_marker(head_lines)
    out: list[str] = []
    out.extend(prefix)

    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    if out and out[-1].strip() != "":
        out.append("\n")

    for m, w in entries_sorted:
        out.append(f"{m}\n")
        out.append(f'  "{w}"\n\n')

    return "".join(out) + "".join(tail_lines)

def main() -> None:
    if not ALLOW.exists():
        raise SystemExit(f"ERROR: missing {ALLOW}")

    text = ALLOW.read_text(encoding="utf-8")
    new_text = _upsert_sorted(text, MARKER, WRAPPER)
    if new_text == text:
        print("OK: wrapper already allowlisted (insert-sorted canonical)")
        return

    ALLOW.write_text(new_text, encoding="utf-8")
    print("UPDATED:", ALLOW)

if __name__ == "__main__":
    main()
