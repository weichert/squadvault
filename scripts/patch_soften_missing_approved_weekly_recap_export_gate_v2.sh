#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: soften missing APPROVED WEEKLY_RECAP export gate (v2) ==="

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
$py scripts/_patch_soften_missing_approved_weekly_recap_export_gate_v2.py

echo "==> python compile (basic sanity)"
$py -m py_compile \
  src/squadvault/consumers/recap_export_narrative_assemblies_approved.py \
  src/squadvault/consumers/recap_export_variants_approved.py

echo "==> run local proof"
bash scripts/prove_ci.sh

echo "==> postflight: git status"
git status --porcelain=v1
echo "OK"
