#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs inventory follow-ups (canonicality pointers + DS_Store ignore) (v1) ==="

PY="./scripts/py"
if [[ ! -x "$PY" ]]; then
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_docs_inventory_followups_v1.py

echo "==> verify .DS_Store cleanup"
test ! -f docs/.DS_Store
test ! -f docs/80_indices/.DS_Store

echo "==> verify gitignore"
grep -qE '^\.(DS_Store|DS_Store)$|^\.DS_Store$' .gitignore || grep -qE '^\.DS_Store$' .gitignore

echo "==> verify canonicality pointers block"
grep -q 'CANONICALITY_RULES_v1_BEGIN' docs/canon_pointers/README.md
grep -q 'CANONICALITY_RULES_v1_END' docs/canon_pointers/README.md

echo "OK"
