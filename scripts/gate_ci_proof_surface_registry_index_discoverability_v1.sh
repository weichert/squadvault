#!/usr/bin/env bash
set -euo pipefail

# gate_ci_proof_surface_registry_index_discoverability_grep_fix_v1

echo "=== Gate: CI proof surface registry discoverability in Ops index (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

MARKER='<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->'
# NOTE: avoid Unicode dash matching issues in macOS grep; match the stable ASCII path instead.
BULLET_PATH='scripts/gate_ci_proof_surface_registry_v1.sh'

if [[ ! -f "${INDEX}" ]]; then
  echo "ERROR: missing index file: ${INDEX}" >&2
  exit 2
fi

marker_count="$(LC_ALL=C grep -nF -- "${MARKER}" "${INDEX}" | wc -l | tr -d ' ')"
bullet_count="$(LC_ALL=C grep -nF -- "${BULLET_PATH}" "${INDEX}" | wc -l | tr -d ' ')"

if [[ "${marker_count}" != "1" ]]; then
  echo "ERROR: expected exactly 1 marker in ${INDEX}, found ${marker_count}" >&2
  echo "HINT: run: bash scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh" >&2
  exit 1
fi

if [[ "${bullet_count}" != "1" ]]; then
  echo "ERROR: expected exactly 1 registry gate path in ${INDEX}, found ${bullet_count}" >&2
  echo "HINT: run: bash scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh" >&2
  exit 1
fi

echo "OK: index contains marker + canonical gate bullet exactly once."
