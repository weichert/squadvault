#!/usr/bin/env bash
# SquadVault — CI Guardrails Ops Entrypoint Parity Gate (v1)
#
# Fail-closed.
#
# Purpose:
#   Prove that every gate executed by scripts/prove_ci.sh is discoverable in:
#     docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
#
#   And (within the bounded index section) that no indexed entrypoint exists
#   without being present in scripts/prove_ci.sh.
#
# Executed surface extraction:
#   - bash scripts/gate_*.sh   -> ALWAYS counted
#   - python scripts/check_*.py -> counted ONLY if that path is already indexed
#                                 in the bounded section (per milestone spec).
#
# Index extraction:
#   Bounded section markers:
#     <!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->
#     <!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->
#
# Deterministic, bash3-safe, repo-root anchored.

set -euo pipefail

echo "==> Gate: CI Guardrails ops entrypoints parity (v1)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PROVE="scripts/prove_ci.sh"
INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

BEGIN="<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END="<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

if [[ ! -f "${PROVE}" ]]; then
  echo "ERROR: missing ${PROVE}" >&2
  exit 2
fi
if [[ ! -f "${INDEX}" ]]; then
  echo "ERROR: missing ${INDEX}" >&2
  exit 2
fi

# --- Extract indexed entrypoints (bounded section) ---
if ! grep -qF "${BEGIN}" "${INDEX}" || ! grep -qF "${END}" "${INDEX}"; then
  echo "ERROR: Ops index missing bounded entrypoints markers." >&2
  echo "Expected markers:" >&2
  echo "  ${BEGIN}" >&2
  echo "  ${END}" >&2
  exit 3
fi

tmp_dir="${TMPDIR:-/tmp}"
indexed_tmp="${tmp_dir}/sv_ci_guardrails_indexed.$$"
executed_tmp="${tmp_dir}/sv_ci_guardrails_executed.$$"

# Pull only the bounded region, then extract bullet tokens that start with scripts/
# Accept bullets like:
#   - scripts/<path> — ...
#   - scripts/<path> - ...
#   - scripts/<path>
awk -v b="${BEGIN}" -v e="${END}" '
  $0 ~ b {inside=1; next}
  $0 ~ e {inside=0}
  inside {print}
' "${INDEX}" | awk '
  # Extract the first token starting with scripts/ from bullet lines.
  # Supports:
  #   - scripts/<path> — ...
  #   - scripts/<path> - ...
  #   - scripts/<path>
  /^[[:space:]]*-[[:space:]]*scripts\// {
    line=$0
    sub(/^[[:space:]]*-[[:space:]]*/, "", line)
    sub(/[[:space:]].*$/, "", line)
    print line
  }
' | sed -e 's/[[:space:]]*$//' | sort -u > "${indexed_tmp}"

# --- Extract executed entrypoints from prove_ci ---
# 1) Always count: bash scripts/gate_*.sh
# 2) Conditionally count: python scripts/check_*.py ONLY if already indexed
#
# NOTE: we validate "reachable surface exists" (static presence), not runtime branches.
bash_gate_lines="$(grep -nE '^[[:space:]]*bash[[:space:]]+scripts/gate_[^[:space:]]+\.sh([[:space:]]|$)' "${PROVE}" || true)"
python_check_lines="$(grep -nE '^[[:space:]]*python[[:space:]]+scripts/check_[^[:space:]]+\.py([[:space:]]|$)' "${PROVE}" || true)"

# Extract just the path tokens
# shellcheck disable=SC2001
echo "${bash_gate_lines}" | sed -nE 's/.*bash[[:space:]]+(scripts\/gate_[^[:space:]]+\.sh).*/\1/p' | sort -u > "${executed_tmp}.bash"

# For python checks: include only if path is already indexed in bounded section
# shellcheck disable=SC2001
echo "${python_check_lines}" | sed -nE 's/.*python[[:space:]]+(scripts\/check_[^[:space:]]+\.py).*/\1/p' | sort -u > "${executed_tmp}.py_all"

# Filter python checks by indexed list
# (comm requires sorted inputs)
comm -12 "${indexed_tmp}" "${executed_tmp}.py_all" > "${executed_tmp}.py_indexed" || true

cat "${executed_tmp}.bash" "${executed_tmp}.py_indexed" | sort -u > "${executed_tmp}"

# --- Compare sets ---
executed_not_indexed="${tmp_dir}/sv_ci_guardrails_executed_not_indexed.$$"
indexed_not_executed="${tmp_dir}/sv_ci_guardrails_indexed_not_executed.$$"

comm -23 "${executed_tmp}" "${indexed_tmp}" > "${executed_not_indexed}" || true
comm -13 "${executed_tmp}" "${indexed_tmp}" > "${indexed_not_executed}" || true

fail=0

if [[ -s "${executed_not_indexed}" ]]; then
  fail=1
  echo
  echo "==== Executed but NOT indexed (fail) ===="
  cat "${executed_not_indexed}"
fi

if [[ -s "${indexed_not_executed}" ]]; then
  fail=1
  echo
  echo "==== Indexed (bounded) but NOT executed (fail) ===="
  cat "${indexed_not_executed}"
fi

rm -f   "${indexed_tmp}"   "${executed_tmp}"   "${executed_tmp}.bash"   "${executed_tmp}.py_all"   "${executed_tmp}.py_indexed"   "${executed_not_indexed}"   "${indexed_not_executed}"

if [[ "${fail}" -ne 0 ]]; then
  echo
  echo "ERROR: CI guardrails ops entrypoint parity gate failed." >&2
  exit 1
fi

echo "OK: CI guardrails ops entrypoints parity (v1)"
