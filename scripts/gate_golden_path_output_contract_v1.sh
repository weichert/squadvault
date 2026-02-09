#!/usr/bin/env bash
set -euo pipefail

# SquadVault — Golden Path Output Contract Gate (v1)
# Structure-only validation of export assemblies.

usage() {
  cat <<'EOF'
Usage:
  scripts/gate_golden_path_output_contract_v1.sh --selected-assembly <abs_path>

Validates:
  - selected assembly exists
  - path contains exports/<league>/<season>/week_<NN>/
  - week dir contains both assembly_plain_v1__approved_vNN.md and assembly_sharepack_v1__approved_vNN.md
  - naming invariants (vNN)
  - minimal markdown structure (>=1 heading within first 80 lines)

EOF
}

SELECTED=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --selected-assembly) SELECTED="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

fail() { echo "CONTRACT_V1_FAIL: $*" >&2; exit 1; }

[[ -n "${SELECTED}" ]] || fail "--selected-assembly is required"
[[ -f "${SELECTED}" ]] || fail "selected assembly does not exist: ${SELECTED}"

# Resolve directory + filename
WEEK_DIR="$(cd "$(dirname "${SELECTED}")" && pwd)"
FILE="$(basename "${SELECTED}")"

# Validate directory shape contains exports/<league>/<season>/week_<NN>
# We do this with a conservative regex on the full path.
FULL="${WEEK_DIR}/${FILE}"

# Expect .../exports/<digits>/<4digits>/week_<2digits>/<file>
echo "${FULL}" | grep -E '/exports/[0-9]+/[0-9]{4}/week_[0-9]{2}/' >/dev/null || \
  fail "selected assembly path is not under exports/<league>/<season>/week_<NN>: ${FULL}"

# Validate filename pattern + derive sibling
echo "${FILE}" | grep -E '^assembly_(plain|sharepack)_v1__approved_v[0-9]{2}\.md$' >/dev/null || \
  fail "selected assembly filename violates contract v1: ${FILE}"

PLAIN="${WEEK_DIR}/assembly_plain_v1__approved_$(echo "${FILE}" | sed -E 's/^assembly_(plain|sharepack)_v1__approved_(v[0-9]{2})\.md$/\2/').md"
SHARE="${WEEK_DIR}/assembly_sharepack_v1__approved_$(echo "${FILE}" | sed -E 's/^assembly_(plain|sharepack)_v1__approved_(v[0-9]{2})\.md$/\2/').md"

[[ -f "${PLAIN}" ]] || fail "missing required plain assembly: ${PLAIN}"
[[ -f "${SHARE}" ]] || fail "missing required sharepack assembly: ${SHARE}"

# Minimal markdown structure: non-empty + a heading within first 80 lines
check_md() {
  local p="$1"
  [[ -s "$p" ]] || fail "assembly is empty: $p"
  # heading must appear early (structure only, not content)
  head -n 80 "$p" | grep -E '^\s*#' >/dev/null || fail "no markdown heading in first 80 lines: $p"
}

check_md "${PLAIN}"
check_md "${SHARE}"

echo "OK: Golden Path outputs conform to Output Contract (v1)"
