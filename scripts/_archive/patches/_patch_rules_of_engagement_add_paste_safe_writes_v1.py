from __future__ import annotations

from pathlib import Path

DOC = Path("docs/process/rules_of_engagement.md")

BEGIN = "<!-- SV_PASTE_SAFE_FILE_WRITES_v1_BEGIN -->"
END   = "<!-- SV_PASTE_SAFE_FILE_WRITES_v1_END -->"

BLOCK = f"""{BEGIN}
## Paste-Safe File Writes

When creating or modifying scripts, patchers, wrappers, or structured docs,
you **must** use paste-safe writes.

Canonical tool:
- `scripts/clipwrite.sh` (wraps `scripts/clipwrite.py`)

Reference:
- `docs/process/Paste_Safe_File_Writes_v1.0.md`

{END}
"""

def main() -> int:
    if not DOC.exists():
        raise SystemExit(f"FAIL: missing {DOC}")

    s = DOC.read_text(encoding="utf-8")

    if BEGIN in s:
        print("OK: rules_of_engagement already references Paste-Safe File Writes.")
        return 0

    # Insert near top, after title
    lines = s.splitlines()
    out = []
    inserted = False

    for i, line in enumerate(lines):
        out.append(line)
        if not inserted and i < 5 and line.startswith("#"):
            out.append("")
            out.append(BLOCK.rstrip())
            out.append("")
            inserted = True

    if not inserted:
        out.append("")
        out.append(BLOCK.rstrip())

    DOC.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("OK: indexed Paste-Safe File Writes in rules_of_engagement.md (v1)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
