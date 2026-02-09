#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add contract surface completeness gate + proof (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash -n "${BASH_SOURCE[0]}"

PATCHER="scripts/_patch_gate_contract_surface_completeness_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" "${PATCHER}"

chmod +x scripts/gate_contract_surface_completeness_v1.sh
chmod +x scripts/prove_contract_surface_completeness_v1.sh

bash -n scripts/gate_contract_surface_completeness_v1.sh
bash -n scripts/prove_contract_surface_completeness_v1.sh

echo "OK"
