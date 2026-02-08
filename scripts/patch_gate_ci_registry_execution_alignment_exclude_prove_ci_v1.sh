#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: exclude prove_ci from registry→execution alignment gate sets (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_ci_registry_execution_alignment_exclude_prove_ci_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_ci_registry_execution_alignment_v1.sh
echo "OK"
