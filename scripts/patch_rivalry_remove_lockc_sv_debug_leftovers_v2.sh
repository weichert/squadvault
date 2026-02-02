#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle remove Lock C SV_DEBUG leftovers (v2) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_remove_lockc_sv_debug_leftovers_v2.py

echo
echo "Sniff (ensure SV_DEBUG leftovers removed):"
grep -n "SV_DEBUG_ENV" src/squadvault/consumers/rivalry_chronicle_generate_v1.py || echo "OK: no SV_DEBUG_ENV"
grep -n "SV_DEBUG_ON" src/squadvault/consumers/rivalry_chronicle_generate_v1.py || echo "OK: no SV_DEBUG_ON"
grep -n "if SV_DEBUG_ON" src/squadvault/consumers/rivalry_chronicle_generate_v1.py || echo "OK: no dangling if"

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
