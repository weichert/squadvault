#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DOUBLE="scripts/""scripts/"

# Scan tracked bash entrypoints:
# - prove scripts
# - gate scripts
# - patch wrappers
#
# IMPORTANT: only flag *actual invocations* of a doubly-prefixed path, not
# guardrail scripts that mention the pattern in their own grep checks.
#
# We flag lines like:
#   bash ${DOUBLE}<...>
#   ./${DOUBLE}<...>

scan_globs=(
  "scripts/prove_*.sh"
  "scripts/gate_*.sh"
  "scripts/patch_*.sh"
)

found_any=0

for g in "${scan_globs[@]}"; do
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    test -f "${f}"

    # bad: bash ${DOUBLE}...
    if grep -nE '^[[:space:]]*bash[[:space:]]+${DOUBLE}' "${f}" >/dev/null; then
      echo "ERROR: detected forbidden double scripts prefix invocation in ${f}"
      grep -nE '^[[:space:]]*bash[[:space:]]+${DOUBLE}' "${f}" || true
      found_any=1
    fi

    # bad: ./${DOUBLE}...
    if grep -nE '^[[:space:]]*\./${DOUBLE}' "${f}" >/dev/null; then
      echo "ERROR: detected forbidden double scripts prefix invocation in ${f}"
      grep -nE '^[[:space:]]*\./${DOUBLE}' "${f}" || true
      found_any=1
    fi
  done < <(git ls-files "${g}")
done

if [[ "${found_any}" -ne 0 ]]; then
  exit 1
fi

echo "OK: no double scripts prefix invocations found."
