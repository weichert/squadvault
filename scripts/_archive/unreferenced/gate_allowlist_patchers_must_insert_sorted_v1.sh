#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: allowlist patchers must insert-sorted (no append-before-EOF) (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Heuristic: reject patchers that modify gate_patch_wrapper_idempotence_allowlist_v1.sh
# by searching for patterns that strongly indicate “append near EOF”.
#
# We intentionally fail-closed: if any allowlist patcher uses these patterns, it must be updated
# to insert in sorted order (or use a centralized canonicalizer patcher).
needle1='rfind("EOF")'
needle2='idx = text.rfind("EOF")'
needle3='if "EOF" in text:'

hits=0
while IFS= read -r f; do
  if grep -nF -- "${needle1}" "${f}" >/dev/null 2>&1; then
    echo "ERROR: ${f} contains '${needle1}' (append-before-EOF pattern)."
    grep -nF -- "${needle1}" "${f}" || true
    hits=$((hits+1))
  fi
  if grep -nF -- "${needle2}" "${f}" >/dev/null 2>&1; then
    echo "ERROR: ${f} contains '${needle2}' (append-before-EOF pattern)."
    grep -nF -- "${needle2}" "${f}" || true
    hits=$((hits+1))
  fi
  if grep -nF -- "${needle3}" "${f}" >/dev/null 2>&1; then
    echo "ERROR: ${f} contains '${needle3}' (append-before-EOF pattern)."
    grep -nF -- "${needle3}" "${f}" || true
    hits=$((hits+1))
  fi
done < <(git ls-files 'scripts/_patch_allowlist_patch_wrapper_*.py' 2>/dev/null || true)

if [[ "${hits}" -ne 0 ]]; then
  echo "FAIL: found ${hits} forbidden allowlist patcher patterns."
  echo "Fix: rewrite allowlist patchers to insert wrappers in sorted order."
  exit 1
fi

echo "OK: no forbidden allowlist patcher patterns found."
