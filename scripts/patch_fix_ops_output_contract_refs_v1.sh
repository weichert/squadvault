#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: fix ops refs for Golden Path Output Contract (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_fix_ops_output_contract_refs_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_fix_ops_output_contract_refs_v1.sh
echo "OK"
