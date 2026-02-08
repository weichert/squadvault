#!/usr/bin/env bash
set -euo pipefail

echo "==> Gate: proof suite completeness (v1)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

REGISTRY_DOC="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
test -f "${REGISTRY_DOC}"

FS_LIST="$(mktemp)"
REG_LIST="$(mktemp)"
trap 'rm -f "${FS_LIST}" "${REG_LIST}"' EXIT

# Filesystem truth
git ls-files 'scripts/prove_*.sh' | sort -u > "${FS_LIST}"

# Registry truth (explicit paths referenced in the registry doc)
grep -oE 'scripts/prove_[A-Za-z0-9_]+\.sh' "${REGISTRY_DOC}" | sort -u > "${REG_LIST}"

if [[ ! -s "${FS_LIST}" ]]; then
  echo "ERROR: No scripts/prove_*.sh found in repo (unexpected)."
  exit 1
fi

if [[ ! -s "${REG_LIST}" ]]; then
  echo "ERROR: Registry contains no scripts/prove_*.sh references (unexpected)."
  echo "Registry doc: ${REGISTRY_DOC}"
  exit 1
fi

# Strong invariant: exact match
if ! diff -u "${FS_LIST}" "${REG_LIST}" >/dev/null 2>&1; then
  echo "ERROR: Proof suite completeness violation."
  echo "  Registry doc: ${REGISTRY_DOC}"
  echo
  echo "--- Filesystem proofs (scripts/prove_*.sh)"
  sed 's/^/  /' "${FS_LIST}"
  echo
  echo "--- Registry proofs (extracted from registry doc)"
  sed 's/^/  /' "${REG_LIST}"
  echo
  echo "--- Diff (filesystem vs registry)"
  diff -u "${FS_LIST}" "${REG_LIST}" || true
  exit 1
fi

echo "OK: proof runners match registry exactly."
