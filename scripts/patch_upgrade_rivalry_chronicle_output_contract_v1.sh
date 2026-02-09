#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: upgrade Rivalry Chronicle output contract (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_upgrade_rivalry_chronicle_output_contract_v1.py

echo "==> Confirm file exists"
test -f docs/contracts/rivalry_chronicle_output_contract_v1.md
echo "OK"
