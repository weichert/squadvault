#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts normalize create_draft signature indentation (v10a) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_fix_create_draft_signature_indent_v10a.py

echo
echo "Sniff signature:"
nl -ba src/squadvault/core/recaps/recap_artifacts.py | sed -n '180,210p'

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
