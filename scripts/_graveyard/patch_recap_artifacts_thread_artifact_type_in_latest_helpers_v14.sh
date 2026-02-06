#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts thread artifact_type in latest helpers (v14) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_thread_artifact_type_in_latest_helpers_v14.py

echo
echo "Sniff (latest helper internals + latest_approved_version signature):"
nl -ba src/squadvault/core/recaps/recap_artifacts.py | sed -n '55,105p'

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
