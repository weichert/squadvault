from __future__ import annotations

from pathlib import Path
import re

DOC = Path("docs/80_indices/ops/Creative_Surface_Registry_v1.0.md")

# We require explicit bounded markers to avoid corrupting an unexpected doc shape.
BEGIN_RE = re.compile(r"^<!--\s*SV_CREATIVE_SURFACE_REGISTRY_ENTRIES.*BEGIN\s*-->\s*$", re.MULTILINE)
END_RE   = re.compile(r"^<!--\s*SV_CREATIVE_SURFACE_REGISTRY_ENTRIES.*END\s*-->\s*$", re.MULTILINE)

NEEDED_ID = "CREATIVE_SURFACE_REGISTRY_V1_EN"

def _extract_block(src: str) -> tuple[int, int, str]:
    m1 = BEGIN_RE.search(src)
    m2 = END_RE.search(src)
    if not m1 or not m2 or m2.start() < m1.end():
        raise SystemExit(
            "ERROR: Could not find bounded Entries block markers in registry doc.\n"
            "Refusing to patch to avoid corrupting an unexpected file shape."
        )
    return m1.end(), m2.start(), src[m1.end():m2.start()]

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing doc: {DOC}")

    src = DOC.read_text(encoding="utf-8")

    lo, hi, block = _extract_block(src)

    # Collect bullet IDs of the form: - SOME_ID
    lines = block.splitlines()
    bullet_re = re.compile(r"^\s*-\s+([A-Z0-9_]+)\s*$")

    ids: list[str] = []
    kept: list[str] = []

    for ln in lines:
        m = bullet_re.match(ln)
        if m:
            ids.append(m.group(1))
        else:
            kept.append(ln)

    if NEEDED_ID in ids:
        print("OK: registry already contains needed ID (noop)")
        return

    ids.append(NEEDED_ID)
    ids = sorted(set(ids))

    # Rebuild: preserve any non-bullet lines in the block (typically blank lines / comments),
    # then emit a canonical bullet list (one per line).
    rebuilt_lines: list[str] = []
    # Keep leading non-bullet content exactly as-is (most docs have none, but be safe)
    # We keep only lines that are not pure bullet lines.
    rebuilt_lines.extend(kept)
    # Ensure there is at least one blank line between kept content and bullets when needed.
    if rebuilt_lines and rebuilt_lines[-1].strip() != "":
        rebuilt_lines.append("")
    # Emit bullets
    rebuilt_lines.extend([f"- {i}" for i in ids])
    rebuilt = "\n".join(rebuilt_lines).rstrip() + "\n"

    out = src[:lo] + rebuilt + src[hi:]
    DOC.write_text(out, encoding="utf-8")
    print(f"OK: added {NEEDED_ID} to Creative Surface Registry entries (v5)")

if __name__ == "__main__":
    main()
