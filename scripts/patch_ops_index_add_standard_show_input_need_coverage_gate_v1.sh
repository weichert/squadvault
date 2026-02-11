#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops index add standard show input-need coverage gate (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python -m py_compile scripts/_patch_ops_index_add_standard_show_input_need_coverage_gate_v1.py
python scripts/_patch_ops_index_add_standard_show_input_need_coverage_gate_v1.py

echo "OK"
