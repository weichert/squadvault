#!/usr/bin/env bash
set -euo pipefail

echo "==> Gate: CI Guardrails ops entrypoints exactness (v1)"

DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
RENDER="scripts/_render_ci_guardrails_ops_entrypoints_block_v1.py"

if [[ ! -f "${DOC}" ]]; then
  echo "ERROR: missing ${DOC}" >&2
  exit 2
fi

if [[ ! -f "${RENDER}" ]]; then
  echo "ERROR: missing ${RENDER}" >&2
  exit 2
fi

tmp_expected="$(mktemp)"
tmp_actual="$(mktemp)"

cleanup() {
  rm -f "${tmp_expected}" "${tmp_actual}"
}
trap cleanup EXIT

begin_count="$(grep -c 'SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN' "${DOC}" || true)"
end_count="$(grep -c 'SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END' "${DOC}" || true)"

if [[ "${begin_count}" -ne 1 ]]; then
  echo "ERROR: expected exactly one begin marker in ${DOC}; found ${begin_count}" >&2
  exit 1
fi

if [[ "${end_count}" -ne 1 ]]; then
  echo "ERROR: expected exactly one end marker in ${DOC}; found ${end_count}" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 ./scripts/py "${RENDER}" > "${tmp_expected}"

awk '
  /SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN/ { in_block=1 }
  in_block { print }
  /SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END/ { exit }
' "${DOC}" > "${tmp_actual}"

if grep -q 'SV_CI_GUARDRAIL_GATE_' "${tmp_actual}"; then
  echo "ERROR: nested machine-managed markers remain inside the bounded block." >&2
  exit 1
fi

if grep -qE '^- scripts/gate_[A-Za-z0-9_]+\.sh$' "${tmp_actual}"; then
  echo "ERROR: found bare gate bullet with no canonical description." >&2
  exit 1
fi

if ! diff -u "${tmp_expected}" "${tmp_actual}"; then
  echo "ERROR: CI Guardrails ops entrypoints bounded block is not canonical." >&2
  exit 1
fi

echo "OK: CI Guardrails ops entrypoints exactness (v1) passed."
