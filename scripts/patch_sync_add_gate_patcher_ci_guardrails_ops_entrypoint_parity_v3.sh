#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: sync add-gate patcher to canonical gate using raw string (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.py

echo "==> py_compile patched add-gate patcher"
${PY} -m py_compile scripts/_patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.py

echo "==> smoke: run add-gate wrapper (must no-op cleanly now)"
bash scripts/patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK"
