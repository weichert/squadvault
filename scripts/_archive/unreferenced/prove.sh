#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${REPO_ROOT}/scripts/dev_env.sh" >/dev/null
exec "${REPO_ROOT}/scripts/prove_golden_path.sh"
