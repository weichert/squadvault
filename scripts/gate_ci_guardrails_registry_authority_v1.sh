#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PROVE_CI="scripts/prove_ci.sh"
REGISTRY_TSV="docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"

TMPDIR_ROOT="${TMPDIR:-/tmp}"
TMPDIR_ROOT="${TMPDIR_ROOT%/}"

EXECUTED="$(mktemp "${TMPDIR_ROOT}/sv_ci_guardrails_registry_authority_executed.XXXXXX")"
REGISTERED="$(mktemp "${TMPDIR_ROOT}/sv_ci_guardrails_registry_authority_registered.XXXXXX")"
MISSING="$(mktemp "${TMPDIR_ROOT}/sv_ci_guardrails_registry_authority_missing.XXXXXX")"

cleanup() {
  rm -f "${EXECUTED}" "${REGISTERED}" "${MISSING}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

awk '
  /^[[:space:]]*#/ { next }
  {
    if ($1 == "bash" && $2 ~ /^scripts\/gate_[A-Za-z0-9_]+\.sh$/) {
      print $2
      next
    }
    if ($1 ~ /^\.\/scripts\/gate_[A-Za-z0-9_]+\.sh$/) {
      gsub(/^\.\//, "", $1)
      print $1
      next
    }
  }
' "${PROVE_CI}" | sort -u > "${EXECUTED}"

cut -f1 "${REGISTRY_TSV}" | grep '^scripts/gate_[A-Za-z0-9_]\+\.sh$' | sort -u > "${REGISTERED}"

comm -23 "${EXECUTED}" "${REGISTERED}" > "${MISSING}"

if [[ -s "${MISSING}" ]]; then
  echo "ERROR: CI guardrails registry authority gate failed." >&2
  echo "The following gate scripts are executed by scripts/prove_ci.sh but missing from ${REGISTRY_TSV}:" >&2
  sed 's/^/  - /' "${MISSING}" >&2
  exit 1
fi

echo "OK: every gate script executed by scripts/prove_ci.sh is present in ${REGISTRY_TSV}."
