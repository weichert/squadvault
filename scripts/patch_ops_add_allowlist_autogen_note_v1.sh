#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add autogen note to patch_pair_allowlist_v1.txt (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_ops_add_allowlist_autogen_note_v1.py

echo "==> bash syntax check (spot)"
bash -n scripts/patch_ops_add_allowlist_autogen_note_v1.sh

echo "OK"
