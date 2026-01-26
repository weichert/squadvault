#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts helper signatures accept artifact_type (v8) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_helper_sigs_accept_artifact_type_v8.py

echo
echo "Sniff helper defs:"
grep -n "def _latest_artifact_version_any_state" src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "def _next_version" src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "def _latest_approved_fingerprint_in_conn" src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "def _latest_approved_version_in_conn" src/squadvault/core/recaps/recap_artifacts.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
