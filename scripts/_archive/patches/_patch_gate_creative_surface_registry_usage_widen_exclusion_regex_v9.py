from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

OLD_TOKEN = "CREATIVE_SURFACE_REGISTRY$"
NEW_TOKEN = "(CREATIVE_SURFACE_REGISTRY$|CREATIVE_SURFACE_REGISTRY_ENTRIES$|CREATIVE_SURFACE_REGISTRY_ENTRY$)"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # Idempotence
    if NEW_TOKEN in src:
        print("OK: exclusion regex already widened (noop)")
        return

    # Only patch if the old token exists somewhere.
    if OLD_TOKEN not in src:
        raise SystemExit(
            "ERROR: expected exclusion token not found: " + OLD_TOKEN + "\n"
            "Refusing to patch to avoid corrupting an unexpected file shape."
        )

    # Replace exactly ONE occurrence (the one in the exclusion grep).
    # We target the most likely context: grep -v -E '...CREATIVE_SURFACE_REGISTRY$...'
    # but fall back to a single plain replacement if needed.
    pat = re.compile(r"(grep\s+-v\s+-E\s+['\"][^'\"]*)CREATIVE_SURFACE_REGISTRY\$(.*?['\"])")
    m = pat.search(src)
    if m:
        out = src[:m.start()] + m.group(1) + NEW_TOKEN + m.group(2) + src[m.end():]
        TARGET.write_text(out, encoding="utf-8")
        print("OK: widened exclusion regex within grep -v -E (v9)")
        return

    # Fallback: replace first occurrence of the token.
    out = src.replace(OLD_TOKEN, NEW_TOKEN, 1)
    TARGET.write_text(out, encoding="utf-8")
    print("OK: widened exclusion regex (fallback replace) (v9)")

if __name__ == "__main__":
    main()
