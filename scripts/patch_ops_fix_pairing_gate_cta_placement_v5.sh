#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: dedupe + place pairing CTA after allowlist line (v5) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_ops_fix_pairing_gate_cta_placement_v5.py

echo "==> bash syntax check (spot)"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/patch_ops_fix_pairing_gate_cta_placement_v5.sh

echo "==> smoke: force failure (tracked unpaired patcher) and confirm CTA prints once AFTER allowlist line"
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
