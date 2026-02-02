#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle approve Lock E fix callsite indent (v5b) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_rivalry_chronicle_approve_lock_e_v5b_fix_callsite_indent.py"
