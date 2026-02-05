#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: cleanup export-assemblies HEX64 patch scripts (v1) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_cleanup_export_assemblies_hex64_patch_scripts_v1.py"

echo "==> bash -n (all scripts)"
# keep this lightweight + bash3-safe
for f in $(git ls-files 'scripts/*.sh'); do
  bash -n "$f"
done
echo "OK: bash -n"

echo "==> status"
git status --porcelain=v1 || true
echo "OK"
