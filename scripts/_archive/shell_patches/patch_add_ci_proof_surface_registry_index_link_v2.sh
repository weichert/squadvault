#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI proof surface registry index link (v2) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${self_dir}/.." && pwd)"

py="${repo_root}/scripts/py"
if [[ -x "${py}" ]]; then
  "${repo_root}/scripts/py" "${repo_root}/scripts/_patch_add_ci_proof_surface_registry_index_link_v2.py"
else
  python="${PYTHON:-python}"
  "${repo_root}/scripts/py" "${repo_root}/scripts/_patch_add_ci_proof_surface_registry_index_link_v2.py"
fi
