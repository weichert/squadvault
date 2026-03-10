#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

echo "=== Patch: add CI Guardrails ops entrypoint exactness gate (v1) ==="

for required in \
  scripts/_render_ci_guardrails_ops_entrypoints_block_v1.py \
  scripts/_patch_add_ci_guardrails_ops_entrypoint_exactness_v1.py \
  scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh
do
  if [[ ! -f "${required}" ]]; then
    echo "ERROR: missing ${required}" >&2
    exit 2
  fi
done

PYTHONDONTWRITEBYTECODE=1 ./scripts/py scripts/_patch_add_ci_guardrails_ops_entrypoint_exactness_v1.py

chmod +x \
  scripts/patch_add_ci_guardrails_ops_entrypoint_exactness_v1.sh \
  scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh

bash -n \
  scripts/patch_add_ci_guardrails_ops_entrypoint_exactness_v1.sh \
  scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh

echo "OK: CI Guardrails ops entrypoint exactness patch applied (v1)"
