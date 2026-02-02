#!/usr/bin/env bash
set -euo pipefail

echo "=== Docs Import: staging manifest → canonical docs/ (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python3 scripts/_import_docs_staging_v1.py "$@"
