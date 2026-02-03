#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci export finalized WORK_DB (v1) ==="

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
$py scripts/_patch_prove_ci_export_final_work_db_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "==> run local proof"
bash scripts/prove_ci.sh

echo "==> postflight: git status"
git status --porcelain=v1

echo "OK"
