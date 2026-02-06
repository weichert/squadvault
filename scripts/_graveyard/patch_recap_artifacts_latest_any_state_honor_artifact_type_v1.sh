#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts latest-any-state helpers honor artifact_type (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_latest_any_state_honor_artifact_type_v1.py

echo
echo "Quick grep (should show artifact_type default + plumbing):"
grep -n "_latest_artifact_row_any_state" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 20
grep -n "_latest_artifact_fingerprint_any_state" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 20

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
