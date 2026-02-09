#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: contract linkage gate bash3 compatibility (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_contract_linkage_bash3_compat_v1.py

# hygiene
bash -n scripts/gate_contract_linkage_v1.sh

echo "OK"
