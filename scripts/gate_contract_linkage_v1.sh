#!/usr/bin/env bash
# SV_CONTRACT_NAME: CONTRACT_MARKERS
# SV_CONTRACT_DOC_PATH: docs/contracts/Contract_Markers_v1.0.md

set -euo pipefail

# Contract Linkage Gate (v1)
# Policy: docs/contracts/Contract_Markers_v1.0.md
# Enforces that any script declaring a contract declares BOTH markers in comment form:
#   # Example marker fields (do not copy verbatim tokens):
#   #   SV_CONTRACT_NAME = <name>
#   #   SV_CONTRACT_DOC_PATH = <repo-relative path>
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

  # Comment-only marker matching to avoid false positives from string literals.
  line="$(grep -n -m1 -E "^[[:space:]]*#[[:space:]]*${key}:[[:space:]]*" "${file}" || true)"
  if [[ -z "${line}" ]]; then
    return 0
  fi

  # Strip grep -n prefix "N:" then strip the marker key.
  echo "${line#*:}" | sed -E "s/^[[:space:]]*#[[:space:]]*${key}:[[:space:]]*//"
}

bad=0

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
