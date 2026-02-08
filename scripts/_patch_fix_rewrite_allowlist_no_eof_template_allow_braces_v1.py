from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py")

def _extract_template_block(text: str) -> tuple[int, int, str]:
    """
    Extract the body of the TEMPLATE triple-quoted string.

    We match: TEMPLATE = \"\"\"\\\n ... \n\"\"\"
    and return (start_idx, end_idx, body).
    """
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

    # Primary fix: inner f-string uses {ALLOW} but outer .format() would treat it as a placeholder.
    tmpl = tmpl.replace("{ALLOW}", "{{ALLOW}}")

    # Defensive escapes for other accidental .format() placeholders inside TEMPLATE.
    # DO NOT touch {allow}/{wrapper}/{marker} — those are intended outer .format() inputs.
    for token in ("{path}", "{p}", "{ALLOW_PATH}", "{TARGET}", "{OFFENDERS}"):
        tmpl = tmpl.replace(token, token.replace("{", "{{").replace("}", "}}"))

    if tmpl == before:
        if "{ALLOW}" in text:
            raise SystemExit("ERROR: '{ALLOW}' exists but not inside TEMPLATE body match; refuse ambiguous state")
        print("OK: no {ALLOW} found to escape (already fixed?)")
        return

    new_text = text[:a] + tmpl + text[b:]
    TARGET.write_text(new_text, encoding="utf-8")
    print("UPDATED:", TARGET)

if __name__ == "__main__":
    main()
