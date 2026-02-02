#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts latest helpers bind passed artifact_type (v13) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_latest_helpers_bind_passed_artifact_type_v13.py

echo
echo "Sniff (helper execute tuples around latest helpers):"
nl -ba src/squadvault/core/recaps/recap_artifacts.py | sed -n '35,110p'

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
