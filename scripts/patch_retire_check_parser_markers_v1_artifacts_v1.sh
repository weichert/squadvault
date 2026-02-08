#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: retire check parser markers v1 artifacts (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_retire_check_parser_markers_v1_artifacts_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
${PY} -m py_compile "${PATCHER}"

echo "==> run patcher"
${PY} "${PATCHER}"

echo "OK"
