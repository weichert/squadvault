from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("docs/80_indices/ops/Creative_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_BEGIN -->"
END = "<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_END -->"

# This is what the usage gate expects to see registered.
ID = "CREATIVE_SURFACE_FINGERPRINT_v1"

# Insert a simple bullet containing the literal ID.
# Keep it intentionally minimal so it won't fight doc formatting.
ID_LINE = f"- {ID}\n"

# Prefer placing it immediately after the canonical fingerprint artifact line, if present.
ANCHOR_SUBSTR = "artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing doc: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")
    if BEGIN not in src or END not in src:
        print("ERROR: refused to patch (missing bounded block markers).", file=sys.stderr)
        print(f"Missing: {BEGIN} or {END}", file=sys.stderr)
        return 3

    pre, rest = src.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    lines = mid.splitlines(keepends=True)

    # No-op if already registered anywhere in the bounded block.
    if any(ID in ln for ln in lines):
        return 0

    # Find insertion point.
    insert_at = 0
    for i, ln in enumerate(lines):
        if ANCHOR_SUBSTR in ln:
            insert_at = i + 1
            break

    # Avoid inserting into the middle of a paragraph: ensure we insert on a line boundary.
    # Add a newline before if needed (rare).
    if insert_at > 0 and not lines[insert_at - 1].endswith("\n"):
        lines[insert_at - 1] = lines[insert_at - 1] + "\n"

    # Insert ID bullet; if there isn't already a blank line separating sections, we keep it minimal.
    lines.insert(insert_at, ID_LINE)

    new_mid = "".join(lines)
    new_src = pre + BEGIN + new_mid + END + post

    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
