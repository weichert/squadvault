#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock C SV_DEBUG logs draft tuple (v12b) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_lockc_debug_return_tuple_v12b.py

echo
echo "Sniff (Lock C assignment + debug line):"
grep -n "draft_result = _sv_call_with_signature_filter" -n src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 5
grep -n "SV_DEBUG: Lock C draft_result" -n src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
