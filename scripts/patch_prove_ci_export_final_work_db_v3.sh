#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci export finalized WORK_DB after mktemp+copy (v3) ==="

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
$py scripts/_patch_prove_ci_export_final_work_db_v3.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "==> run local proof (may fail later on export assemblies; that's OK for verifying placement)"
bash scripts/prove_ci.sh || true

echo "==> confirm exports now occur after cp into WORK_DB"
grep -n -C 3 'cp -p "${FIXTURE_DB}" "${WORK_DB}"' scripts/prove_ci.sh | sed -n '1,120p'

echo "==> postflight: git status"
git status --porcelain=v1

echo "OK"
