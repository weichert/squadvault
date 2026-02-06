#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci exports CI_WORK_DB/WORK_DB (v2) ==="

allowed_paths=(
  "scripts/_patch_prove_ci_export_ci_work_db_v2.py"
  "scripts/patch_prove_ci_export_ci_work_db_v2.sh"
  "scripts/prove_ci.sh"
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
./scripts/py scripts/_patch_prove_ci_export_ci_work_db_v2.py

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_prove_ci_export_ci_work_db_v2.py

echo "==> bash -n prove_ci"
bash -n scripts/prove_ci.sh

echo "==> show diff"
git diff -- scripts/prove_ci.sh || true

echo "==> full prove (must be clean at start)"
bash scripts/prove_ci.sh

echo "OK: patch complete (v2). Now git add + commit + push."
