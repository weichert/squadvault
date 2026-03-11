#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: contract surface completeness gate tmpdir trap is set -u safe (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_contract_surface_completeness_tmpdir_trap_safe_v1.py

echo "==> bash -n gate"
bash -n scripts/gate_contract_surface_completeness_v1.sh

echo "==> smoke: prove_contract_surface_completeness"
bash scripts/prove_contract_surface_completeness_v1.sh

echo "OK"
