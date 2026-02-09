#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix RC linkage gate discovery glob (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_contract_linkage_general_gate_rc_discovery_fix_v1.py

# hygiene
python -m py_compile scripts/_patch_contract_linkage_general_gate_v1.py

echo "OK"
