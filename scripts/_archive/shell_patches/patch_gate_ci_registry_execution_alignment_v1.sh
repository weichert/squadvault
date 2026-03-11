#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire CI registry → execution alignment gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_ci_registry_execution_alignment_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/gate_ci_registry_execution_alignment_v1.sh
echo "OK"

echo "==> run gate standalone"
bash scripts/gate_ci_registry_execution_alignment_v1.sh
echo "OK"
