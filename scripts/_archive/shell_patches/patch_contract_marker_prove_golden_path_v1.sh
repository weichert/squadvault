#!/usr/bin/env bash
set -euo pipefail

# Patch: normalize Golden Path contract markers in prove runner (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_contract_marker_prove_golden_path_v1.py"

PY="./scripts/py"
if [[ -x "${PY}" ]]; then
  "${PY}" "${PATCHER}"
else
  "${PYTHON:-python}" "${PATCHER}"
fi
