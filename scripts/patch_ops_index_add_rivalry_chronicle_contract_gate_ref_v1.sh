#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops index add Rivalry Chronicle output contract gate ref (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_ops_index_add_rivalry_chronicle_contract_gate_ref_v1.py
echo "OK"
