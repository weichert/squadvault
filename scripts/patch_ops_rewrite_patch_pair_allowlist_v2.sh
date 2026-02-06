#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops rewrite patch_pair_allowlist_v1.txt from gate output (v2) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_ops_rewrite_patch_pair_allowlist_v2.py

echo "==> bash syntax check (spot)"
bash -n scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh

echo "==> smoke: pairing gate (verbose)"
SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh | head -n 80

echo "OK"
