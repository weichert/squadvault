#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wrapper skips prove_ci when SV_IDEMPOTENCE_MODE=1 (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_wrapper_skip_prove_ci_in_idempotence_mode_v1.py"
WRAPPER="scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n wrapper"
bash -n "${WRAPPER}"
bash -n "scripts/patch_wrapper_skip_prove_ci_in_idempotence_mode_v1.sh"

echo "==> grep: wrapper checks SV_IDEMPOTENCE_MODE"
grep -nF 'SV_IDEMPOTENCE_MODE' "${WRAPPER}"

echo "OK"
