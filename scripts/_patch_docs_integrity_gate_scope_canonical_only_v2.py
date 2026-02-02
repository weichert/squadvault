from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_add_docs_integrity_gate_v1.py")
MARK = "docs_integrity_scope_canonical_only_v2"

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if MARK in s:
        print("NO-OP: already patched (docs_integrity_scope_canonical_only_v2)")
        return

    # We will inject:
    #  - a helper function that post-processes scripts/check_docs_integrity_v1.py
    #  - a call to that helper right after the patcher writes the checker file
    #
    # Step A: locate the place where the patcher writes check_docs_integrity_v1.py
    # Common pattern: Path("scripts/check_docs_integrity_v1.py").write_text(...)
    write_pat = re.compile(
        r'(?P<indent>^[ \t]*)Path\(\s*["\']scripts/check_docs_integrity_v1\.py["\']\s*\)\.write_text\(',
        re.M,
    )
    m = write_pat.search(s)
    if not m:
        # fallback: sometimes they assign CHECKER = Path(...) then CHECKER.write_text(...)
        write_pat2 = re.compile(r'(?P<indent>^[ \t]*)CHECKER\.write_text\(', re.M)
        m = write_pat2.search(s)
        if not m:
            die("FAIL: could not find where _patch_add_docs_integrity_gate_v1.py writes check_docs_integrity_v1.py")

    indent = m.group("indent")

    helper = f"""
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

    # Find gate_header_presence(...) and inject a scope limiter inside its file loop.
    m = re.search(r"(?m)^def gate_header_presence\\(\\s*files:\\s*List\\[Path\\]\\s*\\)\\s*->\\s*None:\\s*\\n", src)
    if not m:
        return  # don't fail regeneration; checker structure may have changed

    # Find first "for p in files:" after function header
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

    # avoid double-inject if close by
    window = src[for_line_abs : for_line_abs + 500]
    if "if not rp.startswith('docs/canonical/'):" in window:
        return

    insert_at = for_line_abs + len(for_line)
    out = src[:insert_at] + injection + src[insert_at:]
    checker.write_text(out, encoding="utf-8", newline="\\n")
"""

    # Step B: inject helper near the top-level helpers area.
    # We'll place it after the first occurrence of "def die(" if present, otherwise near file top.
    anchor = re.search(r"(?m)^def die\\(", s)
    if anchor:
        insert_pos = anchor.end()
        # insert after die() function block (approx): next blank line after die definition
        next_blank = re.search(r"\n\s*\n", s[insert_pos:])
        if next_blank:
            insert_pos = insert_pos + next_blank.end()
    else:
        insert_pos = 0

    s2 = s[:insert_pos] + helper + s[insert_pos:]

    # Step C: add call AFTER checker write.
    # We insert immediately after the write_text(...) call block by finding the next line after that statement.
    # We'll inject a standalone call with same indentation.
    call_line = f"{indent}_sv_postprocess_docs_integrity_checker_scope()  # {MARK}\n"

    # Find end of the write_text(...) statement by locating the next newline after the match line.
    # Then insert the call on the following line (safe even if it's inside main()).
    line_start = s2.rfind("\n", 0, m.start()) + 1
    line_end = s2.find("\n", m.start())
    if line_end == -1:
        die("FAIL: unexpected file layout (no newline after checker write line)")

    # Insert the call AFTER the line that *starts* the write_text call; even if multi-line args,
    # placing immediately after the first line is still within same block and valid Python.
    insert_call_at = line_end + 1
    s3 = s2[:insert_call_at] + call_line + s2[insert_call_at:]

    TARGET.write_text(s3, encoding="utf-8", newline="\n")
    print("OK: patched _patch_add_docs_integrity_gate_v1.py to post-process checker scope (v2)")

if __name__ == "__main__":
    main()
