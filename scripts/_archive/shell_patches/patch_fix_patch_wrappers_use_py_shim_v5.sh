#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: bulk-fix patch wrappers to use scripts/py (v5) ==="

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
repo_root="$(cd -- "${here}/.." >/dev/null 2>&1 && pwd)"
cd "${repo_root}"

./scripts/py scripts/_patch_fix_patch_wrappers_use_py_shim_v5.py

echo "==> bash syntax check (wrappers)"
for f in $(git ls-files 'scripts/patch_*.sh' | sort); do
  bash -n "$f"
done

echo "OK"
