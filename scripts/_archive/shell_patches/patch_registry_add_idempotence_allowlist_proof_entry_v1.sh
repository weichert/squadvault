#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: registry add idempotence allowlist proof entry (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_registry_add_idempotence_allowlist_proof_entry_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
${PY} -m py_compile "${PATCHER}"

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> cheap local verification: run proof surface registry gate"
bash scripts/check_ci_proof_surface_matches_registry_v1.sh

echo "OK"
