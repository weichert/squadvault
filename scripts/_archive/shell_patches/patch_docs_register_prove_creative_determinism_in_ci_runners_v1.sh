#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: register prove_creative_determinism in CI_PROOF_RUNNERS block (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_docs_register_prove_creative_determinism_in_ci_runners_v1.py

echo "==> sanity: entry present inside CI_PROOF_RUNNERS block"
awk '
/<!-- CI_PROOF_RUNNERS_BEGIN -->/{p=1;next}
/<!-- CI_PROOF_RUNNERS_END -->/{p=0}
p{print}
' docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md | grep -n "prove_creative_determinism_v1.sh" >/dev/null

echo "OK"
