#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v1) — RETIRED (shim to v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Delegate to canonical v2 gate.
bash scripts/gate_no_double_scripts_prefix_v2.sh
