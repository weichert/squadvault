#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove RC approved_by optional (v5) ==="
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_prove_rc_approved_by_v5.py
echo "==> bash -n"
bash -n scripts/prove_rivalry_chronicle_end_to_end_v1.sh
echo "OK"
