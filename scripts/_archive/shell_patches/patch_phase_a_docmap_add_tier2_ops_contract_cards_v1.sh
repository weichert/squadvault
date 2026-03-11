#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: DocMap canonical md — add Tier-2 ops contract cards (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
./scripts/py scripts/_patch_phase_a_docmap_add_tier2_ops_contract_cards_v1.py

echo
echo "OK"
