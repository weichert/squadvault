#!/usr/bin/env bash
set -euo pipefail

# Patch: remove SV_CONTRACT_DOC_PATH marker from run_golden_path_v1.sh (non-enforcement surface) (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_remove_run_golden_path_contract_doc_marker_v1.py"

PY="./scripts/py"
if [[ -x "${PY}" ]]; then
  "${PY}" "${PATCHER}"
else
  "${PYTHON:-python}" "${PATCHER}"
fi
