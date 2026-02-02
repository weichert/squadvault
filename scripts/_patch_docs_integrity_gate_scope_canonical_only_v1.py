from __future__ import annotations

import re
from pathlib import Path

CHECKER = Path("scripts/check_docs_integrity_v1.py")
PATCHER = Path("scripts/_patch_add_docs_integrity_gate_v1.py")

MARK = "docs_integrity_scope_canonical_only_v1"

def die(msg: str) -> None:
    raise SystemExit(msg)

def patch_gate_header_presence(src: str, target_label: str) -> str:
    """
    Inject a scope limiter into gate_header_presence(...) so header enforcement applies only to docs/canonical/**.
    We keep this intentionally minimal: just a repo-relative prefix check before reading files.
    """

    if MARK in src:
        return src

    # Find the gate_header_presence function block
    m = re.search(r"(?m)^def gate_header_presence\(\s*files:\s*List\[Path\]\s*\)\s*->\s*None:\s*\n", src)
    if not m:
        die(f"FAIL: could not locate gate_header_presence() in {target_label}")

    # Find the first "for p in files:" line after function start
    func_start = m.start()
    m_for = re.search(r"(?m)^[ \t]+for p in files:\s*\n", src[m.end():])
    if not m_for:
        die(f"FAIL: could not find 'for p in files:' inside gate_header_presence() in {target_label}")

    for_line_abs = m.end() + m_for.start()

    # Determine indentation level of the for-loop body
    # We'll inject immediately after the for-line, at +4 spaces relative to "for" indent.
    for_line = src[for_line_abs: for_line_abs + (m_for.end() - m_for.start())]
    for_indent = re.match(r"^([ \t]+)for p in files:", for_line)
    if not for_indent:
        die(f"FAIL: could not parse indentation for for-loop in {target_label}")
    indent = for_indent.group(1) + (" " * 4)

    injection = (
        f"{indent}# {MARK}: header enforcement only applies to docs/canonical/**\n"
        f"{indent}rp = rel(p)\n"
        f"{indent}if not rp.startswith('docs/canonical/'):\n"
        f"{indent}    continue\n"
    )

    # Ensure we don't inject twice by checking for rel(p) usage right after loop
    window = src[for_line_abs: for_line_abs + 400]
    if "if not rp.startswith('docs/canonical/'):" in window:
        return src  # already effectively patched

    # Insert immediately after the for-line
    insert_at = for_line_abs + len(for_line)
    return src[:insert_at] + injection + src[insert_at:]

def main() -> None:
    # Patch runtime checker
    s = CHECKER.read_text(encoding="utf-8")
    s2 = patch_gate_header_presence(s, str(CHECKER))
    if s2 != s:
        CHECKER.write_text(s2, encoding="utf-8", newline="\n")
        print("OK: patched checker header scope to docs/canonical only")
    else:
        print("NO-OP: checker already patched (or could not be safely modified)")

    # Patch template inside the docs integrity gate patcher so future regen keeps the same rule.
    p = PATCHER.read_text(encoding="utf-8")
    p2 = patch_gate_header_presence(p, str(PATCHER))
    if p2 != p:
        PATCHER.write_text(p2, encoding="utf-8", newline="\n")
        print("OK: patched patcher-template header scope to docs/canonical only")
    else:
        print("NO-OP: patcher-template already patched (or could not be safely modified)")

if __name__ == "__main__":
    main()
