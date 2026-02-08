#!/usr/bin/env bash
# SquadVault — proof: allowlist wrappers no-op under SV_IDEMPOTENCE_MODE=1 (v1)
#
# Proves:
#   - Every wrapper listed in scripts/patch_idempotence_allowlist_v1.txt produces no repo mutations
#     when invoked with SV_IDEMPOTENCE_MODE=1 from a clean tree.
#
# Constraints:
#   - repo-root anchored
#   - bash3-safe
#   - deterministic
#   - idempotent (does not mutate repo)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

require_clean() {
  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "ERROR: repo must be clean: ${1}"
    git status --porcelain=v1
    exit 2
  fi
}

require_file() {
  if [[ ! -f "${1}" ]]; then
    echo "ERROR: missing required file: ${1}"
    exit 2
  fi
}

echo "==> Proof: allowlisted patch wrappers are no-op under SV_IDEMPOTENCE_MODE=1 (v1)"

require_file "scripts/patch_idempotence_allowlist_v1.txt"
require_clean "entry"

count=0
while IFS= read -r raw; do
  line="${raw}"
  line="$(echo "${line}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  if [[ -z "${line}" ]]; then
    continue
  fi
  if [[ "${line}" == \#* ]]; then
    continue
  fi

  if [[ ! -f "${line}" ]]; then
    echo "ERROR: allowlist wrapper not found: ${line}"
    exit 2
  fi
  if [[ ! -x "${line}" ]]; then
    echo "ERROR: allowlist wrapper not executable: ${line}"
    exit 2
  fi

  count=$((count + 1))
  echo "==> [${count}] ${line}"
  SV_IDEMPOTENCE_MODE=1 bash "${line}"

  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "ERROR: wrapper mutated repo under SV_IDEMPOTENCE_MODE=1: ${line}"
    echo "==> git status --porcelain=v1"
    git status --porcelain=v1
    echo "==> git diff --name-only"
    git diff --name-only || true
    exit 2
  fi
done < "scripts/patch_idempotence_allowlist_v1.txt"

echo "==> wrappers checked: ${count}"
require_clean "exit"
echo "OK"
