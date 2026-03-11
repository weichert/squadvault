#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci export SQUADVAULT_TEST_DB from WORK_DB (v2) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_prove_ci_export_squadvault_test_db_env_v2.py
echo "==> bash -n"
bash -n scripts/prove_ci.sh
echo "OK"
