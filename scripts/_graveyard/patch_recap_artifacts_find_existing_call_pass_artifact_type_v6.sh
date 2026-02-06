#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts pass artifact_type into _find_existing_draft_version call (v6) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_find_existing_call_pass_artifact_type_v6.py

echo
echo "Sniff (callsite):"
grep -n "_find_existing_draft_version(con, league_id, season, week_index, selection_fingerprint" src/squadvault/core/recaps/recap_artifacts.py | head -n 20

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
