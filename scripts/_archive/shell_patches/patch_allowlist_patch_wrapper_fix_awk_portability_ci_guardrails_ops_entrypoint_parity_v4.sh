#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist awk portability fix wrapper (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v4.py

echo "==> bash syntax check"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "==> verify wrapper present"
grep -nF 'scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v4.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
