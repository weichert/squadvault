#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

exec "$REPO_ROOT/scripts/py" "$REPO_ROOT/scripts/_patch_fix_prove_ci_no_repo_root_script_invocations_v1.py"
