#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: core approve_recap_artifact force-set approved_at (v2b) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_core_recap_artifacts_approve_force_set_approved_at_v2b.py"
