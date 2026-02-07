#!/usr/bin/env bash
set -euo pipefail

# gate_patch_wrapper_idempotence_set_env_v1

echo "=== Gate: patch wrapper idempotence (allowlist) v1 ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export LC_ALL=C
export LANG=C

ALLOWLIST="scripts/patch_idempotence_allowlist_v1.txt"

echo "==> Guard: allowlist wrappers must not recurse into prove_ci"
bash scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh


if [[ ! -f "${ALLOWLIST}" ]]; then
  echo "ERROR: missing allowlist: ${ALLOWLIST}" >&2
  exit 2
fi

tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t sv_idempotence)"
cleanup() { rm -rf "${tmpdir}"; }
trap cleanup EXIT

status0="${tmpdir}/status0.txt"
status1="${tmpdir}/status1.txt"
status2="${tmpdir}/status2.txt"

git status --porcelain=v1 > "${status0}"

# Helper: run wrapper and require repo to remain clean.
run_wrapper_once() {
  local wrapper="$1"

  if [[ ! -f "${wrapper}" ]]; then
    echo "ERROR: missing wrapper in allowlist: ${wrapper}" >&2
    exit 3
  fi

  echo "==> wrapper: ${wrapper}"
  SV_IDEMPOTENCE_MODE=1 bash "${wrapper}"

  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "ERROR: wrapper left repo DIRTY (must be idempotent/no-op from clean): ${wrapper}" >&2
    echo "==> git status --porcelain=v1" >&2
    git status --porcelain=v1 >&2
    exit 4
  fi
}

# Read wrappers from allowlist (ignore comments/blank lines).
wrappers=()
while IFS= read -r line; do
  case "${line}" in
    "" ) continue ;;
    \#* ) continue ;;
  esac
  wrappers+=("${line}")
done < "${ALLOWLIST}"

if [[ "${#wrappers[@]}" -eq 0 ]]; then
  echo "ERROR: allowlist is empty: ${ALLOWLIST}" >&2
  exit 5
fi

echo "==> pass 1"
for w in "${wrappers[@]}"; do
  run_wrapper_once "${w}"
done

git status --porcelain=v1 > "${status1}"

echo "==> pass 2"
for w in "${wrappers[@]}"; do
  run_wrapper_once "${w}"
done

git status --porcelain=v1 > "${status2}"

# status1 and status2 must match exactly (no new changes on second pass).
if ! cmp -s "${status1}" "${status2}"; then
  echo "ERROR: wrappers are not idempotent (pass2 status differs from pass1 status)" >&2
  echo "==> diff (status1 vs status2)" >&2
  diff -u "${status1}" "${status2}" >&2 || true
  exit 6
fi

# Also require we started clean.
if [[ -s "${status0}" ]]; then
  echo "ERROR: repo was not clean before idempotence gate; run from a clean working tree" >&2
  echo "==> initial git status --porcelain=v1" >&2
  cat "${status0}" >&2
  exit 7
fi

echo "OK: allowlisted patch wrappers are idempotent from clean."
