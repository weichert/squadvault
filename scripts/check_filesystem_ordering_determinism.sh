#!/usr/bin/env bash
set -euo pipefail

# === SquadVault: Filesystem Ordering Determinism Gate (v1) ===
# Detect common unordered filesystem iteration patterns in scripts/ and src/.
# Waiver (explicit, reviewable):
#   # SV_ALLOW_UNSORTED_FS_ORDER

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

FAIL=0
say() { echo "$@"; }
warn() { echo "ERROR: $@" 1>&2; }

grep_hits() {
  local label="$1"
  local re="$2"
  shift 2

  local hits
  hits="$(grep -R -n -E "${re}" "$@" 2>/dev/null || true)"

  if [ -n "${hits}" ]; then
    hits="$(printf "%s\n" "${hits}" | grep -v "SV_ALLOW_UNSORTED_FS_ORDER" || true)"
  fi

  if [ -n "${hits}" ]; then
    warn "Filesystem ordering nondeterminism risk: ${label}"
    printf "%s\n" "${hits}" 1>&2
    FAIL=1
  fi
}

TARGETS_SHELL="scripts"
TARGETS_PY="src scripts"

grep_hits "shell: 'ls | ...' (ordering + whitespace hazards)"   '(^|[[:space:];&(])ls([[:space:]].*)?[[:space:]]*\|'   ${TARGETS_SHELL}

grep_hits "shell: 'for x in *' (glob order as implicit contract)"   'for[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]+in[[:space:]]+[^;]*\*'   ${TARGETS_SHELL}

grep_hits "shell: 'find ... | while read' (traversal order)"   'find[[:space:]].*\|[[:space:]]*while[[:space:]]+read'   ${TARGETS_SHELL}

grep_hits "python: os.listdir() used (must sort)"   'os\.listdir[[:space:]]*\('   ${TARGETS_PY}

grep_hits "python: glob.glob() used (must sort)"   'glob\.glob[[:space:]]*\('   ${TARGETS_PY}

grep_hits "python: Path.glob()/rglob() used (must sort)"   '\.r?glob[[:space:]]*\('   ${TARGETS_PY}

grep_hits "python: os.walk() used (must sort dirnames/filenames)"   'os\.walk[[:space:]]*\('   ${TARGETS_PY}

if [ "${FAIL}" -ne 0 ]; then
  echo 1>&2
  warn "Filesystem ordering determinism gate FAILED."
  warn "Fix by sorting explicitly (e.g., 'sorted(...)', '.sort()', '... | sort'),"
  warn "or add waiver only if ordering provably does not matter:"
  warn "  # SV_ALLOW_UNSORTED_FS_ORDER"
  exit 1
fi

say "OK: filesystem ordering determinism gate passed."
