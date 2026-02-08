#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: harden CI proof surface registry parser with markers (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_check_ci_proof_surface_parser_markers_v3.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
${PY} -m py_compile "${PATCHER}"

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> bash -n check script"
bash -n scripts/check_ci_proof_surface_matches_registry_v1.sh

echo "==> cheap local verification: run check script"
bash scripts/check_ci_proof_surface_matches_registry_v1.sh

echo "OK"
