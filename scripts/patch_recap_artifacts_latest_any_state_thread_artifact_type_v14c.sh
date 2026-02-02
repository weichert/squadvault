#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts latest any-state threads artifact_type (v14c) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_latest_any_state_thread_artifact_type_v14c.py

echo
echo "Sniff (latest any-state helpers):"
nl -ba src/squadvault/core/recaps/recap_artifacts.py | sed -n '40,90p'

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
