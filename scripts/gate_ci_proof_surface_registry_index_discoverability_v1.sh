#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: CI proof surface registry discoverability in Ops index (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

MARKER='<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->'
BULLET='- scripts/gate_ci_proof_surface_registry_v1.sh — CI Proof Surface Registry Gate (canonical)'

if [[ ! -f "${INDEX}" ]]; then
  echo "ERROR: missing index file: ${INDEX}" >&2
  exit 2
fi

marker_count="$(grep -nF "${MARKER}" "${INDEX}" | wc -l | tr -d ' ')"
bullet_count="$(grep -nF "${BULLET}" "${INDEX}" | wc -l | tr -d ' ')"

if [[ "${marker_count}" != "1" ]]; then
  echo "ERROR: expected exactly 1 marker in ${INDEX}, found ${marker_count}" >&2
  echo "HINT: run: bash scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh" >&2
  exit 1
fi

if [[ "${bullet_count}" != "1" ]]; then
  echo "ERROR: expected exactly 1 bullet in ${INDEX}, found ${bullet_count}" >&2
  echo "HINT: run: bash scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh" >&2
  exit 1
fi

echo "OK: index contains marker + canonical gate bullet exactly once."
