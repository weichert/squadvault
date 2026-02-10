#!/usr/bin/env bash
set -euo pipefail

# Write a file from stdin safely (paste-proof).
# Usage:
#   bash scripts/clipwrite.sh path/to/file <<'EOF'
#   ...content...
#   EOF

if [[ "$#" -ne 1 ]]; then
  echo "usage: $0 <path>  (content comes from stdin)" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

exec "${PY}" scripts/clipwrite.py "$1"
