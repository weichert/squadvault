#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire no-obsolete-allowlist-rewrite-artifacts gate into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} -m py_compile scripts/_patch_prove_ci_wire_gate_no_obsolete_allowlist_rewrite_artifacts_v1.py
${PY} scripts/_patch_prove_ci_wire_gate_no_obsolete_allowlist_rewrite_artifacts_v1.py

echo "==> bash -n prove_ci"
bash -n scripts/prove_ci.sh

echo "==> verify gate invocation present"
grep -n "gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh" scripts/prove_ci.sh >/dev/null

echo "OK"
