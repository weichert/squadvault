#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap.py approve-rivalry-chronicle add --approved-at-utc (v1) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_recap_py_add_approve_rivalry_chronicle_approved_at_utc_v1.py"
