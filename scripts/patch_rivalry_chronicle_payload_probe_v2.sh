#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock B — payload column probe v2 ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_rivalry_chronicle_payload_probe_v2.py
