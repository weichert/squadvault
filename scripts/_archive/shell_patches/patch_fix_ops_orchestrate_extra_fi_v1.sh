#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate remove stray fi (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_fix_ops_orchestrate_extra_fi_v1.py
echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
