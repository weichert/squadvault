#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add coverage baseline v1 ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py -m py_compile scripts/_patch_add_coverage_baseline_v1.py
./scripts/py scripts/_patch_add_coverage_baseline_v1.py

echo "OK"
