from __future__ import annotations

from pathlib import Path
import re
import sys

GATE = Path("scripts/gate_no_untracked_patch_artifacts_v1.sh")

# Grep -E compatible (no non-capturing groups)
WANTED_REGEX = r"^\?\?[[:space:]]+scripts/(_patch_.*\.py|patch_.*\.sh)$"

def main() -> int:
    if not GATE.exists():
        print(f"ERROR: missing {GATE}", file=sys.stderr)
        return 2

    text = GATE.read_text(encoding="utf-8")

    # If already contains the wanted regex, we're done (idempotent)
    if WANTED_REGEX in text:
        return 0

    lines = text.splitlines(True)

    # Target: the line that defines `hits="... grep -E '...scripts/...` (single line)
    # We'll replace ONLY the regex inside grep -E '...'
    pat = re.compile(r"(grep\s+-E\s+')([^']+)(')")

    changed = False
    out = []

    for ln in lines:
        if "hits=" in ln and "grep" in ln and "grep -E" in ln and "scripts/" in ln:
            m = pat.search(ln)
            if m:
                before, _old_regex, after = m.group(1), m.group(2), m.group(3)
                new_ln = pat.sub(lambda mm: f"{before}{WANTED_REGEX}{after}", ln, count=1)
                out.append(new_ln)
                changed = True
                continue
        out.append(ln)

    if not changed:
        print(
            "ERROR: Could not find a suitable hits=...grep -E '...'<regex>' line to patch in gate_no_untracked_patch_artifacts_v1.sh.\n"
            "Refusing to patch.",
            file=sys.stderr,
        )
        return 3

    new_text = "".join(out)
    GATE.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
