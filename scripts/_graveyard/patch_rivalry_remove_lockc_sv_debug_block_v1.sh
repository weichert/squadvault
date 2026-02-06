#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle remove Lock C SV_DEBUG block (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_remove_lockc_sv_debug_block_v1.py

echo
echo "Sniff (ensure debug removed):"
grep -n "SV_DEBUG: Lock C created=" src/squadvault/consumers/rivalry_chronicle_generate_v1.py || echo "OK: no SV_DEBUG print"
grep -n "SV_DEBUG_ENV" src/squadvault/consumers/rivalry_chronicle_generate_v1.py || echo "OK: no SV_DEBUG_ENV"

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
