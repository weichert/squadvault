from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py")

def _escape_braces_in_append_calls(text: str) -> tuple[str, int]:
    """
    Convert f"...{m}..." -> f"...{{m}}..."
            f'..."{w}"...' -> f'..."{{w}}"...'
    Only within out.append(f"...") / out.append(f'...') contexts.
    """
    changed = 0

    # Escape {m} inside out.append(f"...") lines
    def repl_m(match: re.Match) -> str:
        nonlocal changed
        s = match.group(0)
        if "{{m}}" in s:
            return s
        changed += 1
        return s.replace("{m}", "{{m}}")

    # Escape {w} inside out.append(f'...') lines (or double-quote variants)
    def repl_w(match: re.Match) -> str:
        nonlocal changed
        s = match.group(0)
        if "{{w}}" in s:
            return s
        changed += 1
        return s.replace("{w}", "{{w}}")

    # Operate on append calls only (keeps scope tight).
    text2 = re.sub(r'^[ \t]*out\.append\(f"[^"\n]*\{m\}[^"\n]*"\)[ \t]*$', repl_m, text, flags=re.M)
    text3 = re.sub(r"^[ \t]*out\.append\(f'[^'\n]*\{m\}[^'\n]*'\)[ \t]*$", repl_m, text2, flags=re.M)

    text4 = re.sub(r'^[ \t]*out\.append\(f"[^"\n]*\{w\}[^"\n]*"\)[ \t]*$', repl_w, text3, flags=re.M)
    text5 = re.sub(r"^[ \t]*out\.append\(f'[^'\n]*\{w\}[^'\n]*'\)[ \t]*$", repl_w, text4, flags=re.M)

    return text5, changed

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    # If there are no {m}/{w} at all, show helpful context and refuse.
    if "{m}" not in text and "{w}" not in text:
        raise SystemExit("ERROR: no '{m}' or '{w}' found in target; refuse ambiguous state")

    new_text, changed = _escape_braces_in_append_calls(text)

    # If append-scope matching missed because formatting differs, do a safe fallback:
    # escape any f"...{m}..." or f'...{m}...' and any f"...{w}..." within TEMPLATE body.
    if changed == 0:
        # Only within the TEMPLATE triple-quoted string to avoid touching real code.
        m = re.search(r'TEMPLATE\s*=\s*"""\s*\\\n(.*?)\n"""', text, flags=re.S)
        if not m:
            raise SystemExit("ERROR: cannot locate TEMPLATE triple-quote block; refuse ambiguous state")

        tmpl = m.group(1)
        tmpl2 = tmpl.replace("{m}", "{{m}}").replace("{w}", "{{w}}")
        if tmpl2 == tmpl:
            raise SystemExit("ERROR: found '{m}'/'{w}' but no changes applied; refuse ambiguous state")

        new_text = text[: m.start(1)] + tmpl2 + text[m.end(1) :]
        changed = 1

    if new_text == text:
        print("OK: TEMPLATE braces already escaped")
        return

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"UPDATED: {TARGET} (changes_applied={changed})")

if __name__ == "__main__":
    main()
