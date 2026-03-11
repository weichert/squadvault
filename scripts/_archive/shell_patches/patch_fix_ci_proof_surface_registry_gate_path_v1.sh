#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix CI proof surface registry gate path (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_ci_proof_surface_registry_gate_path_v1.py

echo "==> bash -n (touched shell scripts)"
bash -n scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh
bash -n scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh
bash -n scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh

echo "==> grep: ensure old reference is gone (excluding __pycache__)"
grep -nR --exclude-dir='__pycache__' \
  --exclude='patch_fix_ci_proof_surface_registry_gate_path_v1.sh' \
  --exclude='_patch_fix_ci_proof_surface_registry_gate_path_v1.py' \
  "gate_ci_proof_surface_registry_v1.sh" docs scripts | head -n 50 || true

echo "==> grep: ensure new reference present"
grep -nR --exclude-dir='__pycache__' "check_ci_proof_surface_matches_registry_v1.sh" docs scripts | head -n 50 || true

echo "OK"
