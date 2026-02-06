#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: graveyard superseded Lock E wrappers (v1) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_graveyard_move_lock_e_superseded_wrappers_v1.py"
