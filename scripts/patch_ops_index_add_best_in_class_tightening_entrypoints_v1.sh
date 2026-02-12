#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops index add best-in-class tightening entrypoints (v1) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
./scripts/py -m py_compile scripts/_patch_ops_index_add_best_in_class_tightening_entrypoints_v1.py
./scripts/py scripts/_patch_ops_index_add_best_in_class_tightening_entrypoints_v1.py
echo "OK"
