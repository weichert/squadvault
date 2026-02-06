#!/usr/bin/env bash
set -euo pipefail

echo "==> Python shim compliance gate (v2)"

# Invariant (v2):
#   Any scripts/patch_*.sh wrapper that runs a scripts/_patch_*.py patcher MUST do so via:
#     ./scripts/py scripts/_patch_foo.py
#   (No direct `python`, `python3`, or `$python` execution of patchers.)
#
# Rationale:
#   Wrappers are the highest-leverage drift surface: a single bad wrapper reintroduces
#   local/CI divergence and CWD/import nondeterminism.
#
# Scope:
#   - scripts/patch_*.sh only (static analysis; no runtime behavior)
#   - Does not police prove_*.sh or non-wrapper scripts yet (intentionally narrow)

die() {
  echo "ERROR: $*" >&2
  exit 1
}

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
repo_root="$(cd -- "${here}/.." >/dev/null 2>&1 && pwd)"
cd "${repo_root}"

# Use git ls-files so we only scan tracked wrappers (deterministic).
# Use git ls-files so we only scan tracked wrappers (deterministic).
wrappers="$(git ls-files 'scripts/patch_*.sh' | sort || true)"
if [ -z "${wrappers}" ]; then
  die "no tracked scripts/patch_*.sh wrappers found (unexpected)"
fi

violations=0

# We only care about *executions* of patchers.
# A line counts as a patcher execution iff:
#   - it references scripts/_patch_*.py AND
#   - it appears to run via python-ish launcher (python/python3/$python/$py/${PYTHON...}) OR scripts/py
#
# Non-executions that may reference patchers (allowed):
#   - cat > scripts/_patch_*.py <<'PY'
#   - test -f scripts/_patch_*.py
#   - py_compile lines (we don't police compilation launcher here)
#
# Required invariant for executions:
#   - the launcher must be scripts/py (any path form containing '/scripts/py').

is_exec_line() {
  # $1 = full "file:line:content" string
  # must mention a patcher path
  printf "%s" "$1" | grep -q -E 'scripts/_patch_[A-Za-z0-9_]+\.py' || return 1

  # ignore obvious non-exec patterns
  printf "%s" "$1" | grep -q -E 'cat[[:space:]]+>[[:space:]]+scripts/_patch_|test[[:space:]]+-f[[:space:]]+scripts/_patch_|-m[[:space:]]+py_compile' && return 1

  # must look like an execution launcher
  printf "%s" "$1" | grep -q -E '(^|[[:space:];&(:])(\./scripts/py|.*/scripts/py|python3?|"\$\{?PYTHON[^"]*\}"|\$\{?PYTHON[^[:space:]]*\}?|\$python|\$py|"?\$\{?python[^}]*\}?"?)' || return 1

  return 0
}

has_py_shim_launcher() {
  # Accept any scripts/py launcher form (quoted or not):
  #   ./scripts/py
  #   scripts/py
  #   "$repo_root/scripts/py"
  #   "${repo_root}/scripts/py"
  #
  # (We accept optional path prefix ending right before scripts/py, including repo_root var forms.)
  printf "%s" "$1" | grep -q -E '(^|[[:space:];&(:])("?((\$\{?repo_root\}?/)?(\./)?|[^"[:space:]]*/)?scripts/py"?)'
}

for f in ${wrappers}; do
  # candidate lines: any non-comment line mentioning scripts/_patch_*.py
  matches="$(grep -nH -E 'scripts/_patch_[A-Za-z0-9_]+\.py' "${f}" | grep -v -E '^[^:]+:[0-9]+:[[:space:]]*#' || true)"
  if [ -z "${matches}" ]; then
    continue
  fi

  bad=""
  while IFS= read -r line; do
    if is_exec_line "${line}"; then
      if ! has_py_shim_launcher "${line}"; then
        bad="${bad}${line}"$'\n'
      fi
    fi
  done <<< "${matches}"

  if [ -n "${bad}" ]; then
    echo "FAIL: wrapper executes patcher without scripts/py launcher:" >&2
    echo "" >&2
    printf "%s" "${bad}" >&2
    echo "" >&2
    echo "Remediation:" >&2
    echo "  - Replace python/\$python/\$py launchers with scripts/py:" >&2
    echo "      ./scripts/py scripts/_patch_x.py" >&2
    echo "      \"${repo_root}/scripts/py\" \"${repo_root}/scripts/_patch_x.py\"" >&2
    violations=1
  fi
done

if [ "${violations}" -ne 0 ]; then
  exit 1
fi

echo "OK: Python shim compliance gate (v2) passed."
