#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Contract Markers Policy doc + index it (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_docs_add_contract_markers_policy_v1.py

# hygiene
python -m py_compile scripts/_patch_docs_add_contract_markers_policy_v1.py

# quick sanity checks
test -f docs/contracts/Contract_Markers_v1.0.md
test -f docs/contracts/README.md
grep -n "Contract_Markers_v1.0.md" docs/contracts/README.md >/dev/null

echo "OK"
