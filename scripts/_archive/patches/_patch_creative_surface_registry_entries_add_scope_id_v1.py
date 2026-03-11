from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("docs/80_indices/ops/Creative_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_BEGIN -->"
END   = "<!-- SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_END -->"

NEEDED = [
    "CREATIVE_SURFACE_REGISTRY_V1",
    "CREATIVE_SURFACE_SCOPE_V1",
]

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing doc: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")
    if BEGIN not in src or END not in src:
        print("ERROR: refused to patch (missing ENTRIES bounded block).", file=sys.stderr)
        print(f"Need both:\n  {BEGIN}\n  {END}", file=sys.stderr)
        return 3

    pre, rest = src.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    existing: list[str] = []
    kept_mid_lines: list[str] = []
    for ln in mid.splitlines():
        stripped = ln.strip()
        if stripped.startswith("- "):
            existing.append(stripped[2:].strip())
        kept_mid_lines.append(ln)

    merged = sorted(set(existing).union(NEEDED))

    # Rebuild the ENTRIES block content:
    # keep a single header line if present; otherwise just bullets.
    header_lines: list[str] = []
    for ln in kept_mid_lines:
        s = ln.strip()
        if s.startswith("## "):
            header_lines = [ln.rstrip("\n")]
            break

    new_mid_lines: list[str] = [""]  # leading newline after BEGIN
    if header_lines:
        new_mid_lines.append(header_lines[0])
        new_mid_lines.append("")
    for cid in merged:
        new_mid_lines.append(f"- {cid}")
    new_mid_lines.append("")  # blank line before END

    new_mid = "\n".join(new_mid_lines) + "\n"

    new_src = pre + BEGIN + new_mid + END + post
    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
