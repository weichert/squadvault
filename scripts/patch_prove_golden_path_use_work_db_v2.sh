#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_golden_path prefers WORK_DB (v2) ==="

allowed_paths=(
  "scripts/_patch_prove_golden_path_use_work_db_v2.py"
  "scripts/patch_prove_golden_path_use_work_db_v2.sh"
  "scripts/prove_golden_path.sh"
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
./scripts/py scripts/_patch_prove_golden_path_use_work_db_v2.py

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_prove_golden_path_use_work_db_v2.py

echo "==> bash -n target"
bash -n scripts/prove_golden_path.sh

echo "==> show diff"
git diff -- scripts/prove_golden_path.sh || true

echo "==> full prove"
bash scripts/prove_ci.sh

echo "OK: patch complete (v2). Now git add + commit + push."
