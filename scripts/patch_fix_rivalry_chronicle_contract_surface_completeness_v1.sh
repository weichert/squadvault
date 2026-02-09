#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix Rivalry Chronicle contract surface completeness (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_fix_rivalry_chronicle_contract_surface_completeness_v1.py

echo "==> Spot-check Enforced By section"
grep -n "^## Enforced By" -n docs/contracts/rivalry_chronicle_contract_output_v1.md
awk 'BEGIN{p=0} /^## Enforced By/{p=1; next} /^## /{p=0} {if(p) print}' docs/contracts/rivalry_chronicle_contract_output_v1.md

echo "OK"
