#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add pytest pin to requirements.txt (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_add_pytest_to_requirements_v1.py

echo "==> sanity: show pytest line"
grep -n "pytest" requirements.txt || { echo "ERROR: pytest not found in requirements.txt"; exit 2; }

echo "==> bash -n"
bash -n scripts/*.sh

echo "OK"
