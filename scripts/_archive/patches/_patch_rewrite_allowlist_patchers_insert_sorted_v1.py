from __future__ import annotations

import re
from pathlib import Path

# Offenders reported by the gate
OFFENDERS = [
    Path("scripts/_patch_allowlist_patch_wrapper_add_gate_ops_indices_no_autofill_placeholders_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_bulk_index_ci_guardrails_entrypoints_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_cleanup_ci_guardrails_ops_entrypoint_parity_iterations_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_docs_fill_ci_guardrails_autofill_descriptions_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v4.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.py"),
]

ALLOW_PATH = "scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh"

TEMPLATE = """\
from __future__ import annotations

import re
from pathlib import Path

ALLOW = Path("{allow}")

WRAPPER = "{wrapper}"
MARKER = "{marker}"

def _extract_entries(head_lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(head_lines):
        line = head_lines[i]
        if line.startswith("# SV_ALLOWLIST:"):
            m = line.rstrip("\\n")
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
    entries.append((marker.rstrip("\\n"), wrapper))

    # Sort by wrapper path (stable/deterministic)
    entries_sorted = sorted({{(m, w) for (m, w) in entries}}, key=lambda t: t[1])

    prefix = _prefix_before_first_marker(head_lines)
    out: list[str] = []
    out.extend(prefix)

    if out and not out[-1].endswith("\\n"):
        out[-1] += "\\n"
    if out and out[-1].strip() != "":
        out.append("\\n")

    for m, w in entries_sorted:
        out.append(f"{{m}}\\n")
        out.append(f'  "{{w}}"\\n\\n')

    return "".join(out) + "".join(tail_lines)

def main() -> None:
    if not ALLOW.exists():
        raise SystemExit(f"ERROR: missing {{ALLOW}}")

    text = ALLOW.read_text(encoding="utf-8")
    new_text = _upsert_sorted(text, MARKER, WRAPPER)
    if new_text == text:
        print("OK: wrapper already allowlisted (insert-sorted canonical)")
        return

    ALLOW.write_text(new_text, encoding="utf-8")
    print("UPDATED:", ALLOW)

if __name__ == "__main__":
    main()
"""

def _find_wrapper_and_marker(src: str, path: Path) -> tuple[str, str]:
    # WRAPPER = "..."
    m_wrap = re.search(r'^\s*WRAPPER\s*=\s*"([^"]+)"\s*$', src, flags=re.M)
    if not m_wrap:
        raise SystemExit(f"ERROR: cannot find WRAPPER=... in {path}")
    wrapper = m_wrap.group(1)

    # MARKER = "..."
    m_mark = re.search(r'^\s*MARKER\s*=\s*"([^"]+)"\s*$', src, flags=re.M)
    if not m_mark:
        raise SystemExit(f"ERROR: cannot find MARKER=... in {path}")
    marker = m_mark.group(1)

    return wrapper, marker

def main() -> None:
    updated = 0

    for p in OFFENDERS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing offender file: {p}")

        src = p.read_text(encoding="utf-8")
        wrapper, marker = _find_wrapper_and_marker(src, p)

        new_src = TEMPLATE.format(allow=ALLOW_PATH, wrapper=wrapper, marker=marker)

        # normalize single trailing newline
        if not new_src.endswith("\n"):
            new_src += "\n"

        if src != new_src:
            p.write_text(new_src, encoding="utf-8")
            print("UPDATED:", p)
            updated += 1
        else:
            print("OK:", p, "(already canonical insert-sorted)")

    print("DONE: rewritten allowlist patchers =", updated)

if __name__ == "__main__":
    main()
