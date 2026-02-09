#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops refs add Golden Path Output Contract (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_ops_refs_add_output_contract_v1.py

echo "OK"
