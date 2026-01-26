#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle v1 — Lock Point C (persist draft) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_rivalry_chronicle_v1_lock_c_persist_draft_v1.py

echo
echo "Next: run rivalry-chronicle again; should print Lock C OK and still write --out JSON."
