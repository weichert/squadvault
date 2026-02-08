#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist new patch wrappers for idempotence gate (ci_guardrails_ops_entrypoint_parity v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_allowlist_patch_wrappers_for_ci_guardrails_ops_entrypoint_parity_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "==> verify wrappers present"
grep -nF 'scripts/patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh
grep -nF 'scripts/patch_wire_ci_guardrails_ops_entrypoint_parity_gate_into_prove_ci_v1.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh
grep -nF 'scripts/patch_index_ci_guardrails_ops_entrypoint_parity_gate_discoverability_v1.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
