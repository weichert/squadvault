#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: enable strict exports in CI (v1) ==="

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
cd "$repo_root"

py="$repo_root/scripts/py"
if [ -x "$py" ]; then
  python_exec="$py"
else
  python_exec="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_enable_strict_exports_in_ci_v1.py

echo "==> bash -n"
bash -n scripts/prove_ci.sh
bash -n scripts/prove_golden_path.sh

echo "==> grep confirm"
grep -n "SV_STRICT_EXPORTS=1" scripts/prove_ci.sh

echo "OK"
