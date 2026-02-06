#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist Golden Path governance index patcher in .gitignore (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_gitignore_allow_docs_add_golden_path_governance_index_patcher_v1.py

echo "==> verify"
git check-ignore -v scripts/_patch_docs_add_golden_path_governance_index_v1.py || echo "OK: not ignored"

echo "==> diff"
git diff -- .gitignore || true

echo "OK"
