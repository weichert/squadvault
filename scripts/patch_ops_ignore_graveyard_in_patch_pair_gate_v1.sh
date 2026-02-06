#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: pairing gate ignores scripts/_graveyard/** (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ops_ignore_graveyard_in_patch_pair_gate_v1.py

echo "==> bash syntax check (spot)"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/patch_ops_ignore_graveyard_in_patch_pair_gate_v1.sh

echo "==> smoke A: graveyard unpaired patcher should be IGNORED (gate should PASS)"
mkdir -p scripts/_graveyard
cat > scripts/_graveyard/_patch__smoke_graveyard_unpaired_tmp_v1.py <<'PY'
print("smoke graveyard")
PY
git add scripts/_graveyard/_patch__smoke_graveyard_unpaired_tmp_v1.py

set +e
out_a="$(SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh 2>&1)"
rc_a=$?
set -e

git reset -q HEAD -- scripts/_graveyard/_patch__smoke_graveyard_unpaired_tmp_v1.py
rm -f scripts/_graveyard/_patch__smoke_graveyard_unpaired_tmp_v1.py

if [ "$rc_a" -ne 0 ]; then
  echo "ERROR: expected PASS when unpaired file is inside scripts/_graveyard/"
  echo "$out_a"
  exit 1
fi
echo "OK: graveyard ignored"

echo "==> smoke B: normal unpaired patcher should still FAIL (gate should FAIL)"
cat > scripts/_patch__smoke_unpaired_tmp_v1.py <<'PY'
print("smoke root")
PY
git add scripts/_patch__smoke_unpaired_tmp_v1.py

set +e
out_b="$(SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh 2>&1)"
rc_b=$?
set -e

git reset -q HEAD -- scripts/_patch__smoke_unpaired_tmp_v1.py
rm -f scripts/_patch__smoke_unpaired_tmp_v1.py

if [ "$rc_b" -eq 0 ]; then
  echo "ERROR: expected FAIL when unpaired file is in scripts/"
  echo "$out_b"
  exit 1
fi

n="$(printf "%s\n" "$out_b" | grep -c "NEXT: Fix patcher/wrapper pairing failures" || true)"
if [ "$n" -ne 1 ]; then
  echo "ERROR: expected CTA header exactly once; got $n"
  echo "$out_b"
  exit 1
fi
echo "OK: strict enforcement preserved outside graveyard"

echo "OK"
