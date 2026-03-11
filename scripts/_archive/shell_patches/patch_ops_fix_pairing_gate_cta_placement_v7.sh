#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: smoke-check pairing CTA (v7 wrapper) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

# Re-run the v6 patcher (idempotent) to ensure the desired state.
./scripts/py scripts/_patch_ops_fix_pairing_gate_cta_placement_v7.py

echo "==> bash syntax check (spot)"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/patch_ops_fix_pairing_gate_cta_placement_v7.sh

echo "==> smoke: force failure (tracked unpaired patcher) and confirm CTA prints once"
cat > scripts/_patch__smoke_unpaired_tmp_v1.py <<'PY'
print("smoke")
PY
git add scripts/_patch__smoke_unpaired_tmp_v1.py

set +e
out="$(SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh 2>&1)"
rc=$?
set -e

git reset -q HEAD -- scripts/_patch__smoke_unpaired_tmp_v1.py
rm -f scripts/_patch__smoke_unpaired_tmp_v1.py

if [ "$rc" -eq 0 ]; then
  echo "ERROR: smoke expected failure but gate passed"
  echo "$out"
  exit 1
fi

n="$(printf "%s\n" "$out" | grep -c "NEXT: Fix patcher/wrapper pairing failures" || true)"
if [ "$n" -ne 1 ]; then
  echo "ERROR: expected CTA header once, got $n"
  echo "$out"
  exit 1
fi

echo "OK"
