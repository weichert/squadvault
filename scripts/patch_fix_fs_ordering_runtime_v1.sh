#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: fix runtime filesystem ordering (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python3}"
if ! command -v "${python}" >/dev/null 2>&1; then
  python="python"
fi

"${python}" scripts/_patch_fix_fs_ordering_runtime_v1.py

echo "==> py_compile"
python -m py_compile \
  src/squadvault/consumers/editorial_review_week.py \
  src/squadvault/validation/signals/signal_taxonomy_type_a_v1.py

echo "OK"
