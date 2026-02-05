#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: strict_subshell helper + operator safety note (v2) ==="

python="${PYTHON:-python}"
$python scripts/_patch_add_strict_subshell_helper_v2.py

echo "==> bash syntax check"
bash -n scripts/strict_subshell_v1.sh

echo "OK"
