#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove forbidden standalone 'pytest -q Tests' from prove_golden_path (v2) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_prove_golden_path_remove_pytest_dir_invocation_v2.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> verify no standalone forbidden invocation remains"
if grep -n '^[[:space:]]*pytest -q Tests[[:space:]]*$' scripts/prove_golden_path.sh >/dev/null; then
  echo "ERROR: standalone forbidden invocation still present" >&2
  exit 1
fi

echo "OK"
