#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prune trailing marker-only lines in recap_artifacts.py (v1) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_core_recap_artifacts_prune_trailing_markers_v1.py"
