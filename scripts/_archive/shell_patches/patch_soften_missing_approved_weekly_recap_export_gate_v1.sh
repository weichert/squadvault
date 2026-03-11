#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: soften missing APPROVED WEEKLY_RECAP export gate (v1) ==="

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
./scripts/py scripts/_patch_soften_missing_approved_weekly_recap_export_gate_v1.py

echo "==> bash syntax check (all scripts)"
bash -n scripts/*.sh

echo "==> run local proof"
bash scripts/prove_ci.sh

echo "==> postflight: git status"
git status --porcelain=v1
echo "OK"
