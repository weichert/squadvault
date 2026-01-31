#!/usr/bin/env bash
set -euo pipefail

# SquadVault — Fixture immutability guard (CI)
# - Records a pre-run fingerprint for fixture files
# - Verifies fingerprints are unchanged after proofs
# - Loud, actionable failure on mutation
#
# Modes:
#   record <statefile> <file1> [file2 ...]
#   verify <statefile> <file1> [file2 ...]

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/check_fixture_immutability_ci.sh record <statefile> <file1> [file2 ...]
  scripts/check_fixture_immutability_ci.sh verify <statefile> <file1> [file2 ...]
EOF
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

mode="${1:-}"
statefile="${2:-}"
shift || true
shift || true

if [[ -z "${mode}" || -z "${statefile}" ]]; then
  usage
fi

if [[ $# -lt 1 ]]; then
  echo "ERROR: no files provided." >&2
  usage
fi

# Hash strategy:
# - If file is tracked by git: use git blob hash-object (stable, content-based)
# - Else: fall back to sha256 (shasum) content hash
hash_file() {
  local f="$1"
  if [[ ! -f "${f}" ]]; then
    echo "MISSING"
    return 0
  fi

  if git ls-files --error-unmatch "${f}" >/dev/null 2>&1; then
    git hash-object "${f}"
  else
    # macOS has shasum; Linux often does too. Keep it simple + portable.
    shasum -a 256 "${f}" | awk '{print $1}'
  fi
}

record() {
  local sf="$1"; shift
  : > "${sf}"

  # deterministic ordering for stability
  # (sort paths lexicographically before recording)
  # shellcheck disable=SC2207
  local files_sorted=($(printf "%s\n" "$@" | LC_ALL=C sort))

  for f in "${files_sorted[@]}"; do
    local h
    h="$(hash_file "${f}")"
    if [[ "${h}" == "MISSING" ]]; then
      echo "ERROR: fixture file missing: ${f}" >&2
      exit 41
    fi
    printf "%s\t%s\n" "${f}" "${h}" >> "${sf}"
  done
}

verify() {
  local sf="$1"; shift
  if [[ ! -f "${sf}" ]]; then
    echo "ERROR: statefile not found: ${sf}" >&2
    exit 42
  fi

  local failed=0

  # Read the recorded set (authoritative)
  # Format: path \t hash
  while IFS=$'\t' read -r f oldh; do
    # Only verify files we recorded (ignores extra args)
    local newh
    newh="$(hash_file "${f}")"
    if [[ "${newh}" == "MISSING" ]]; then
      echo "ERROR: fixture disappeared during run: ${f}" >&2
      failed=1
      continue
    fi
    if [[ "${newh}" != "${oldh}" ]]; then
      echo >&2
      echo "============================================" >&2
      echo "FIXTURE MUTATION DETECTED (CI FORBIDS THIS)" >&2
      echo "File: ${f}" >&2
      echo "Before: ${oldh}" >&2
      echo "After:  ${newh}" >&2
      echo "--------------------------------------------" >&2
      echo "This means a proof wrote into a COMMITTED fixture." >&2
      echo "CI requires fixtures to be immutable and proofs to be deterministic." >&2
      echo "" >&2
      echo "Next steps (local):" >&2
      echo "  1) Inspect what changed:" >&2
      echo "     git status --porcelain" >&2
      echo "     git diff -- ${f} || true" >&2
      echo "  2) Restore fixture:" >&2
      echo "     git checkout -- ${f}" >&2
      echo "" >&2
      echo "Fix guidance:" >&2
      echo "  - Identify the code path writing to the fixture DB." >&2
      echo "  - Update the proof/consumer to use a temp COPY when writes are required," >&2
      echo "    OR open the DB read-only if writes are accidental." >&2
      echo "  - Do NOT silently mask this inside CI." >&2
      echo "============================================" >&2
      failed=1
    fi
  done < "${sf}"

  if [[ "${failed}" -ne 0 ]]; then
    exit 43
  fi
}

case "${mode}" in
  record) record "${statefile}" "$@" ;;
  verify) verify "${statefile}" "$@" ;;
  *) usage ;;
esac
