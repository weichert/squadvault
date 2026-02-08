from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    new_text = """\
from __future__ import annotations

import re
from pathlib import Path

OFFENDERS = [
    Path("scripts/_patch_allowlist_patch_wrapper_add_gate_ops_indices_no_autofill_placeholders_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_bulk_index_ci_guardrails_entrypoints_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_cleanup_ci_guardrails_ops_entrypoint_parity_iterations_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_docs_fill_ci_guardrails_autofill_descriptions_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v4.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.py"),
]

ALLOW_PATH = "scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh"

TEMPLATE = \"\"\"\\
from __future__ import annotations

import re
from pathlib import Path

ALLOW = Path("{allow}")

WRAPPER = "{wrapper}"
MARKER = "{marker}"

def _extract_entries(lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# SV_ALLOWLIST:"):
            m = line.rstrip("\\n")
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            w = None
            if j < len(lines):
                m2 = re.search(r'"([^"]+)"', lines[j])
                if m2:
                    w = m2.group(1)
            if w:
                entries.append((m, w))
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
    entries.append((marker.rstrip("\\n"), wrapper))

    entries_sorted = sorted({{(m, w) for (m, w) in entries}}, key=lambda t: t[1])

    prefix = _prefix_before_first_marker(lines)

    out: list[str] = []
    out.extend(prefix)

    if out and not out[-1].endswith("\\n"):
        out[-1] += "\\n"
    if out and out[-1].strip() != "":
        out.append("\\n")

    for m, w in entries_sorted:
        out.append(f"{m}\\n")
        out.append(f'  "{w}"\\n\\n')

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
\"\"\"

def _find_marker_wrapper(src: str, path: Path) -> tuple[str, str]:
    # Fast path: explicit vars (support a few historical names)
    for var in ("WRAPPER", "PATCH_WRAPPER", "PATCHER_WRAPPER"):
        m_wrap = re.search(rf'^\\s*{var}\\s*=\\s*["\\\']([^"\\\']+)["\\\']\\s*$', src, flags=re.M)
        if m_wrap:
            wrapper = m_wrap.group(1)
            break
    else:
        wrapper = ""

    for var in ("MARKER", "ALLOWLIST_MARKER"):
        m_mark = re.search(rf'^\\s*{var}\\s*=\\s*["\\\']([^"\\\']+)["\\\']\\s*$', src, flags=re.M)
        if m_mark:
            marker = m_mark.group(1)
            break
    else:
        marker = ""

    if wrapper and marker:
        return wrapper, marker

    # Fallback: parse the actual allowlist entry block inside the source:
    #   # SV_ALLOWLIST: ...
    #     "scripts/patch_....sh"
    lines = src.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("# SV_ALLOWLIST:"):
            marker_line = line.rstrip("\\n")
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                m2 = re.search(r'"([^"]+)"', lines[j])
                if m2:
                    wrapper_path = m2.group(1)
                    return wrapper_path, marker_line

    raise SystemExit(f"ERROR: cannot find marker+wrapper in {path}")

def main() -> None:
    updated = 0
    for p in OFFENDERS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing offender file: {p}")

        src = p.read_text(encoding="utf-8")
        wrapper, marker = _find_marker_wrapper(src, p)

        new_src = TEMPLATE.format(allow=ALLOW_PATH, wrapper=wrapper, marker=marker)
        if not new_src.endswith("\\n"):
            new_src += "\\n"

        if src != new_src:
            p.write_text(new_src, encoding="utf-8")
            print("UPDATED:", p)
            updated += 1
        else:
            print("OK:", p, "(already canonical insert-sorted NO-EOF)")

    print("DONE: rewritten allowlist patchers =", updated)

if __name__ == "__main__":
    main()
"""
    if not new_text.endswith("\n"):
        new_text += "\n"

    TARGET.write_text(new_text, encoding="utf-8")
    print("UPDATED:", TARGET)

if __name__ == "__main__":
    main()
