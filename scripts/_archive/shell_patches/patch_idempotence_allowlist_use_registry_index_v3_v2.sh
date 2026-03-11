#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: idempotence allowlist uses registry index v3 (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_idempotence_allowlist_use_registry_index_v3_v2.py"
ALLOW="scripts/patch_idempotence_allowlist_v1.txt"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> grep confirm"
grep -nF 'scripts/patch_index_ci_proof_surface_registry_discoverability_v3.sh' "${ALLOW}"

echo "OK"
