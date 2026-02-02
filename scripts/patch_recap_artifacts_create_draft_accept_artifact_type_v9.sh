#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts create_draft accepts artifact_type kwarg (v9) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_create_draft_accept_artifact_type_v9.py

echo
echo "Sniff signature:"
grep -n "def create_recap_artifact_draft_idempotent" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
