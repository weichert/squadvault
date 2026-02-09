from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

# Fix the mangled literal-newline-in-quotes form:
#   txt = "\n".join(...)    <-- desired source
# became:
#   txt = "
#   ".join(...).rstrip() + "
#   "
#
# We repair ONLY the join/append line, leaving the rest of the contract block intact.

# Match the entire bad join+append line even if the newline appears literally inside the quotes.
BAD_JOIN_LINE_RE = re.compile(
    r'^txt\s*=\s*"\s*\n\s*"\.join\(lines\)\.rstrip\(\)\s*\+\s*"\s*\n\s*"\s*$',
    re.M,
)

GOOD_JOIN_LINE = r'txt = "\n".join(lines).rstrip() + "\n"'

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    # If already canonical, no-op.
    if GOOD_JOIN_LINE in txt0 and not BAD_JOIN_LINE_RE.search(txt0):
        return

    txt1, n = BAD_JOIN_LINE_RE.subn(GOOD_JOIN_LINE, txt0)

    # If we didn't hit the "bad" form, we still want to ensure the good line exists
    # (but we refuse to do fuzzy edits beyond the known-bad corruption).
    if n == 0:
        if GOOD_JOIN_LINE in txt0:
            return
        raise SystemExit(
            "Refusing: did not find the known-bad newline corruption pattern, "
            "and the canonical join line is not present. Manual inspection needed."
        )

    PROVE.write_text(txt1, encoding="utf-8")

if __name__ == "__main__":
    main()
