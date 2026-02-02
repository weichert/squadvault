#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON="${PYTHON:-python}"
export PYTHONPATH="${PYTHONPATH:-${REPO_ROOT}/src}"

exec "${PYTHON}" "${REPO_ROOT}/scripts/_smoke_persist_rivalry_chronicle_v1.py" "$@"
