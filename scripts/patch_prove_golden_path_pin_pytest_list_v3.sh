#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_golden_path pin pytest list (v3; bash3-safe; removes fallback) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_prove_golden_path_pin_pytest_list_v3.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> verify no mapfile and no standalone pytest dir invocation"
if grep -n 'mapfile' scripts/prove_golden_path.sh >/dev/null; then
  echo "ERROR: mapfile still present" >&2
  exit 1
fi
if grep -n '^[[:space:]]*pytest -q Tests[[:space:]]*$' scripts/prove_golden_path.sh >/dev/null; then
  echo "ERROR: standalone 'pytest -q Tests' still present" >&2
  exit 1
fi

echo "OK"
