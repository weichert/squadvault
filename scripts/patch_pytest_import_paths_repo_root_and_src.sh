#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_pytest_import_paths_repo_root_and_src.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_pytest_import_paths_repo_root_and_src.py"

echo "==> bash syntax check"
bash -n "scripts/patch_pytest_import_paths_repo_root_and_src.sh"

echo "OK"
