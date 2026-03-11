from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

# Remove the previously injected (broken) bash block if present.
BAD_BEGIN = "# --- Canonicalize Rivalry Chronicle export header for contract (v1) ---"
BAD_END = "# --- /Canonicalize Rivalry Chronicle export header for contract (v1) ---"

# We will replace the single write_text line in the export Python snippet with a canonicalizer+write.
WRITE_RE = re.compile(r"^out_path\.write_text\(txt,\s*encoding=['\"]utf-8['\"]\)\s*$", re.M)

REPLACEMENT = """\
# Enforce Rivalry Chronicle output contract header (v1): first line must be exact.
hdr = "# Rivalry Chronicle (v1)"
lines = str(txt).splitlines()

# Drop leading blank lines
while lines and lines[0].strip() == "":
    lines.pop(0)

if not lines:
    lines = [hdr]
else:
    if lines[0] != hdr:
        # Preserve whatever was first as body content.
        lines = [hdr, ""] + lines

txt = "\\n".join(lines).rstrip() + "\\n"
out_path.write_text(txt, encoding="utf-8")
"""

def strip_bad_block(s: str) -> str:
    if BAD_BEGIN not in s:
        return s
    # remove from BAD_BEGIN line through BAD_END line (inclusive)
    pattern = re.compile(
        re.escape(BAD_BEGIN) + r".*?" + re.escape(BAD_END) + r"\n?",
        re.S,
    )
    return pattern.sub("", s)

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    txt1 = strip_bad_block(txt0)

    # Replace the write_text line exactly once.
    if not WRITE_RE.search(txt1):
        raise SystemExit("Refusing: could not find expected out_path.write_text(txt, encoding='utf-8') line to replace.")

    txt2, n = WRITE_RE.subn(REPLACEMENT, txt1, count=1)
    if n != 1:
        raise SystemExit(f"Refusing: expected to replace exactly 1 write_text line, replaced {n}.")

    if txt2 != txt0:
        PROVE.write_text(txt2, encoding="utf-8")

if __name__ == "__main__":
    main()
