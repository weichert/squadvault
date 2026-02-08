#!/usr/bin/env bash
set -euo pipefail

# CI gate: Proof Surface Registry must list exactly scripts/prove_*.sh (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DOC="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"

BEGIN="<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->"
END="<!-- SV_PROOF_SURFACE_LIST_v1_END -->"

if [[ ! -f "${DOC}" ]]; then
  echo "ERROR: missing registry doc: ${DOC}" >&2
  exit 1
fi

# Expected: tracked prove scripts (sorted)
expected="$(git ls-files 'scripts/prove_*.sh' | sort)"

# Extract actual block
block="$(awk -v b="${BEGIN}" -v e="${END}" '
  $0==b {inside=1; next}
  $0==e {inside=0; exit}
  inside==1 {print}
' "${DOC}")"

if ! grep -Fqx "${BEGIN}" "${DOC}" || ! grep -Fqx "${END}" "${DOC}"; then
  echo "ERROR: registry doc missing required machine block markers:" >&2
  echo "  ${BEGIN}" >&2
  echo "  ${END}" >&2
  echo "Run: bash scripts/patch_ci_proof_surface_registry_machine_block_v1.sh" >&2
  exit 1
fi

# Normalize actual lines: accept "- scripts/..." bullet form only.
actual="$(printf "%s\n" "${block}" \
  | sed -nE 's/^[[:space:]]*-[[:space:]]+(scripts\/prove_[^[:space:]]+)[[:space:]]*$/\1/p')"

# Any non-empty lines in block that are not valid bullets => fail (high signal)
invalid="$(printf "%s\n" "${block}" | sed -e 's/[[:space:]]*$//' | awk '
  NF==0 {next}
  $0 ~ /^[[:space:]]*-[[:space:]]+scripts\/prove_/ {next}
  {print}
')"
if [[ -n "${invalid}" ]]; then
  echo "ERROR: registry machine block contains invalid lines (expected only '- scripts/prove_*.sh'):" >&2
  printf "%s\n" "${invalid}" >&2
  exit 1
fi

# Dedupe check
dupes="$(printf "%s\n" "${actual}" | sort | uniq -d)"
if [[ -n "${dupes}" ]]; then
  echo "ERROR: duplicate entries in registry machine block:" >&2
  printf "%s\n" "${dupes}" >&2
  exit 1
fi

# Must match expected exactly
if [[ "${actual}" != "${expected}" ]]; then
  echo "ERROR: CI_Proof_Surface_Registry is out of sync with tracked prove scripts." >&2
  echo "== Expected (git ls-files 'scripts/prove_*.sh' | sort) ==" >&2
  printf "%s\n" "${expected}" >&2
  echo "== Actual (from registry machine block) ==" >&2
  printf "%s\n" "${actual}" >&2
  echo "Fix by running: bash scripts/patch_ci_proof_surface_registry_machine_block_v1.sh" >&2
  exit 1
fi

echo "OK: proof surface registry exactness gate (v1)"
