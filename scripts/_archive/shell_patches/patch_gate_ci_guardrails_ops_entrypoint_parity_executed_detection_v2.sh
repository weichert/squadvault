#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: parity gate executed detection includes direct invocations (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_ci_guardrails_ops_entrypoint_parity_executed_detection_v2.py

chmod +x scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> bash syntax check"
bash -n scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> verify patch marker present"
grep -n "SV_PATCH: executed gate detection accepts direct invocations (v2)" scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK"
