#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fs ordering gate accept dirnames/filenames sorts (v1) ==="

allowed_paths=(
  "scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v1.py"
  "scripts/patch_fs_order_gate_accept_dirnames_filenames_sorts_v1.sh"
  "scripts/check_filesystem_ordering_determinism.sh"
)

dirty="$(git status --porcelain=v1)"
if [ -n "$dirty" ]; then
  remain="$dirty"
  for p in "${allowed_paths[@]}"; do
    remain="$(printf "%s\n" "$remain" | grep -v " ${p}\$" || true)"
  done
  if [ -n "$remain" ]; then
    echo "FAIL: repo not clean before patch (unexpected changes present)."
    printf "%s\n" "$remain"
    exit 1
  fi
fi

python_bin="${PYTHON:-python}"
"$python_bin" scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v1.py

echo "==> bash -n target"
bash -n scripts/check_filesystem_ordering_determinism.sh

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_fs_order_gate_accept_dirnames_filenames_sorts_v1.py

echo "==> smoke: run fs ordering gate"
bash scripts/check_filesystem_ordering_determinism.sh

echo "==> full prove"
bash scripts/prove_ci.sh

echo "OK: patch complete"
