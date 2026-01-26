#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle approve Lock E plumb args.approved_at_utc into ApproveRequest (v11) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_rivalry_chronicle_approve_lock_e_v11_plumb_args_approved_at_utc_into_request.py"
