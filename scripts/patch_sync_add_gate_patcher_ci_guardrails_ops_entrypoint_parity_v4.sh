#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: sync add-gate patcher canonical parity gate text (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v4.py

echo "==> py_compile"
"${PY}" -m py_compile scripts/_patch_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v4.py
"${PY}" -m py_compile scripts/_patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.py

echo "==> smoke: add-gate wrapper must no longer refuse"
bash scripts/patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK"
