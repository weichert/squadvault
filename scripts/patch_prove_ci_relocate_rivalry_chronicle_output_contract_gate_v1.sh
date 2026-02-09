#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: relocate Rivalry Chronicle output contract gate in prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_prove_ci_relocate_rivalry_chronicle_output_contract_gate_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "==> verify anchor + gate markers present"
grep -n "prove_rivalry_chronicle_end_to_end_v1.sh" scripts/prove_ci.sh
grep -n "SV_GATE: rivalry_chronicle_output_contract (v1) begin" -n scripts/prove_ci.sh
echo "OK"
