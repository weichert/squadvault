#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap.py forward --approved-at-utc for approve-rivalry-chronicle (v2) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_recap_py_forward_approve_rivalry_chronicle_approved_at_utc_v2.py"
