#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist bulk-index wrapper for idempotence gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_allowlist_patch_wrapper_bulk_index_ci_guardrails_entrypoints_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "==> verify wrapper present"
grep -nF 'scripts/patch_bulk_index_missing_ci_guardrails_entrypoints_from_prove_ci_v1.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
