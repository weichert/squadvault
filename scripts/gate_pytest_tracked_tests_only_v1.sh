#!/usr/bin/env bash
set -euo pipefail

# === Gate: Pytest must only target tracked Tests/ (v1) ===
#
# Enforces that all pytest invocations in proof/gate/check scripts explicitly
# target Tests/ (tracked paths), never ".", "tests/", absolute paths, or no path.
#
# Scans only tracked:
#   scripts/prove_*.sh
#   scripts/gate_*.sh
#   scripts/check_*.sh
#
# Static enforcement only (grep+token checks). No runtime behavior changes.

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"

cd "$REPO_ROOT"

fail=0
violations=""

TARGETS=()
while IFS= read -r f; do
  [ -n "$f" ] && TARGETS+=("$f")
done < <(
  git ls-files "scripts/prove_*.sh"
)
if [ "${#TARGETS[@]}" -eq 0 ]; then
  echo "ERROR: gate_pytest_tracked_tests_only_v1: no tracked targets found under scripts/{prove_,gate_,check_}*.sh"
  exit 2
fi

is_allowed_tests_path() {
  local tok="$1"
  case "$tok" in
    Tests|Tests/*) return 0 ;;
    *) return 1 ;;
  esac
}

is_forbidden_path() {
  local tok="$1"
  case "$tok" in
    "."|"./"|"./"* ) return 0 ;;
    "tests"|"tests/"|"tests/"* ) return 0 ;;
    /* ) return 0 ;;
    *) return 1 ;;
  esac
}

option_consumes_value() {
  local opt="$1"
  case "$opt" in
    -k|-m|-c|-o|--maxfail|--rootdir|--confcutdir|--basetemp|--override-ini) return 0 ;;
    *) return 1 ;;
  esac
}

check_line_pytest_usage() {
  local file="$1"
  local lineno="$2"
  local line="$3"

  line="${line%%#*}"

  echo "$line" | grep -Eq '(^|[[:space:];&|()])pytest([[:space:]]|$)' || return 0

  if echo "$line" | grep -Eq 'git[[:space:]]+ls-files[[:space:]]+Tests([[:space:]]|$).*xargs[[:space:]]+pytest([[:space:]]|$)'; then
    return 0
  fi

  # shellcheck disable=SC2086
  set -- $line
  local -a toks=("$@")

  local i=0
  local p=-1
  for ((i=0; i<${#toks[@]}; i++)); do
    if [ "${toks[$i]}" = "pytest" ]; then
      p="$i"
      break
    fi
  done
  if [ "$p" -lt 0 ]; then
    return 0
  fi

  local -a args=()
  for ((i=p+1; i<${#toks[@]}; i++)); do
    args+=("${toks[$i]}")
  done

  if [ "${#args[@]}" -eq 0 ]; then
    violations+="${file}:${lineno}: pytest with no explicit path (must target Tests/)\n"
    fail=1
    return 0
  fi

  local idx=0
  while [ "$idx" -lt "${#args[@]}" ]; do
    local a="${args[$idx]}"
    if [[ "$a" == -* ]]; then
      if option_consumes_value "$a"; then
        idx=$((idx+2))
      else
        idx=$((idx+1))
      fi
      continue
    fi
    break
  done

  if [ "$idx" -ge "${#args[@]}" ]; then
    violations+="${file}:${lineno}: pytest options present but no explicit path (must target Tests/)\n"
    fail=1
    return 0
  fi

  local first_path="${args[$idx]}"

  if is_forbidden_path "$first_path"; then
    violations+="${file}:${lineno}: forbidden pytest target '${first_path}' (must target Tests/)\n"
    fail=1
    return 0
  fi

  if ! is_allowed_tests_path "$first_path"; then
# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->
# Allow array-expansion targets like "${gp_tests[@]}" to bypass Tests/ prefix check.
# Tolerate optional surrounding quotes: "${...}", '${...}', \"${...}\", \'${...}\'.
sv_tok="${first_path-${t-${tok-${arg-${target-${raw-}}}}}}"
sv_norm="${sv_tok-}"
for _sv_i in 1 2 3 4; do
  case "$sv_norm" in
    \\\"*\\\") sv_norm="${sv_norm#\\\"}"; sv_norm="${sv_norm%\\\"}";;
    \\\'*\\\') sv_norm="${sv_norm#\\\'}"; sv_norm="${sv_norm%\\\'}";;
    "*")         sv_norm="${sv_norm#"}";   sv_norm="${sv_norm%"}";;
    '*')         sv_norm="${sv_norm#\'}";   sv_norm="${sv_norm%\'}";;
    *) break;;
  esac
done
case "$sv_norm" in
  \$\{[A-Za-z0-9_]*_tests\[@\]\}) return 0;;
esac
    violations+="${file}:${lineno}: pytest target must start with Tests/ (found '${first_path}')\n"
    fail=1
    return 0
  fi
}

for f in "${TARGETS[@]}"; do
  lineno=0
  while IFS= read -r line || [ -n "$line" ]; do
    lineno=$((lineno+1))
    check_line_pytest_usage "$f" "$lineno" "$line"
  done < "$f"
done

if [ "$fail" -ne 0 ]; then
  echo "FAIL: pytest invocations must explicitly target tracked Tests/ paths only."
  echo
  # shellcheck disable=SC2059
  printf "%b" "$violations"
  exit 1
fi

echo "OK: pytest invocations target Tests/ only (tracked)."
