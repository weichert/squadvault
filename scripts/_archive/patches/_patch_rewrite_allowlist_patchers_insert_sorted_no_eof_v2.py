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

ALLOWLIST_PATH = "scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh"

def _extract_wrapper_marker(src: str, p: Path) -> tuple[str, str]:
    """
    Extract (wrapper_path, marker_line) from an existing allowlist patcher.

    Preferred: explicit WRAPPER/MARKER vars.
    Fallback: parse:
      # SV_ALLOWLIST: ...
        "scripts/patch_....sh"
    """
    m_wrap = re.search(r'^\s*WRAPPER\s*=\s*["\']([^"\']+)["\']\s*$', src, flags=re.M)
    m_mark = re.search(r'^\s*MARKER\s*=\s*["\']([^"\']+)["\']\s*$', src, flags=re.M)
    if m_wrap and m_mark:
        return m_wrap.group(1), m_mark.group(1)

    lines = src.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# SV_ALLOWLIST:"):
            marker = line.strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                m2 = re.search(r'"([^"]+)"', lines[j])
                if m2:
                    return m2.group(1), marker

    raise SystemExit(f"ERROR: cannot find WRAPPER+MARKER (or SV_ALLOWLIST block) in {p}")

# IMPORTANT:
# - We DO NOT use str.format() here (because TEMPLATE contains many { } braces that are real Python).
# - We use sentinel tokens and replace them.
TEMPLATE = """\
from __future__ import annotations

import re
from pathlib import Path

ALLOW = Path("__ALLOWLIST_PATH__")

WRAPPER = "__WRAPPER_PATH__"
MARKER = "__MARKER_LINE__"

def _extract_entries(lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# SV_ALLOWLIST:"):
            marker_line = line.rstrip("\\n")
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
    entries.append((marker.rstrip("\\n"), wrapper))

    # Sort by wrapper path (deterministic), de-dupe
    entries_sorted = sorted({(m, w) for (m, w) in entries}, key=lambda t: t[1])

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
"""

def _render_template(allowlist_path: str, wrapper: str, marker: str) -> str:
    # Keep this extremely explicit and safe.
    out = TEMPLATE
    out = out.replace("__ALLOWLIST_PATH__", allowlist_path)
    out = out.replace("__WRAPPER_PATH__", wrapper)
    out = out.replace("__MARKER_LINE__", marker)
    if "__ALLOWLIST_PATH__" in out or "__WRAPPER_PATH__" in out or "__MARKER_LINE__" in out:
        raise SystemExit("ERROR: template substitution incomplete; refuse ambiguous state")
    return out

def main() -> None:
    updated = 0
    for p in OFFENDERS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing offender file: {p}")

        src = p.read_text(encoding="utf-8")
        wrapper, marker = _extract_wrapper_marker(src, p)

        new_src = _render_template(ALLOWLIST_PATH, wrapper, marker)
        if not new_src.endswith("\n"):
            new_src += "\n"

        if src != new_src:
            p.write_text(new_src, encoding="utf-8")
            print("UPDATED:", p)
            updated += 1
        else:
            print("OK:", p, "(already canonical insert-sorted NO-EOF)")

    print("DONE: rewritten allowlist patchers =", updated)

if __name__ == "__main__":
    main()
