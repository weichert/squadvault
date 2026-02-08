from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py")

def _extract_template_block(text: str) -> tuple[int, int, str]:
    m = re.search(r'TEMPLATE\s*=\s*"""\s*\\\n(.*?)\n"""', text, flags=re.S)
    if not m:
        raise SystemExit("ERROR: cannot locate TEMPLATE triple-quote block; refuse ambiguous state")
    return m.start(1), m.end(1), m.group(1)

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    a, b, tmpl = _extract_template_block(text)

    before = tmpl

    # Replace literal newline inside quotes:  " <newline> "  -> "\\n"
    # (this is what creates unterminated string literals in generated offender patchers)
    tmpl = tmpl.replace("\"\n\"", "\"\\\\n\"")
    tmpl = tmpl.replace("'\n'", "'\\\\n'")

    # Also handle common cases where indentation crept in:
    tmpl = re.sub(r"\"[ \t]*\n[ \t]*\"", "\"\\\\n\"", tmpl)
    tmpl = re.sub(r"'[ \t]*\n[ \t]*'", "'\\\\n'", tmpl)

    if tmpl == before:
        print("OK: no literal newline-in-quotes found inside TEMPLATE (already fixed?)")
        return

    new_text = text[:a] + tmpl + text[b:]
    TARGET.write_text(new_text, encoding="utf-8")
    print("UPDATED:", TARGET)

if __name__ == "__main__":
    main()
