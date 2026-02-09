from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

NEEDLE = '# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.'
SENTINEL = "REQUIRED_SECTION_HEADINGS_V10"
NEWLINES_ANCHOR = "new_lines = lines[:meta_start] + meta + lines[meta_end:]"

# Remove the entire previously inserted block (including surrounding blank lines).
REMOVE_RE = re.compile(
    r"""
    ^[ \t]*#\s*---\s*REQUIRED_SECTION_HEADINGS_V10\s*---\s*\n
    (?:.*\n)*?
    ^[ \t]*\n
    """,
    re.MULTILINE | re.VERBOSE,
)

INSERT_BLOCK = """\
# --- REQUIRED_SECTION_HEADINGS_V10 ---
required = [
    "## Matchup Summary",
    "## Key Moments",
    "## Stats & Nuggets",
    "## Closing",
]
present = {ln.strip() for ln in new_lines}
missing = [h for h in required if h not in present]
if missing:
    # Append a minimal scaffold for any missing headings (keep existing content intact).
    # Ensure at least one blank line before the scaffold.
    if new_lines and new_lines[-1].strip() != "":
        new_lines.append("")
    for h in missing:
        new_lines.append(h)
        new_lines.append("")
"""

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    if NEEDLE not in txt0:
        raise SystemExit("Refusing: expected contract block marker not found; cannot apply v11 safely.")

    if NEWLINES_ANCHOR not in txt0:
        raise SystemExit("Refusing: expected new_lines anchor not found; cannot apply v11 safely.")

    # 1) Remove any existing v10 block (idempotent if absent)
    txt1 = txt0
    if SENTINEL in txt1:
        txt1, n = REMOVE_RE.subn("", txt1, count=1)
        if n != 1:
            # If sentinel present but regex didn't match cleanly, refuse to avoid mangling.
            raise SystemExit(f"Refusing: expected to remove exactly 1 v10 block, removed {n}.")
    else:
        n = 0

    # 2) Insert v10 block after new_lines assignment, if not already there
    if SENTINEL in txt1:
        # If still present, something is wrong (should have been removed above)
        raise SystemExit("Refusing: v10 sentinel still present after attempted removal.")

    lines = txt1.splitlines(True)
    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and NEWLINES_ANCHOR in ln:
            out.append(INSERT_BLOCK + "\n\n")
            inserted = True

    if not inserted:
        raise SystemExit("Refusing: failed to insert v10 block after new_lines anchor.")

    txt2 = "".join(out)
    if txt2 != txt0:
        PROVE.write_text(txt2, encoding="utf-8")

if __name__ == "__main__":
    main()
