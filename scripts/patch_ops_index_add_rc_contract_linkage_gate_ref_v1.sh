#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops index discoverability for RC contract linkage gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_ops_index_add_rc_contract_linkage_gate_ref_v1.py"

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> verify marker + bullet present"
grep -n "SV_RIVALRY_CHRONICLE_CONTRACT_LINKAGE" -n docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true
grep -n "gate_rivalry_chronicle_contract_linkage_v1.sh" -n docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true
