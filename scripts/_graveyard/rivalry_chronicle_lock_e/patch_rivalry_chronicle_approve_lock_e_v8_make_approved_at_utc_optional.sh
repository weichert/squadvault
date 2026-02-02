#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle approve Lock E make approved_at_utc optional (v8) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_rivalry_chronicle_approve_lock_e_v8_make_approved_at_utc_optional.py"
