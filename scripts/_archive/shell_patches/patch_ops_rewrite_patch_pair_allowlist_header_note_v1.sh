#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: embed allowlist autogen NOTE into rewriter HEADER (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ops_rewrite_patch_pair_allowlist_header_note_v1.py

echo "==> bash syntax check (spot)"
bash -n scripts/patch_ops_rewrite_patch_pair_allowlist_header_note_v1.sh

echo "==> smoke: run allowlist rewriter and confirm NOTE survives regen"
./scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh >/dev/null
grep -n 'NOTE: This file is auto-rewritten by scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh' scripts/patch_pair_allowlist_v1.txt

echo "OK"
