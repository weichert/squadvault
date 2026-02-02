#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts approved fingerprint gate honors artifact_type (v10b) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_approved_fp_call_pass_artifact_type_v10b.py

echo
echo "Sniff (approved_fp line):"
grep -n "_latest_approved_fingerprint(con, league_id, season, week_index" src/squadvault/core/recaps/recap_artifacts.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
