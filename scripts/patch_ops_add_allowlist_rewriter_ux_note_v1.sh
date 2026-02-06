#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add UX note to allowlist rewriter wrapper (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ops_add_allowlist_rewriter_ux_note_v1.py

echo "==> bash syntax check (spot)"
bash -n scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh
bash -n scripts/patch_ops_add_allowlist_rewriter_ux_note_v1.sh

echo "OK"
