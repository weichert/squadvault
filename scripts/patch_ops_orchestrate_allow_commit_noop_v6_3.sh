#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate treat --commit no-op as OK (v6.3) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_ops_orchestrate_allow_commit_noop_v6_3.py

echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
