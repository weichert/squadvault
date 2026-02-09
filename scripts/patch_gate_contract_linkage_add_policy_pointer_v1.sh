#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Contract Markers Policy pointer to contract linkage gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_contract_linkage_add_policy_pointer_v1.py

# hygiene
python -m py_compile scripts/_patch_gate_contract_linkage_add_policy_pointer_v1.py
bash -n scripts/gate_contract_linkage_v1.sh

# quick sanity
grep -n -F "# Policy: docs/contracts/Contract_Markers_v1.0.md" scripts/gate_contract_linkage_v1.sh >/dev/null

echo "OK"
