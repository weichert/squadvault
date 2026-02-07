from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh")

OLD = """MARKER='<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->'
BULLET='- scripts/check_ci_proof_surface_matches_registry_v1.sh — CI Proof Surface Registry Gate (canonical)'
"""

NEW = """MARKER='<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->'
# NOTE: avoid Unicode dash matching issues in macOS grep; match the stable ASCII path instead.
BULLET_PATH='scripts/check_ci_proof_surface_matches_registry_v1.sh'
"""

OLD_COUNTS = """marker_count="$(grep -nF "${MARKER}" "${INDEX}" | wc -l | tr -d ' ')"
bullet_count="$(grep -nF "${BULLET}" "${INDEX}" | wc -l | tr -d ' ')"
"""

NEW_COUNTS = """marker_count="$(LC_ALL=C grep -nF -- "${MARKER}" "${INDEX}" | wc -l | tr -d ' ')"
bullet_count="$(LC_ALL=C grep -nF -- "${BULLET_PATH}" "${INDEX}" | wc -l | tr -d ' ')"
"""

OLD_ERR = """if [[ "${bullet_count}" != "1" ]]; then
  echo "ERROR: expected exactly 1 bullet in ${INDEX}, found ${bullet_count}" >&2
  echo "HINT: run: bash scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh" >&2
  exit 1
fi
"""

NEW_ERR = """if [[ "${bullet_count}" != "1" ]]; then
  echo "ERROR: expected exactly 1 registry gate path in ${INDEX}, found ${bullet_count}" >&2
  echo "HINT: run: bash scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh" >&2
  exit 1
fi
"""

MARKER = "# gate_ci_proof_surface_registry_index_discoverability_grep_fix_v1"


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing canonical file: {TARGET}", file=sys.stderr)
        return 2

    original = TARGET.read_text(encoding="utf-8")

    if MARKER in original:
        return 0

    updated = original

    if OLD not in updated:
        print("ERROR: expected header block not found; gate has drifted.", file=sys.stderr)
        return 3
    updated = updated.replace(OLD, NEW, 1)

    if OLD_COUNTS not in updated:
        print("ERROR: expected grep count block not found; gate has drifted.", file=sys.stderr)
        return 4
    updated = updated.replace(OLD_COUNTS, NEW_COUNTS, 1)

    if OLD_ERR not in updated:
        print("ERROR: expected bullet error block not found; gate has drifted.", file=sys.stderr)
        return 5
    updated = updated.replace(OLD_ERR, NEW_ERR, 1)

    # Stamp marker near top (after set -euo pipefail) for traceability.
    needle = "set -euo pipefail\n"
    idx = updated.find(needle)
    if idx != -1:
        insert_at = idx + len(needle)
        updated = updated[:insert_at] + "\n" + MARKER + "\n" + updated[insert_at:]

    if updated == original:
        return 0

    TARGET.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
