from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_add_docs_integrity_gate_v1.py")
MARK = "docs_integrity_scope_canonical_only_v3"

def die(msg: str) -> None:
    raise SystemExit(msg)

HELPER = f"""
# {MARK}: post-process generated checker so header enforcement applies only to docs/canonical/**
def _sv_postprocess_docs_integrity_checker_scope() -> None:
    import re
    from pathlib import Path

    checker = Path("scripts/check_docs_integrity_v1.py")
    if not checker.exists():
        return

    src = checker.read_text(encoding="utf-8")

    # already patched?
    if "{MARK}" in src:
        return

    m = re.search(r"(?m)^def gate_header_presence\\(\\s*files:\\s*List\\[Path\\]\\s*\\)\\s*->\\s*None:\\s*\\n", src)
    if not m:
        return

    m_for = re.search(r"(?m)^[ \\t]+for p in files:\\s*\\n", src[m.end():])
    if not m_for:
        return

    for_line_abs = m.end() + m_for.start()
    for_line = src[for_line_abs : for_line_abs + (m_for.end() - m_for.start())]

    m_indent = re.match(r"^([ \\t]+)for p in files:", for_line)
    if not m_indent:
        return

    body_indent = m_indent.group(1) + (" " * 4)
    injection = (
        f"{{body_indent}}# {MARK}: header enforcement only applies to docs/canonical/**\\n"
        f"{{body_indent}}rp = rel(p)\\n"
        f"{{body_indent}}if not rp.startswith('docs/canonical/'):\\n"
        f"{{body_indent}}    continue\\n"
    )

    window = src[for_line_abs : for_line_abs + 600]
    if "if not rp.startswith('docs/canonical/'):" in window:
        return

    out = src[: (for_line_abs + len(for_line))] + injection + src[(for_line_abs + len(for_line)) :]
    checker.write_text(out, encoding="utf-8", newline="\\n")
"""

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if MARK in s:
        print(f"NO-OP: already patched ({MARK})")
        return

    # 1) Insert helper near top (after imports is fine)
    # Prefer: after the last import block near the top.
    m_imports_end = None
    for m in re.finditer(r"(?m)^(from|import) .*\n", s):
        m_imports_end = m.end()

    insert_pos = m_imports_end if m_imports_end is not None else 0
    s2 = s[:insert_pos] + HELPER + s[insert_pos:]

    # 2) Insert call near end of main(): find the LAST print(...) and inject before it
    # We only want to patch main(), not some helper.
    m_main = re.search(r"(?m)^def main\(\)\s*->\s*None:\s*\n", s2)
    if not m_main:
        die("FAIL: could not find def main() in _patch_add_docs_integrity_gate_v1.py")

    # Search from main() start forward for all 4-space-indented print(...) lines
    tail = s2[m_main.end():]
    prints = list(re.finditer(r"(?m)^(?P<indent>[ \t]+)print\(", tail))
    if not prints:
        die("FAIL: could not find any print(...) inside main(); cannot anchor safe injection point")

    last_print = prints[-1]
    indent = last_print.group("indent")
    call = f"{indent}_sv_postprocess_docs_integrity_checker_scope()  # {MARK}\n"

    # Insert call right before the last print line
    abs_insert = m_main.end() + last_print.start()
    s3 = s2[:abs_insert] + call + s2[abs_insert:]

    TARGET.write_text(s3, encoding="utf-8", newline="\n")
    print(f"OK: patched {TARGET} to postprocess checker scope at end of main() (v3)")

if __name__ == "__main__":
    main()
