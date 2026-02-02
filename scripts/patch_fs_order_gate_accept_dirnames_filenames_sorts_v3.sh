#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fs ordering gate accept dirnames/filenames sorts (v3) ==="

if [ -n "$(git status --porcelain=v1)" ]; then
  echo "FAIL: repo not clean before patch."
  git status --porcelain=v1
  exit 1
fi

python_bin="${PYTHON:-python}"
"$python_bin" scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v3.py

echo "==> bash -n target"
bash -n scripts/check_filesystem_ordering_determinism.sh

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v3.py

echo "==> smoke: run fs ordering gate"
bash scripts/check_filesystem_ordering_determinism.sh

echo "OK: patch applied. Now commit, then run: bash scripts/prove_ci.sh"
