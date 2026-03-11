from __future__ import annotations

from pathlib import Path
import sys

ALLOWLIST = Path("scripts/patch_idempotence_allowlist_v1.txt")

OLD = "scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh"
NEW = "scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh"

MARKER = "# patch_idempotence_allowlist_use_v2_v1"


def main() -> int:
    if not ALLOWLIST.exists():
        print(f"ERROR: missing canonical file: {ALLOWLIST}", file=sys.stderr)
        return 2

    original = ALLOWLIST.read_text(encoding="utf-8")

    if MARKER in original and NEW in original:
        return 0

    updated = original

    if OLD in updated:
        updated = updated.replace(OLD, NEW)
    elif NEW not in updated:
        # If neither is present, append NEW at end.
        if not updated.endswith("\n"):
            updated += "\n"
        updated += NEW + "\n"

    # Stamp marker once near top for traceability.
    if MARKER not in updated:
        updated = updated.rstrip("\n") + "\n" + MARKER + "\n"

    # Normalize: end with newline.
    if not updated.endswith("\n"):
        updated += "\n"

    if updated == original:
        return 0

    ALLOWLIST.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
