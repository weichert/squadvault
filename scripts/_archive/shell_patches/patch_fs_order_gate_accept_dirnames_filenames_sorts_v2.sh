#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fs ordering gate accept dirnames/filenames sorts (v2) ==="

if [ -n "$(git status --porcelain=v1)" ]; then
  echo "FAIL: repo not clean before patch."
  git status --porcelain=v1
  exit 1
fi

python_bin="${PYTHON:-python}"
./scripts/py scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v2.py

echo "==> bash -n target"
bash -n scripts/check_filesystem_ordering_determinism.sh

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v2.py

echo "==> smoke: run fs ordering gate"
bash scripts/check_filesystem_ordering_determinism.sh

echo "==> full prove"
bash scripts/prove_ci.sh

echo "OK: patch complete"
