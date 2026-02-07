#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: micro-tidy proof surface gate path wrapper grep (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_micro_tidy_fix_proof_surface_gate_path_wrapper_grep_v1.py

echo "==> bash -n (wrapper)"
bash -n scripts/patch_fix_ci_proof_surface_registry_gate_path_v1.sh

echo "==> run wrapper (should be idempotent / no surprises)"
bash scripts/patch_fix_ci_proof_surface_registry_gate_path_v1.sh >/dev/null

echo "OK"
