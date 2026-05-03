#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper: RC contract linkage gate -> general contract linkage gate (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash scripts/gate_contract_linkage_v1.sh
