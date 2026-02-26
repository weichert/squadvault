#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

exec "$REPO_ROOT/scripts/py" "$REPO_ROOT/scripts/_patch_add_ci_proof_runner_creative_sharepack_if_available_to_ci_block_v1.py"
