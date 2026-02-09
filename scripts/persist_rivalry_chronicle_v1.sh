#!/usr/bin/env bash
# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON="${PYTHON:-python}"
export PYTHONPATH="${PYTHONPATH:-${REPO_ROOT}/src}"

exec "${PYTHON}" "${REPO_ROOT}/scripts/_smoke_persist_rivalry_chronicle_v1.py" "$@"
