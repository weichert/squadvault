#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_golden_path wire output contract gate (v1, autovar) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_prove_golden_path_wire_output_contract_gate_v1_autovar.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh
echo "OK"
