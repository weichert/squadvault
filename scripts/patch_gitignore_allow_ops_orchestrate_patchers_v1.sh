#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: .gitignore allow ops_orchestrate patchers (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
./scripts/py scripts/_patch_gitignore_allow_ops_orchestrate_patchers_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_gitignore_allow_ops_orchestrate_patchers_v1.sh
echo "OK"
