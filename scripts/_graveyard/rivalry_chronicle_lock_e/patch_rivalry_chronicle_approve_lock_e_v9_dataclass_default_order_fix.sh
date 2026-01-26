#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle approve Lock E dataclass default order fix (v9) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_rivalry_chronicle_approve_lock_e_v9_dataclass_default_order_fix.py"
