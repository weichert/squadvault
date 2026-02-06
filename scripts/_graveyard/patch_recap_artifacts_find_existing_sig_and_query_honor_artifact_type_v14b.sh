#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts _find_existing_draft_version honors artifact_type (v14b) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_find_existing_sig_and_query_honor_artifact_type_v14b.py

echo
echo "Sniff (_find_existing_draft_version):"
grep -n "def _find_existing_draft_version" src/squadvault/core/recaps/recap_artifacts.py | head -n 5
nl -ba src/squadvault/core/recaps/recap_artifacts.py | sed -n '140,210p'

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
