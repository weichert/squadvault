#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci wire best-in-class tightening (v1) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
./scripts/py -m py_compile scripts/_patch_prove_ci_wire_best_in_class_tightening_v1.py
./scripts/py scripts/_patch_prove_ci_wire_best_in_class_tightening_v1.py
bash -n scripts/prove_ci.sh
echo "OK"
