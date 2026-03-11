#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist sync-add-gate-patcher wrapper (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_allowlist_patch_wrapper_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.py

echo "==> bash syntax check"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "==> verify wrapper present"
grep -nF 'scripts/patch_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
