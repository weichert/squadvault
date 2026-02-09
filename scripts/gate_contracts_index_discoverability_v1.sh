#!/usr/bin/env bash
set -euo pipefail

# SquadVault — Contracts Index Discoverability Gate (v1)
# Ensures docs/contracts/README.md indexes all versioned contract docs.

fail() { echo "CONTRACTS_INDEX_V1_FAIL: $*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

CONTRACTS_DIR="docs/contracts"
README="${CONTRACTS_DIR}/README.md"

[[ -d "${CONTRACTS_DIR}" ]] || fail "missing contracts dir: ${CONTRACTS_DIR}"
[[ -f "${README}" ]] || fail "missing README index: ${README}"

# List contract docs (versioned) in canonical filesystem order
# macOS/BSD find compatible; stable sort
contract_files="$(find "${CONTRACTS_DIR}" -maxdepth 1 -type f -name '*_contract_v*.md' | sort)"

# Extract listed contract paths from README bullet lines: - `path`
listed="$(grep -E '^- `docs/contracts/[^`]+`$' "${README}" | sed -E 's/^- `([^`]+)`$/\1/' | sort)"

# Fail if README lists duplicates (after sorting, duplicates have adjacent equals)
if printf '%s\n' "${listed}" | awk 'NF{print}' | uniq -d | grep -q .; then
  fail "README contains duplicate contract entries"
fi

# Ensure every contract file is listed exactly once
missing=""
while IFS= read -r f; do
  [[ -n "${f}" ]] || continue
  if ! printf '%s\n' "${listed}" | grep -Fx "${f}" >/dev/null; then
    missing="${missing}\n- ${f}"
  fi
done <<< "${contract_files}"

if [[ -n "${missing}" ]]; then
  fail "README is missing contract entries:${missing}"
fi

# Ensure README does not reference non-existent files
extra=""
while IFS= read -r f; do
  [[ -n "${f}" ]] || continue
  if [[ ! -f "${f}" ]]; then
    extra="${extra}\n- ${f}"
  fi
done <<< "${listed}"

if [[ -n "${extra}" ]]; then
  fail "README references non-existent contract files:${extra}"
fi

# Hard requirement: Golden Path Output Contract v1 must be listed
req="docs/contracts/golden_path_output_contract_v1.md"
printf '%s\n' "${listed}" | grep -Fx "${req}" >/dev/null || fail "missing required index entry: ${req}"

echo "OK: contracts README indexes all versioned contracts (v1)"
