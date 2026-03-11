#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add new wrappers to patch idempotence allowlist (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile scripts/_patch_add_wrappers_to_patch_idempotence_allowlist_v1.py

echo "==> run patcher"
"${PY}" scripts/_patch_add_wrappers_to_patch_idempotence_allowlist_v1.py

echo "==> verify allowlist canonical"
bash scripts/gate_patch_idempotence_allowlist_canonical_v1.sh

echo "OK"
