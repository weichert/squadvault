#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock C debug uses 'created' (v12d) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_lockc_debug_use_created_v12d.py

echo
echo "Sniff (Lock C assignment + debug print):"
grep -n "_sv_call_with_signature_filter" src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 8
grep -n "SV_DEBUG: Lock C" src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
