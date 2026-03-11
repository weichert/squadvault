#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: relocate Rivalry Chronicle output contract gate after full continued invocation (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_prove_ci_relocate_rivalry_chronicle_output_contract_gate_v3.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "==> show window around rivalry chronicle prove invocation"
line="$(grep -n "prove_rivalry_chronicle_end_to_end_v1.sh" scripts/prove_ci.sh | head -n1 | cut -d: -f1)"
start=$((line-2))
end=$((line+25))
if [[ "${start}" -lt 1 ]]; then start=1; fi
sed -n "${start},${end}p" scripts/prove_ci.sh

echo "==> verify gate marker exists"
grep -n "SV_GATE: rivalry_chronicle_output_contract (v1) begin" scripts/prove_ci.sh

echo "OK"
