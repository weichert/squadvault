#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate remove orphan else prove tail (v1) ==="
python="${PYTHON:-python}"
$python scripts/_patch_fix_ops_orchestrate_orphan_else_v1.py
echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
