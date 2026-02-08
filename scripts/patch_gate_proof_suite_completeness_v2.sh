#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire proof suite completeness gate via SV_ANCHOR docs_gates (v1) (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_proof_suite_completeness_v2.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/gate_proof_suite_completeness_v1.sh

echo "==> verify marker present exactly once"
grep -n 'SV_GATE: proof_suite_completeness (v1)' scripts/prove_ci.sh
test "$(grep -c 'SV_GATE: proof_suite_completeness (v1) begin' scripts/prove_ci.sh)" -eq 1
test "$(grep -c 'SV_GATE: proof_suite_completeness (v1) end' scripts/prove_ci.sh)" -eq 1

echo "OK"
