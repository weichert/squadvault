#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: Rivalry Chronicle approve guard schema-aware (v7 reindent-only) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_rc_approve_guard_rendered_text_schema_aware_v7.py

echo "==> py_compile"
./scripts/py -m py_compile src/squadvault/consumers/rivalry_chronicle_approve_v1.py

echo "==> pytest (idempotency test)"
./scripts/py -m pytest Tests/test_rivalry_chronicle_approve_idempotency_v1.py -q

echo "OK"
