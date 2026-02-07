from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh")
MARKER = "# wrapper_skip_prove_ci_in_idempotence_mode_v1"

NEEDLE = 'echo "==> prove_ci (expected DIRTY pre-commit)"\n' \
         'bash scripts/prove_ci.sh || true\n\n'

REPL = (
    'if [[ "${SV_IDEMPOTENCE_MODE:-0}" != "1" ]]; then\n'
    '  echo "==> prove_ci (expected DIRTY pre-commit)"\n'
    '  bash scripts/prove_ci.sh || true\n'
    'else\n'
    '  echo "==> prove_ci skipped (SV_IDEMPOTENCE_MODE=1)"\n'
    'fi\n\n'
)

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing canonical file: {TARGET}", file=sys.stderr)
        return 2

    original = TARGET.read_text(encoding="utf-8")

    if MARKER in original:
        return 0

    if NEEDLE not in original:
        print("ERROR: expected prove_ci block not found; wrapper has drifted.", file=sys.stderr)
        return 3

    updated = original.replace(NEEDLE, REPL, 1)

    # Stamp marker after set -euo pipefail.
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
