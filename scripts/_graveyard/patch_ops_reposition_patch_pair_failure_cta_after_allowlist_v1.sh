#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: move pairing gate CTA after allowlist path line (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_ops_reposition_patch_pair_failure_cta_after_allowlist_v1.py

echo "==> bash syntax check (spot)"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/patch_ops_reposition_patch_pair_failure_cta_after_allowlist_v1.sh

echo "==> smoke: force failure (tracked unpaired patcher) and confirm CTA prints after allowlist line"
cat > scripts/_patch__smoke_unpaired_tmp_v1.py <<'PY'
print("smoke")
PY
git add scripts/_patch__smoke_unpaired_tmp_v1.py

set +e
SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh
rc=$?
set -e

git reset -q HEAD -- scripts/_patch__smoke_unpaired_tmp_v1.py
rm -f scripts/_patch__smoke_unpaired_tmp_v1.py

if [ "$rc" -eq 0 ]; then
  echo "ERROR: smoke expected failure but gate passed"
  exit 1
fi

echo "OK"
