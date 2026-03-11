from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

GOOD_LINE = r'txt = "\n".join(lines).rstrip() + "\n"'

# Match the broken multiline join/append:
#   txt = "
#   ".join(lines).rstrip() + "
#   "
#
# PLUS (optional) the glued next token, e.g.
#   "out_path.write_text(...)
#
# We capture an immediately-following out_path.write_text so we can force a newline.
BROKEN_BLOCK_RE = re.compile(
    r'''
    txt\s*=\s*"          # txt = "
    \s*\r?\n\s*"         # <newline> "
    \.join\(lines\)      # .join(lines)
    \.rstrip\(\)         # .rstrip()
    \s*\+\s*"            # + "
    \s*\r?\n\s*"         # <newline> "
    \s*                  # optional whitespace
    (out_path\.write_text) ? # optional glued call start
    ''',
    re.VERBOSE | re.MULTILINE,
)

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    m = BROKEN_BLOCK_RE.search(txt0)
    if not m:
        # If no broken form exists, ensure we didn't leave it half-broken.
        if GOOD_LINE in txt0:
            return
        raise SystemExit(
            "Refusing: did not find known-bad multiline join block, and canonical join line not found."
        )

    # Replace only the first occurrence (should be exactly one in this script).
    def repl(match: re.Match) -> str:
        glued = match.group(1)
        if glued:
            # out_path.write_text was glued to the closing quote; reinsert newline.
            return GOOD_LINE + "\n" + glued
        return GOOD_LINE

    txt1, n = BROKEN_BLOCK_RE.subn(repl, txt0, count=1)
    if n != 1:
        raise SystemExit(f"Refusing: expected exactly 1 replacement, got {n}.")

    PROVE.write_text(txt1, encoding="utf-8")

if __name__ == "__main__":
    main()
