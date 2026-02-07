#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add canonical patcher/wrapper pattern doc (v1) ==="

PY="./scripts/py"
if [[ ! -x "$PY" ]]; then
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_add_canonical_patcher_wrapper_doc_v1.py

echo "OK"
