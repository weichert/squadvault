from __future__ import annotations

import re
from pathlib import Path

ALLOW = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")

WRAPPER = "scripts/patch_add_gate_ops_indices_no_autofill_placeholders_v1.sh"
MARKER = "# SV_ALLOWLIST: add_gate_ops_indices_no_autofill_placeholders (v1)"

def _extract_entries(lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# SV_ALLOWLIST:"):
            marker_line = line.rstrip("\n")
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            wrapper_path = None
            if j < len(lines):
                m2 = re.search(r'"([^"]+)"', lines[j])
                if m2:
                    wrapper_path = m2.group(1)
            if wrapper_path:
                entries.append((marker_line, wrapper_path))
                k = j + 1
                while k < len(lines) and lines[k].strip() == "":
                    k += 1
                i = k
                continue
        i += 1
    return entries

def _prefix_before_first_marker(lines: list[str]) -> list[str]:
    prefix: list[str] = []
    for line in lines:
        if line.startswith("# SV_ALLOWLIST:"):
            break
        prefix.append(line)
    return prefix

def _upsert_sorted(text: str, marker: str, wrapper: str) -> str:
    if marker in text:
        if wrapper in text:
            return text
        raise SystemExit("ERROR: marker exists but wrapper missing; refuse ambiguous state")

    lines = text.splitlines(True)

    entries = _extract_entries(lines)
    entries.append((marker.rstrip("\n"), wrapper))

    # Sort by wrapper path (deterministic), de-dupe
    entries_sorted = sorted({(m, w) for (m, w) in entries}, key=lambda t: t[1])

    prefix = _prefix_before_first_marker(lines)

    out: list[str] = []
    out.extend(prefix)

    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    if out and out[-1].strip() != "":
        out.append("\n")

    for m, w in entries_sorted:
        out.append(f"{m}\n")
        out.append(f'  "{w}"\n\n')

    return "".join(out)

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
