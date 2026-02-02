#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle v1 — Lock E (approve + immutability) [v2] ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_add_rivalry_chronicle_v1_lock_e_approve_v2.py

echo
echo "Next: ./scripts/recap.sh approve-rivalry-chronicle -h"
