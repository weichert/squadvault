#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts _latest_approved_fingerprint accepts artifact_type (v14a) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_latest_approved_fp_sig_accept_artifact_type_v14a.py

echo
echo "Sniff (_latest_approved_fingerprint def):"
grep -n "def _latest_approved_fingerprint" -n src/squadvault/core/recaps/recap_artifacts.py | head -n 5
nl -ba src/squadvault/core/recaps/recap_artifacts.py | sed -n '100,155p'

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
