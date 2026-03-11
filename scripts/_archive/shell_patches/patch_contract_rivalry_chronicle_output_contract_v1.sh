#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: add Rivalry Chronicle output contract doc (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_contract_rivalry_chronicle_output_contract_v1.py
echo "OK"
