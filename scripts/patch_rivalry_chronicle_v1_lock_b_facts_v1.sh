#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle v1 — Lock Point B (facts assembler) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_rivalry_chronicle_v1_lock_b_facts_v1.py

echo
echo "Next: run a facts-only build to a scratch JSON file."
