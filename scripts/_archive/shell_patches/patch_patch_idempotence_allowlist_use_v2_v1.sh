#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: idempotence allowlist -> index discoverability v2 (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_patch_idempotence_allowlist_use_v2_v1.py"
ALLOWLIST="scripts/patch_idempotence_allowlist_v1.txt"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n wrapper"
bash -n "scripts/patch_patch_idempotence_allowlist_use_v2_v1.sh"

echo "==> grep: allowlist contains v2"
grep -nF 'scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh' "${ALLOWLIST}"

echo "==> prove_ci (expected DIRTY pre-commit)"
bash scripts/prove_ci.sh || true

echo "OK"
