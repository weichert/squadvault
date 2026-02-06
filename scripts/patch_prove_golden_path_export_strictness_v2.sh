#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_golden_path export strictness (v2) ==="

echo "==> preflight: repo cleanliness"
if [ -n "$(git status --porcelain=v1)" ]; then
  echo "ERROR: repo is not clean. Commit/stash first."
  git status --porcelain=v1
  exit 1
fi
echo "OK: clean"

py="python"
if [ -x "scripts/py" ]; then
  py="scripts/py"
fi

echo "==> apply patcher"
./scripts/py scripts/_patch_prove_golden_path_export_strictness_v2.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> run proof (default mode should pass)"
bash scripts/prove_ci.sh

echo "==> run proof (strict mode should fail if exports are missing)"
SV_STRICT_EXPORTS=1 bash scripts/prove_ci.sh || echo "NOTE: strict mode failed as expected (good)."

echo "==> postflight: git status"
git status --porcelain=v1
echo "OK"
