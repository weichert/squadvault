#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle restore created alias after Lock C (v12c) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_rivalry_lockc_restore_created_alias_v12c.py

echo
echo "Sniff (created alias):"
grep -n "created = draft_result" src/squadvault/consumers/rivalry_chronicle_generate_v1.py | head -n 5

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/rivalry_chronicle_generate_v1.py", doraise=True)
print("OK: compile")
PY
