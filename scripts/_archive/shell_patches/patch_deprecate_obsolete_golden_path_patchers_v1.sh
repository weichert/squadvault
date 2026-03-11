#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: deprecate obsolete Golden Path patchers (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_deprecate_obsolete_golden_path_patchers_v1.py

echo "==> quick sanity: ensure v3 remains untouched"
test -f scripts/_patch_prove_golden_path_pin_pytest_list_v3.py

echo "OK"
