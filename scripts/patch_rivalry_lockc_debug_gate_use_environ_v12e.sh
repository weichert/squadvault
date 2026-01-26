#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock C debug gate uses SV_DEBUG env (v12e) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_lockc_debug_gate_use_environ_v12e.py

echo
echo "Sniff (SV_DEBUG gate):"
grep -n "SV_DEBUG_ENV = os.environ.get('SV_DEBUG'" src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 5
grep -n "SV_DEBUG: Lock C created=" src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
