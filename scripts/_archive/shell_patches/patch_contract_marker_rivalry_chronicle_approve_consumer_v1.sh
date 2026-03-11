#!/usr/bin/env bash
set -euo pipefail

# Patch: add Rivalry Chronicle contract markers to approve consumer (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_contract_marker_rivalry_chronicle_approve_consumer_v1.py"

PY="./scripts/py"
if [[ -x "${PY}" ]]; then
  "${PY}" "${PATCHER}"
else
  "${PYTHON:-python}" "${PATCHER}"
fi
