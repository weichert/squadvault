#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: core recap_artifacts approve_recap_artifact add approved_at_utc (v1) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_core_recap_artifacts_approve_add_approved_at_utc_v1.py"
