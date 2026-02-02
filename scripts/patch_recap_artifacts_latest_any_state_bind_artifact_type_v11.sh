#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts latest-any-state helpers bind artifact_type variable (v11) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_latest_any_state_bind_artifact_type_v11.py

echo
echo "Sniff defs + key bind tuples:"
grep -n "def _latest_artifact_row_any_state" src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "def _latest_artifact_fingerprint_any_state" src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "ARTIFACT_TYPE_WEEKLY_RECAP" src/squadvault/core/recaps/recap_artifacts.py | head -n 30

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
