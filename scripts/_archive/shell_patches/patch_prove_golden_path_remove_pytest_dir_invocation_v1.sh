#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove forbidden 'pytest -q Tests' from prove_golden_path (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_prove_golden_path_remove_pytest_dir_invocation_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> verify forbidden invocation absent"
if grep -n 'pytest -q Tests' scripts/prove_golden_path.sh >/dev/null; then
  echo "ERROR: forbidden 'pytest -q Tests' still present" >&2
  exit 1
fi

echo "OK"
