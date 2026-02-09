#!/usr/bin/env bash
set -euo pipefail

echo "==> Gate: Rivalry Chronicle contract linkage (v1)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PROVE="scripts/prove_rivalry_chronicle_end_to_end_v1.sh"
CONTRACT="docs/contracts/rivalry_chronicle_output_contract_v1.md"

if [[ ! -f "${PROVE}" ]]; then
  echo "ERROR: missing prove script: ${PROVE}" >&2
  exit 1
fi

if ! grep -q "docs/contracts/rivalry_chronicle_output_contract_v1.md" "${PROVE}"; then
  echo "ERROR: prove script does not reference contract source-of-truth path: docs/contracts/rivalry_chronicle_output_contract_v1.md" >&2
  echo "       expected exact string in ${PROVE}" >&2
  exit 1
fi

if [[ ! -f "${CONTRACT}" ]]; then
  echo "ERROR: contract doc missing at ${CONTRACT}" >&2
  exit 1
fi

echo "OK: Rivalry Chronicle prove script links to contract doc (v1)"
