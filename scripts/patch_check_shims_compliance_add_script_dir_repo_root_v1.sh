#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_check_shims_compliance_add_script_dir_repo_root_v1.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_check_shims_compliance_add_script_dir_repo_root_v1.py"

echo "==> bash syntax check"
bash -n "scripts/patch_check_shims_compliance_add_script_dir_repo_root_v1.sh"

echo "OK"
