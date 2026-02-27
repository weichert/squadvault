from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

FILTER_BLOCK = r"""# Filter out internal non-surface tokens that can be accidentally picked up by reference scans.
# (e.g., *_ENTRIES_* / *_ENTRY_* identifiers used for registry extraction plumbing)
referenced_ids_raw="$(printf '%s\n' "${referenced_ids_raw}" | grep -vE '^(CREATIVE_SURFACE_REGISTRY_ENTRIES|CREATIVE_SURFACE_REGISTRY_ENTRY)')"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # Idempotence
    if "grep -vE '^(CREATIVE_SURFACE_REGISTRY_ENTRIES|CREATIVE_SURFACE_REGISTRY_ENTRY)'" in src:
        print("OK: filter already present (noop)")
        return

    # We insert immediately after the first assignment to referenced_ids_raw=...
    pat = re.compile(r'^(?P<indent>\s*)referenced_ids_raw=.*\n', re.MULTILINE)
    m = pat.search(src)
    if not m:
        raise SystemExit(
            "ERROR: could not find referenced_ids_raw assignment in gate.\n"
            "Refusing to patch to avoid corrupting an unexpected file shape."
        )

    insert_at = m.end()
    out = src[:insert_at] + "\n" + FILTER_BLOCK + "\n" + src[insert_at:]
    TARGET.write_text(out, encoding="utf-8")
    print("OK: added referenced_ids_raw filter for ENTRIES/ENTRY tokens (v5)")

if __name__ == "__main__":
    main()
