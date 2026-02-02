#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock C SV_DEBUG logs draft tuple (v12) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_lockc_debug_return_tuple_v12.py

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
