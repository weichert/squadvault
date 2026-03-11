from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("docs/80_indices/ops/Creative_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_BEGIN -->"
END = "<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_END -->"

# IDs the usage gate expects to see registered (literal tokens in the doc).
REQUIRED_IDS = (
    "CREATIVE_SURFACE_FINGERPRINT_v1",
    "CREATIVE_SURFACE_REGISTRY_V1",
)

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

    missing = [cid for cid in REQUIRED_IDS if not any(cid in ln for ln in lines)]
    if not missing:
        return 0

    # Insert immediately after the canonical fingerprint artifact line if present; else at top.
    insert_at = 0
    for i, ln in enumerate(lines):
        if ANCHOR_SUBSTR in ln:
            insert_at = i + 1
            break

    # Insert as simple bullets (one per line), preserving order in REQUIRED_IDS.
    for cid in missing:
        lines.insert(insert_at, f"- {cid}\n")
        insert_at += 1

    new_mid = "".join(lines)
    new_src = pre + BEGIN + new_mid + END + post

    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
