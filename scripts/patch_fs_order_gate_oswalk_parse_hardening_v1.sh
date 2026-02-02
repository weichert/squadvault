#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fs ordering gate os.walk parse hardening (v1) ==="

if [ -n "$(git status --porcelain=v1)" ]; then
  echo "FAIL: repo not clean before patch."
  git status --porcelain=v1
  exit 1
fi

python_bin="${PYTHON:-python}"
"$python_bin" scripts/_patch_fs_order_gate_oswalk_parse_hardening_v1.py

echo "==> bash -n target"
bash -n scripts/check_filesystem_ordering_determinism.sh

echo "==> py_compile patcher"
"$python_bin" -m py_compile scripts/_patch_fs_order_gate_oswalk_parse_hardening_v1.py

echo "==> smoke: run fs ordering gate"
bash scripts/check_filesystem_ordering_determinism.sh

echo "==> full prove"
bash scripts/prove_ci.sh

echo "==> cleanliness postcheck"
if [ -n "$(git status --porcelain=v1)" ]; then
  echo "FAIL: repo not clean after patch."
  git status --porcelain=v1
  exit 1
fi

echo "OK: patch complete"
