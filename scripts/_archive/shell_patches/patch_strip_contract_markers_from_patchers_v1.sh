#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: strip SV_CONTRACT markers from specific patchers (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_strip_contract_markers_from_patchers_v1.py

# hygiene
python -m py_compile scripts/_patch_strip_contract_markers_from_patchers_v1.py
python -m py_compile scripts/_patch_contract_linkage_general_gate_v1.py
python -m py_compile scripts/_patch_gate_contract_linkage_bash3_compat_v1.py

echo "OK"
