#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add strict_subshell helper + operator safety note (v1) ==="

python="${PYTHON:-python}"
$python scripts/_patch_add_strict_subshell_helper_v1.py

echo "==> bash syntax check"
bash -n scripts/strict_subshell_v1.sh

echo "OK"
