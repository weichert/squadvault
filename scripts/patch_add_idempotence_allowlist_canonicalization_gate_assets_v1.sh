#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add allowlist canonicalization patch+gate assets (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_add_idempotence_allowlist_canonicalization_gate_assets_v1.py

chmod +x \
  scripts/_patch_canonicalize_patch_idempotence_allowlist_v1.py \
  scripts/patch_canonicalize_patch_idempotence_allowlist_v1.sh \
  scripts/gate_patch_idempotence_allowlist_canonical_v1.sh

echo "==> bash -n (gate + wrapper)"
bash -n scripts/gate_patch_idempotence_allowlist_canonical_v1.sh
bash -n scripts/patch_canonicalize_patch_idempotence_allowlist_v1.sh

echo "OK"
