#!/usr/bin/env bash
set -euo pipefail

# === SquadVault: Filesystem Ordering Determinism Gate (v1.2.1) ===
# Goal: catch unordered filesystem iteration that can affect behavior/output.
# Scope: runtime + consumers (src/) and non-patcher ops scripts (scripts/).
#
# Waiver (explicit, reviewable):
#   # SV_ALLOW_UNSORTED_FS_ORDER

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

FAIL=0
say() { echo "$@"; }
warn() { echo "ERROR: $@" 1>&2; }

filter_exclusions() {
  grep -v -E '^scripts/_graveyard/' | \
  grep -v -E 'scripts/(patch_|_patch_|_diag_).*' | \
  grep -v -E 'scripts/check_filesystem_ordering_determinism\.sh' | \
  grep -v "SV_ALLOW_UNSORTED_FS_ORDER"
}

report_hits() {
  local label="$1"
  local hits="$2"
  if [ -n "${hits}" ]; then
    warn "Filesystem ordering nondeterminism risk: ${label}"
    printf "%s\n" "${hits}" 1>&2
    FAIL=1
  fi
}

# Run grep, but treat any grep stderr output as fatal (fail loud).
# Usage: safe_grep VAR_NAME <grep args...>
safe_grep() {
  local __outvar="$1"
  shift
  local tmp_err
  tmp_err="$(mktemp -t sv_grep_err.XXXXXX)"
  local out
  out="$("$@" 2>"${tmp_err}" || true)"
  if [ -s "${tmp_err}" ]; then
    cat "${tmp_err}" 1>&2
    rm -f "${tmp_err}"
    warn "grep emitted stderr; treating as fatal."
    exit 1
  fi
  rm -f "${tmp_err}"
  printf -v "${__outvar}" "%s" "${out}"
}

# --- Shell checks (narrow) ---
safe_grep shell_hits_ls_while grep -R -n -E '(^|[[:space:];&(])ls([[:space:]].*)?[[:space:]]*\|[[:space:]]*while[[:space:]]+read' scripts
safe_grep shell_hits_ls_xargs grep -R -n -E '(^|[[:space:];&(])ls([[:space:]].*)?[[:space:]]*\|[[:space:]]*xargs' scripts
safe_grep shell_hits_find_while grep -R -n -E 'find[[:space:]].*\|[[:space:]]*while[[:space:]]+read' scripts

shell_hits_ls_while="$(printf "%s\n" "${shell_hits_ls_while}" | filter_exclusions || true)"
shell_hits_ls_xargs="$(printf "%s\n" "${shell_hits_ls_xargs}" | filter_exclusions || true)"
shell_hits_find_while="$(printf "%s\n" "${shell_hits_find_while}" | filter_exclusions || true)"

report_hits "shell: 'ls | while read' (ls as data source; ordering/whitespace hazards)" "${shell_hits_ls_while}"
report_hits "shell: 'ls | xargs' (ls as data source; ordering/whitespace hazards)" "${shell_hits_ls_xargs}"
report_hits "shell: 'find ... | while read' (traversal order)" "${shell_hits_find_while}"

# --- Python checks ---
safe_grep py_hits_listdir grep -R -n -E 'os\.listdir[[:space:]]*\(' src scripts
safe_grep py_hits_globglob grep -R -n -E 'glob\.glob[[:space:]]*\(' src scripts

py_hits_listdir="$(printf "%s\n" "${py_hits_listdir}" | filter_exclusions || true)"
py_hits_globglob="$(printf "%s\n" "${py_hits_globglob}" | filter_exclusions || true)"

report_hits "python: os.listdir() used (must sort)" "${py_hits_listdir}"
report_hits "python: glob.glob() used (must sort)" "${py_hits_globglob}"

# Path.glob()/rglob(): do NOT flag if same line contains 'sorted(' (simple substring filter; no regex parens)
safe_grep py_hits_pathglob grep -R -n -E '\.r?glob[[:space:]]*\(' src scripts
py_hits_pathglob="$(printf "%s\n" "${py_hits_pathglob}" | filter_exclusions | grep -v "sorted(" || true)"
report_hits "python: Path.glob()/rglob() used without sorted(...)" "${py_hits_pathglob}"

# os.walk(): do NOT flag if dirs.sort() and files.sort() appear within next 5 lines
safe_grep py_hits_oswalk_raw grep -R -n -E 'os\.walk[[:space:]]*\(' src scripts
py_hits_oswalk_raw="$(printf "%s\n" "${py_hits_oswalk_raw}" | filter_exclusions || true)"

py_hits_oswalk_unsorted=""
if [ -n "${py_hits_oswalk_raw}" ]; then
  while IFS= read -r hit; do
    f="$(printf "%s" "${hit}" | cut -d: -f1)"
    ln="$(printf "%s" "${hit}" | cut -d: -f2)"
    # oswalk_numeric_guard_v1: defensive; ignore non-numeric line fields
    printf "%s" "${ln}" | grep -E -q '^[0-9]+$' || continue

    start=$((ln + 1))
    end=$((ln + 5))
    window="$(sed -n "${start},${end}p" "${f}" 2>/dev/null || true)"

    echo "${window}" | grep -q 'dirs\.sort[[:space:]]*()' || { py_hits_oswalk_unsorted="${py_hits_oswalk_unsorted}${hit}\n"; continue; }
    echo "${window}" | grep -q 'files\.sort[[:space:]]*()' || { py_hits_oswalk_unsorted="${py_hits_oswalk_unsorted}${hit}\n"; continue; }
  done <<EOF
${py_hits_oswalk_raw}
EOF
fi

py_hits_oswalk_unsorted="$(printf "%b" "${py_hits_oswalk_unsorted}" | sed '/^$/d' || true)"
report_hits "python: os.walk() used without immediate dirs.sort()/files.sort()" "${py_hits_oswalk_unsorted}"

if [ "${FAIL}" -ne 0 ]; then
  echo 1>&2
  warn "Filesystem ordering determinism gate FAILED."
  warn "Fix by sorting explicitly (e.g., 'sorted(...)', '.sort()', '... | sort'),"
  warn "or add waiver only if ordering provably does not matter:"
  warn "  # SV_ALLOW_UNSORTED_FS_ORDER"
  exit 1
fi

say "OK: filesystem ordering determinism gate passed."
