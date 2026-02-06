#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: rewrite pytest directory invocation gate (v3) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_check_no_pytest_directory_invocation_gate_rewrite_v3.py

echo "==> bash -n"
bash -n scripts/check_no_pytest_directory_invocation.sh

echo "==> self-test: should IGNORE echo mentioning pytest"
tmp="${TMPDIR:-/tmp}/sv_echo_pytest_$$.sh"
tmp2="${TMPDIR:-/tmp}/sv_bad_pytest_dir_$$.sh"
cleanup() { rm -f "$tmp" "$tmp2" >/dev/null 2>&1 || true; }
trap 'cleanup' EXIT

cat > "$tmp" <<'ECHO'
#!/usr/bin/env bash
echo "==> unit tests (pytest; tracked Tests/ paths; bash3-safe)"
ECHO
bash scripts/check_no_pytest_directory_invocation.sh "$tmp" >/dev/null
echo "OK: echo line ignored"

echo "==> self-test: must FAIL on directory invocation"
cat > "$tmp2" <<'BAD'
#!/usr/bin/env bash
pytest -q Tests/validation/signals
BAD

set +e
bash scripts/check_no_pytest_directory_invocation.sh "$tmp2" >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR: expected failure but gate returned success" >&2
  exit 2
fi
echo "OK: directory invocation rejected"

echo "OK"
