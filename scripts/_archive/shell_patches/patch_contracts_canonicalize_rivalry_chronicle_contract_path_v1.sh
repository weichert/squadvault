#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: canonicalize Rivalry Chronicle contract path to match completeness glob (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_contracts_canonicalize_rivalry_chronicle_contract_path_v1.py

echo "==> Confirm canonical contract doc exists"
test -f docs/contracts/rivalry_chronicle_contract_output_v1.md
echo "OK"

echo "==> Confirm old contract doc absent"
test ! -f docs/contracts/rivalry_chronicle_output_contract_v1.md || echo "NOTE: old doc still present (unexpected; investigate)"

echo "==> Spot-check: ensure no OLD path references remain"
if grep -RIn "docs/contracts/rivalry_chronicle_output_contract_v1.md" . >/dev/null 2>&1; then
  echo "ERROR: old contract path still referenced somewhere"
  grep -RIn "docs/contracts/rivalry_chronicle_output_contract_v1.md" . || true
  exit 1
fi
echo "OK"
