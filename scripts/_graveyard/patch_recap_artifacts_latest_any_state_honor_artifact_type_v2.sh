#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts latest-any-state helpers honor artifact_type (v2) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_latest_any_state_honor_artifact_type_v2.py

echo
echo "Sniff test (show defs + key callsites):"
grep -n "def _latest_artifact_row_any_state" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "def _latest_artifact_fingerprint_any_state" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 5
grep -n "_latest_artifact_row_any_state(con, league_id, season, week_index" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 10
grep -n "_latest_artifact_fingerprint_any_state(con, league_id, season, week_index" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 10

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
