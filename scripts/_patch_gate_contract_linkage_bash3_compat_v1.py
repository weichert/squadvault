from __future__ import annotations

from pathlib import Path
import sys

GATE = Path("scripts/gate_contract_linkage_v1.sh")

BEGIN = "# Contract Linkage Gate (v1)"
NEEDLE = "mapfile -t FILES < <(find"

REPLACEMENT = """#!/usr/bin/env bash
set -euo pipefail

# Contract Linkage Gate (v1)
# Enforces that any script claiming a contract includes:
#
# Scope: scripts/*.{sh,py}
#
# Bash3-safe (macOS): avoid mapfile/readarray.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

fail() { echo "FAIL: $*" >&2; exit 1; }

TARGET_DIR="scripts"

extract_marker() {
  local file="$1"
  local key="$2"
  local line
  line="$(grep -n -m1 -E "${key}:[[:space:]]*" "${file}" || true)"
  if [[ -z "${line}" ]]; then
    return 0
  fi
  echo "${line#*:}" | sed -E "s/^.*${key}:[[:space:]]*//"
}

bad=0

# Bash3-safe iteration over find output (sorted deterministically)
while IFS= read -r f; do
  name="$(extract_marker "${f}" "SV_CONTRACT_NAME")"
  doc="$(extract_marker "${f}" "SV_CONTRACT_DOC_PATH")"

  if [[ -n "${name}" || -n "${doc}" ]]; then
    if [[ -z "${name}" ]]; then
      echo "ERR: ${f} declares SV_CONTRACT_DOC_PATH but is missing SV_CONTRACT_NAME" >&2
      bad=1
      continue
    fi
    if [[ -z "${doc}" ]]; then
      echo "ERR: ${f} declares SV_CONTRACT_NAME (${name}) but is missing SV_CONTRACT_DOC_PATH" >&2
      bad=1
      continue
    fi
    if [[ "${doc}" == /* ]]; then
      echo "ERR: ${f} contract doc path must be repo-relative, got: ${doc}" >&2
      bad=1
      continue
    fi
    if [[ ! -f "${doc}" ]]; then
      echo "ERR: ${f} contract doc does not exist: ${doc}" >&2
      bad=1
      continue
    fi
  fi
done < <(find "${TARGET_DIR}" -type f \( -name "*.sh" -o -name "*.py" \) -print | LC_ALL=C sort)

if [[ "${bad}" -ne 0 ]]; then
  fail "contract linkage violations found"
fi

exit 0
"""

def main() -> int:
    if not GATE.exists():
        print(f"ERR: missing gate: {GATE}", file=sys.stderr)
        return 2

    txt = GATE.read_text(encoding="utf-8")

    # Idempotence: if it's already bash3-safe, no-op.
    if NEEDLE not in txt and "Bash3-safe" in txt:
        return 0

    # Safety: ensure we’re patching the right file family.
    if BEGIN not in txt:
        print("ERR: unexpected gate contents (missing expected header); refusing to overwrite.", file=sys.stderr)
        return 2

    # Replace whole file with canonical bash3-safe v1 content.
    GATE.write_text(REPLACEMENT, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
