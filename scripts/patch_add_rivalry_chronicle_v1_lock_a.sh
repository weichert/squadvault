#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle v1 — Lock Point A (kind + CLI entrypoint) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

./scripts/py scripts/_patch_add_rivalry_chronicle_v1_lock_a.py

echo
echo "Next: run a quick CLI smoke check (should exit 2 with STUB message)."
