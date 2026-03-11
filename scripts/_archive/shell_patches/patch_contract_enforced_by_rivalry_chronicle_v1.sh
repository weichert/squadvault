#!/usr/bin/env bash
set -euo pipefail

# Patch: add/validate Enforced By section for Rivalry Chronicle contract (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_contract_enforced_by_rivalry_chronicle_v1.py"

PY="./scripts/py"
if [[ -x "${PY}" ]]; then
  "${PY}" "${PATCHER}"
else
  "${PYTHON:-python}" "${PATCHER}"
fi
