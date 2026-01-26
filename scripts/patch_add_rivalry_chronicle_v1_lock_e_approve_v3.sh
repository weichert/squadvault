#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle v1 Lock E approve command wiring (v3) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_add_rivalry_chronicle_v1_lock_e_approve_v3.py

echo
echo "Sniff: recap.py has rivalry-chronicle-approve command:"
grep -n "rivalry-chronicle-approve" -n scripts/recap.py || true

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("scripts/recap.py", doraise=True)
print("OK: compile recap.py")
PY
