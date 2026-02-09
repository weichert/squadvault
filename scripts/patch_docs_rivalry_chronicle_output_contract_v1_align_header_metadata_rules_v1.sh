#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: align Rivalry Chronicle output contract doc to new spec (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_docs_rivalry_chronicle_output_contract_v1_align_header_metadata_rules_v1.py"

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash syntax check (wrapper)"
bash -n scripts/patch_docs_rivalry_chronicle_output_contract_v1_align_header_metadata_rules_v1.sh

echo "==> show contract header + metadata window"
sed -n '1,40p' docs/contracts/rivalry_chronicle_output_contract_v1.md

echo "==> verify README indexes exactly once"
grep -n "docs/contracts/rivalry_chronicle_output_contract_v1.md" -n docs/contracts/README.md || true
