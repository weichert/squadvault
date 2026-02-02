#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI workflow add concurrency cancel-in-progress (v1) ==="

allowed_paths=(
  "scripts/_patch_ci_add_concurrency_cancel_in_progress_v1.py"
  "scripts/patch_ci_add_concurrency_cancel_in_progress_v1.sh"
  ".github/workflows/ci.yml"
)

dirty="$(git status --porcelain=v1)"
if [ -n "$dirty" ]; then
  remain="$dirty"
  for ap in "${allowed_paths[@]}"; do
    remain="$(printf "%s\n" "$remain" | grep -v " ${ap}$" || true)"
  done
  if [ -n "$remain" ]; then
    echo "FAIL: repo not clean before patch (unexpected changes present)."
    printf "%s\n" "$remain"
    exit 1
  fi
fi

python_bin="${PYTHON:-python}"

echo "==> run patcher"
"$python_bin" scripts/_patch_ci_add_concurrency_cancel_in_progress_v1.py

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_ci_add_concurrency_cancel_in_progress_v1.py

echo "==> show diff"
git diff -- .github/workflows/ci.yml || true

echo "OK: patch applied. Now commit + push."
