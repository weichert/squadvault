#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: link CI proof surface registry from CI guardrails index (v1) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${self_dir}/.." && pwd)"

py="${repo_root}/scripts/py"
if [[ -x "${py}" ]]; then
  "${repo_root}/scripts/py" "${repo_root}/scripts/_patch_add_ci_proof_surface_registry_index_link_v1.py"
else
  python="${PYTHON:-python}"
  "${repo_root}/scripts/py" "${repo_root}/scripts/_patch_add_ci_proof_surface_registry_index_link_v1.py"
fi

echo "OK: CI guardrails index updated (v1)."
