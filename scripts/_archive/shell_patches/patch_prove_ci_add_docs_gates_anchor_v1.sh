#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci add docs_gates anchor (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_add_docs_gates_anchor_v1.py

echo "==> Verify: anchor markers present"
grep -nF "# === SV_ANCHOR: docs_gates (v1) ===" scripts/prove_ci.sh >/dev/null
grep -nF "# === /SV_ANCHOR: docs_gates (v1) ===" scripts/prove_ci.sh >/dev/null

echo "==> Verify: anchor appears before docs integrity invocation"
# crude ordering check: first anchor line number must be < first docs integrity line number
anchor_ln="$(grep -nF "# === SV_ANCHOR: docs_gates (v1) ===" scripts/prove_ci.sh | head -n1 | cut -d: -f1)"
needle_ln="$(grep -nF "bash scripts/prove_docs_integrity_v1.sh" scripts/prove_ci.sh | head -n1 | cut -d: -f1)"
if [[ -z "${anchor_ln}" || -z "${needle_ln}" ]]; then
  echo "ERROR: could not compute ordering line numbers"
  exit 1
fi
if [[ "${anchor_ln}" -ge "${needle_ln}" ]]; then
  echo "ERROR: anchor does not appear before docs integrity invocation"
  echo "  anchor_ln=${anchor_ln}"
  echo "  needle_ln=${needle_ln}"
  exit 1
fi

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_add_docs_gates_anchor_v1.sh

echo "OK"
