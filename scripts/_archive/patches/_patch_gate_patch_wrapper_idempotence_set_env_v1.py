from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")
MARKER = "# gate_patch_wrapper_idempotence_set_env_v1"

NEEDLE = 'echo "==> wrapper: ${wrapper}"\n  bash "${wrapper}"\n'
REPL = (
    'echo "==> wrapper: ${wrapper}"\n'
    '  SV_IDEMPOTENCE_MODE=1 bash "${wrapper}"\n'
)

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing canonical file: {TARGET}", file=sys.stderr)
        return 2

    original = TARGET.read_text(encoding="utf-8")

    if MARKER in original:
        return 0

    if NEEDLE not in original:
        print("ERROR: expected run_wrapper_once block not found; gate has drifted.", file=sys.stderr)
        return 3

    updated = original.replace(NEEDLE, REPL, 1)

    # Stamp marker right after set -euo pipefail for traceability.
    anchor = "set -euo pipefail\n"
    i = updated.find(anchor)
    if i != -1:
        j = i + len(anchor)
        updated = updated[:j] + "\n" + MARKER + "\n" + updated[j:]

    if updated == original:
        return 0

    TARGET.write_text(updated, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
