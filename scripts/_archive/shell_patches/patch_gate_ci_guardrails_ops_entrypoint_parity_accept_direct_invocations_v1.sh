#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: parity gate accepts direct gate invocations (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_ci_guardrails_ops_entrypoint_parity_accept_direct_invocations_v1.py
chmod +x scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> bash syntax check"
bash -n scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> verify gate now scans for scripts/gate_ via grep -oE"
grep -n "grep -oE 'scripts/gate_" scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK"
