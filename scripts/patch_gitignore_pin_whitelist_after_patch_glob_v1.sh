#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_gitignore_pin_whitelist_after_patch_glob_v1.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_gitignore_pin_whitelist_after_patch_glob_v1.py"

echo "==> bash syntax check"
bash -n "scripts/patch_gitignore_pin_whitelist_after_patch_glob_v1.sh"

echo "OK"
