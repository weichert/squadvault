#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_gitignore_whitelist_signal_taxonomy_patcher_v1.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_gitignore_whitelist_signal_taxonomy_patcher_v1.py"

echo "==> bash syntax check"
bash -n "scripts/patch_gitignore_whitelist_signal_taxonomy_patcher_v1.sh"

echo "OK"
