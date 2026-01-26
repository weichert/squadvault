#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock B — autodetect canonical_events payload column (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_rivalry_chronicle_lock_b_payload_col_autodetect_v1.py
