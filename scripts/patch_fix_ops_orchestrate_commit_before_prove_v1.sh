#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate commit before prove (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
"${python}" scripts/_patch_fix_ops_orchestrate_commit_before_prove_v1.py

echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
