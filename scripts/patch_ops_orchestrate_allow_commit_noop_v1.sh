#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate treat --commit no-op as OK (v1) ==="
python="${PYTHON:-python}"
$python scripts/_patch_ops_orchestrate_allow_commit_noop_v1.py
echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
