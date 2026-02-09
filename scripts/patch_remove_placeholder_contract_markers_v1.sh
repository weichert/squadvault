#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove placeholder SV_CONTRACT markers (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_remove_placeholder_contract_markers_v1.py

# hygiene
python -m py_compile scripts/_patch_remove_placeholder_contract_markers_v1.py
python -m py_compile scripts/_patch_contract_linkage_general_gate_v1.py
python -m py_compile scripts/_patch_gate_contract_linkage_bash3_compat_v1.py
bash -n scripts/gate_contract_linkage_v1.sh

echo "OK"
