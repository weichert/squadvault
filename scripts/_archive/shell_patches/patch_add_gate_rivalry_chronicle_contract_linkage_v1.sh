#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Rivalry Chronicle contract linkage gate + wire into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_add_gate_rivalry_chronicle_contract_linkage_v1.py"

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> ensure gate executable"
chmod +x scripts/gate_rivalry_chronicle_contract_linkage_v1.sh

echo "==> bash syntax check"
bash -n scripts/gate_rivalry_chronicle_contract_linkage_v1.sh
bash -n scripts/prove_ci.sh

echo "==> show prove_ci window"
grep -n "rivalry_chronicle_contract_linkage" -n -C 3 scripts/prove_ci.sh || true
