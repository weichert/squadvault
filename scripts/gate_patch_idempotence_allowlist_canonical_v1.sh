#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: idempotence allowlist canonical (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

ALLOWLIST="scripts/patch_idempotence_allowlist_v1.txt"
if [[ ! -f "${ALLOWLIST}" ]]; then
  echo "ERROR: missing allowlist: ${ALLOWLIST}" >&2
  exit 2
fi

items=()
while IFS= read -r raw; do
  line="${raw#"${raw%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  [[ -z "${line}" ]] && continue
  [[ "${line}" == \#* ]] && continue

  if [[ "${raw}" != "${line}" ]]; then
    echo "ERROR: allowlist line has leading/trailing whitespace:" >&2
    echo "  raw: ${raw}" >&2
    exit 3
  fi

  items+=("${line}")
done < "${ALLOWLIST}"

if [[ "${#items[@]}" -eq 0 ]]; then
  echo "ERROR: allowlist is empty: ${ALLOWLIST}" >&2
  exit 4
fi

missing=0
for p in "${items[@]}"; do
  if [[ ! -f "${p}" ]]; then
    echo "ERROR: allowlist references missing file: ${p}" >&2
    missing=1
  fi
done
[[ "${missing}" -ne 0 ]] && exit 5

tmp="$(mktemp -t sv_allowlist.XXXXXX 2>/dev/null || mktemp -t sv_allowlist)"
trap 'rm -f "${tmp}"' EXIT
printf "%s\n" "${items[@]}" > "${tmp}"

dups="$(sort "${tmp}" | uniq -d || true)"
if [[ -n "${dups}" ]]; then
  echo "ERROR: allowlist contains duplicates:" >&2
  echo "${dups}" >&2
  exit 6
fi

sorted_tmp="$(mktemp -t sv_allowlist_sorted.XXXXXX 2>/dev/null || mktemp -t sv_allowlist_sorted)"
trap 'rm -f "${tmp}" "${sorted_tmp}"' EXIT
sort "${tmp}" > "${sorted_tmp}"

if ! cmp -s "${tmp}" "${sorted_tmp}"; then
  echo "ERROR: allowlist is not sorted canonically (LC_ALL=C): ${ALLOWLIST}" >&2
  echo "Hint: run: bash scripts/patch_canonicalize_patch_idempotence_allowlist_v1.sh" >&2
  exit 7
fi

echo "OK: allowlist is canonical (sorted, unique, existing files, no stray whitespace)."
